"""FAERS API snapshot counts: a prototype, not a deduplicated study."""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen

ENDPOINT = "https://api.fda.gov/drug/event.json"


def quote_term(value):
    value = value.strip()
    if not value or any(c in value for c in ('"', '\\')):
        raise ValueError("名称不能为空，也不能包含双引号或反斜杠")
    return '"' + value + '"'


def build_queries(drug, event, start_year, end_year):
    if not 1900 <= start_year <= end_year <= datetime.now(timezone.utc).year:
        raise ValueError("年份必须在 1900 至当前年份之间，且开始年份不晚于结束年份")
    date = f"receivedate:[{start_year}0101 TO {end_year}1231]"
    # Drug phrase matching is intentionally preliminary, not complete identity resolution.
    drug_clause = "patient.drug.openfda.generic_name:" + quote_term(drug)
    event_clause = "patient.reaction.reactionmeddrapt.exact:" + quote_term(event)
    return {
        "N": date,
        "ND": f"({date}) AND ({drug_clause})",
        "NE": f"({date}) AND ({event_clause})",
        "NDE": f"({date}) AND ({drug_clause}) AND ({event_clause})",
    }


def fetch_total(query):
    url = ENDPOINT + "?" + urlencode({"search": query, "limit": 1})
    try:
        with urlopen(url, timeout=30) as response:
            payload = json.load(response)
            status = response.status
    except HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode("utf-8"))
        except (ValueError, UnicodeError):
            raise RuntimeError(f"HTTP {exc.code}: 无法解析错误响应") from exc
        # Only the documented no-match response is zero; access failures are never zero.
        error = payload.get("error", {}) if isinstance(payload, dict) else {}
        if exc.code == 404 and error.get("code") == "NOT_FOUND" and error.get("message") == "No matches found!":
            return {"url": url, "http_status": 404, "total": 0, "response": payload}
        raise RuntimeError(f"HTTP {exc.code}: {error}") from exc
    if not isinstance(payload, dict):
        raise ValueError("API 响应不是 JSON 对象")
    total = payload.get("meta", {}).get("results", {}).get("total")
    if isinstance(total, bool) or not isinstance(total, int) or total < 0:
        raise ValueError("API 没有返回有效的 meta.results.total，不能推断为零")
    return {"url": url, "http_status": status, "total": total, "response": payload}


def make_table(totals):
    n, nd, ne, nde = (totals[key] for key in ("N", "ND", "NE", "NDE"))
    if any(isinstance(x, bool) or not isinstance(x, int) or x < 0 for x in (n, nd, ne, nde)):
        raise ValueError("计数必须是非负整数")
    table = {"a": nde, "b": nd - nde, "c": ne - nde, "d": n - nd - ne + nde}
    if any(value < 0 for value in table.values()) or sum(table.values()) != n:
        raise ValueError("计数不一致；请检查查询语义或数据库是否在查询期间更新")
    return table


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--drug", default="empagliflozin")
    parser.add_argument("--event", default="Diabetic ketoacidosis")
    parser.add_argument("--start-year", type=int, default=2022)
    parser.add_argument("--end-year", type=int, default=2024)
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    args = parser.parse_args()
    try:
        queries = build_queries(args.drug, args.event, args.start_year, args.end_year)
    except ValueError as exc:
        parser.error(str(exc))

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run_dir = args.output_dir / ("counts_" + stamp)
    audit = {
        "status": "running", "started_at_utc": stamp,
        "definition": {
            "drug": args.drug.strip(), "event": args.event.strip(),
            "start_year": args.start_year, "end_year": args.end_year,
            "date_field": "receivedate", "age_sex_filters": None,
            "drug_field": "patient.drug.openfda.generic_name",
            "event_field": "patient.reaction.reactionmeddrapt.exact",
            "drug_role_filter": None,
            "deduplication": "API returned counts; no independent deduplication",
        },
        "queries": queries, "requests": {},
        "limitations": [
            "标准化通用名可能缺失；当前药物短语匹配不是完整药物识别。",
            "事件使用输入的单一完整术语，不包含同义词或相关术语集合。",
            "未独立验证 API 的报告版本处理，也未做患者层面去重。",
            "四次查询不是原子快照；数据库更新可能造成不一致。",
            "保存 API 响应和计数，不是全部报告的数据快照。",
            "报告比例不等于发病率，也不能证明因果关系。",
        ],
    }
    try:
        run_dir.mkdir(parents=True, exist_ok=False)
        for name, query in queries.items():
            print(f"Query {name}: {query}", flush=True)
            audit["requests"][name] = fetch_total(query)
            print(f"  total = {audit['requests'][name]['total']}", flush=True)
        totals = {name: item["total"] for name, item in audit["requests"].items()}
        table = make_table(totals)
        if totals["N"] == 0:
            raise ValueError("分析范围内没有报告，无法开展分析")
        audit.update(status="completed", totals=totals, table=table)
    except (OSError, ValueError, RuntimeError) as exc:
        audit.update(status="failed", error=str(exc))
        print(f"失败：{exc}；不会生成四格表或把失败当成零计数。", file=sys.stderr)
    audit["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    try:
        with (run_dir / "audit.json").open("x", encoding="utf-8") as handle:
            json.dump(audit, handle, ensure_ascii=False, indent=2)
    except OSError as exc:
        print(f"无法保存审计记录：{exc}", file=sys.stderr)
        return 1
    print(f"记录保存至：{run_dir / 'audit.json'}")
    if audit["status"] != "completed":
        return 1
    print("\n                     包含事件       不包含事件")
    print(f"包含目标药物         a={table['a']}        b={table['b']}")
    print(f"不包含目标药物       c={table['c']}        d={table['d']}")
    print("\n仅为 API 计数原型；尚未计算 PRR/ROR，也未验证去重和匹配覆盖。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
