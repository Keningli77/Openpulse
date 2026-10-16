"""Compare baseline and expanded drug-name matching using fresh FAERS counts."""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from faers_counts import build_queries, fetch_total, make_table, quote_term
from faers_stats import compute_statistics


def sensitivity_queries(drug, event, start_year, end_year, names):
    baseline = build_queries(drug, event, start_year, end_year)
    terms = list(dict.fromkeys(name.strip() for name in names))
    if not terms:
        raise ValueError("至少需要一个原始药物名称")
    original = "patient.drug.openfda.generic_name:" + quote_term(drug)
    raw_clauses = ["patient.drug.medicinalproduct:" + quote_term(name) for name in terms]
    expanded = "(" + " OR ".join([original] + raw_clauses) + ")"
    date = baseline["N"]
    event_clause = "patient.reaction.reactionmeddrapt.exact:" + quote_term(event)
    return {
        **baseline,
        "ND_expanded": f"({date}) AND {expanded}",
        "NDE_expanded": f"({date}) AND {expanded} AND ({event_clause})",
    }


def compare(totals):
    common = {key: totals[key] for key in ("N", "NE")}
    baseline = make_table({**common, "ND": totals["ND"], "NDE": totals["NDE"]})
    expanded = make_table({**common, "ND": totals["ND_expanded"], "NDE": totals["NDE_expanded"]})
    added_events = totals["NDE_expanded"] - totals["NDE"]
    added_reports = totals["ND_expanded"] - totals["ND"]
    if added_events < 0 or added_reports < added_events:
        raise ValueError("扩展查询不满足超集关系，需核查查询语义或数据更新")
    result = {"additional_drug_reports": added_reports, "additional_drug_event_reports": added_events}
    for name, table in (("baseline", baseline), ("expanded", expanded)):
        item = {"table": table}
        if min(table.values()) == 0:
            item["statistics_status"] = "unavailable_zero_counts"
        else:
            item.update(statistics_status="completed", statistics=compute_statistics(table))
        result[name] = item
    if all(result[name]["statistics_status"] == "completed" for name in ("baseline", "expanded")):
        result["relative_change_percent"] = {
            metric: 100 * (result["expanded"]["statistics"][metric]["estimate"] /
                           result["baseline"]["statistics"][metric]["estimate"] - 1)
            for metric in ("PRR", "ROR")
        }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--drug", default="empagliflozin")
    parser.add_argument("--event", default="Diabetic ketoacidosis")
    parser.add_argument("--start-year", type=int, default=2022)
    parser.add_argument("--end-year", type=int, default=2024)
    parser.add_argument("--raw-name", action="append", help="可重复传入的原始药物名称；其他药物必须自行指定")
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    args = parser.parse_args()
    names = args.raw_name
    if names is None:
        if args.drug.strip().casefold() != "empagliflozin":
            parser.error("其他药物请通过 --raw-name 指定审核过的名称")
        names = ["empagliflozin", "JARDIANCE", "SYNJARDY", "SYNJARDY XR", "GLYXAMBI", "TRIJARDY XR"]
    try:
        queries = sensitivity_queries(args.drug, args.event, args.start_year, args.end_year, names)
    except ValueError as exc:
        parser.error(str(exc))
    now = datetime.now(timezone.utc)
    folder = args.output_dir / ("sensitivity_" + now.strftime("%Y%m%dT%H%M%S%fZ"))
    audit = {
        "status": "running", "started_at_utc": now.isoformat(),
        "definition": {"drug": args.drug.strip(), "event": args.event.strip(),
                       "start_year": args.start_year, "end_year": args.end_year,
                       "date_field": "receivedate", "raw_names": names,
                       "drug_role_filter": None, "age_sex_filters": None},
        "queries": queries, "requests": {},
        "limitations": [
            "基线及扩展均为短语匹配；扩展名称列表不是完整药物识别，仍可能漏配或误配。",
            "包含目标成分的单方和复方产品；不限定疑似药物角色。",
            "新增命中表示查询覆盖差异，不能直接认定为标准化字段缺失。",
            "两种方案使用同次运行的新计数，不能把与旧文件的差异全部归因于名称匹配。",
            "六次请求不是原子快照，数据库更新可能影响比较。",
            "openFDA 文档说明只返回同一报告最新版本；不同报告之间的病例重复未独立处理。",
            "receivedate 是首次接收日期，不是事件发生日期；报告最新内容可在该年份范围后更新。",
            "匹配敏感性检查不是因果验证，也不自动改变原分析定义。",
        ],
    }
    try:
        folder.mkdir(parents=True, exist_ok=False)
        for name, query in queries.items():
            print(f"Query {name}: {query}", flush=True)
            audit["requests"][name] = fetch_total(query)
            print("  total =", audit["requests"][name]["total"], flush=True)
        totals = {name: request["total"] for name, request in audit["requests"].items()}
        if totals["N"] == 0:
            raise ValueError("时间范围内无报告")
        audit.update(status="completed", totals=totals, comparison=compare(totals))
    except (OSError, ValueError, RuntimeError, OverflowError) as exc:
        audit.update(status="failed", error=str(exc))
        print(f"失败：{exc}；未完成结果不能作为比较结论。", file=sys.stderr)
    audit["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    try:
        with (folder / "sensitivity.json").open("x", encoding="utf-8") as handle:
            json.dump(audit, handle, ensure_ascii=False, indent=2, allow_nan=False)
    except OSError as exc:
        print(f"无法保存：{exc}", file=sys.stderr)
        return 1
    print("保存位置：", folder / "sensitivity.json")
    if audit["status"] != "completed":
        return 1
    result = audit["comparison"]
    for name in ("baseline", "expanded"):
        item = result[name]
        print(f"\n{name} 四格表：{item['table']}")
        if item["statistics_status"] == "completed":
            for metric in ("PRR", "ROR"):
                stat = item["statistics"][metric]
                print(f"{metric} = {stat['estimate']:.4f} | 95% CI [{stat['ci_lower']:.4f}, {stat['ci_upper']:.4f}]")
        else:
            print("存在零计数，未计算 log-Wald 区间。")
    print("\n新增药物报告：", result["additional_drug_reports"])
    print("新增药物+事件报告：", result["additional_drug_event_reports"])
    print("PRR/ROR 相对变化（%）：", result.get("relative_change_percent", "无法计算"))
    print("这只是匹配敏感性检查；不会更新原四格表、统计或报告。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
