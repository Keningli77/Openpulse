"""Compute PRR/ROR and log-Wald intervals from a completed counts audit."""

import argparse
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import NormalDist


def format_stat(value, percent=False):
    if value is None:
        return "Not estimable"
    return f"{value:.6%}" if percent else f"{value:.4f}"


def compute_statistics(table, confidence=0.95):
    if not isinstance(table, dict):
        raise ValueError("A valid contingency table is required")
    counts = [table.get(key) for key in ("a", "b", "c", "d")]
    if any(isinstance(x, bool) or not isinstance(x, int) or x < 0 for x in counts):
        raise ValueError("a, b, c, d must be nonnegative integers")
    if not 0 < confidence < 1:
        raise ValueError("Confidence must be between 0 and 1")
    a, b, c, d = counts
    p_drug = a / (a + b) if a + b else None
    p_background = c / (c + d) if c + d else None
    prr = p_drug / p_background if p_drug is not None and p_background else None
    ror = (a * d) / (b * c) if b * c and a + b and c + d else None
    warnings = ["Intervals use independent-count, large-sample approximations; they do not capture systematic reporting biases.",
                "Reporting proportions are not incidence and cannot establish causality."]
    if any(x == 0 for x in counts):
        unavailable = lambda estimate: {"estimate": estimate, "se_log": None, "ci_lower": None, "ci_upper": None}
        return {"confidence": confidence, "method": "log-Wald", "continuity_correction": None,
                "estimation_status": "zero_cell_no_log_wald_interval",
                "report_proportion_drug": p_drug, "report_proportion_background": p_background,
                "PRR": unavailable(prr), "ROR": unavailable(ror),
                "warnings": warnings + ["A cell is zero. Log-Wald intervals are not computed; no 0.5 correction was applied. Missing denominators are not interpreted as no risk."]}
    se_prr = math.sqrt(1 / a - 1 / (a + b) + 1 / c - 1 / (c + d))
    se_ror = math.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
    z = NormalDist().inv_cdf((1 + confidence) / 2)

    def result(estimate, se):
        return {
            "estimate": estimate, "se_log": se,
            "ci_lower": math.exp(math.log(estimate) - z * se),
            "ci_upper": math.exp(math.log(estimate) + z * se),
        }

    return {
        "confidence": confidence, "method": "log-Wald",
        "continuity_correction": None,
        "report_proportion_drug": p_drug,
        "report_proportion_background": p_background,
        "PRR": result(prr, se_prr), "ROR": result(ror, se_ror),
        "estimation_status": "completed",
        "warnings": warnings + (["A cell count is below 5; the approximation may be unreliable."] if min(counts) < 5 else []),
    }


def validate_audit(audit):
    if not isinstance(audit, dict) or audit.get("status") != "completed":
        raise ValueError("只能分析 status 为 completed 的计数记录")
    table = audit.get("table")
    totals = audit.get("totals")
    if not isinstance(table, dict) or not isinstance(totals, dict):
        raise ValueError("缺少 table 或 totals")
    values = [totals.get(key) for key in ("N", "ND", "NE", "NDE")]
    if any(isinstance(x, bool) or not isinstance(x, int) or x < 0 for x in values):
        raise ValueError("totals 必须包含有效的 N、ND、NE、NDE")
    n, nd, ne, nde = values
    expected = {"a": nde, "b": nd - nde, "c": ne - nde, "d": n - nd - ne + nde}
    if table != expected or any(x < 0 for x in expected.values()) or n == 0:
        raise ValueError("四格表和查询总数不一致或无有效数据")
    return table


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", type=Path, required=True, help="counts 脚本生成的 audit.json")
    parser.add_argument("--confidence", type=float, default=0.95)
    parser.add_argument("--output", type=Path, help="默认保存到 audit.json 同目录下的独立 stats 文件")
    args = parser.parse_args()
    try:
        raw = args.audit.read_bytes()
        audit = json.loads(raw)
        table = validate_audit(audit)
        statistics = compute_statistics(table, args.confidence)
        now = datetime.now(timezone.utc)
        output = args.output or args.audit.parent / ("stats_" + now.strftime("%Y%m%dT%H%M%S%fZ") + ".json")
        saved = {
            "status": "completed", "created_at_utc": now.isoformat(),
            "source_audit": str(args.audit.resolve()),
            "source_sha256": hashlib.sha256(raw).hexdigest(),
            "definition": audit.get("definition"), "table": table,
            "statistics": statistics, "source_limitations": audit.get("limitations", []),
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8") as handle:
            json.dump(saved, handle, ensure_ascii=False, indent=2, allow_nan=False)
    except (OSError, ValueError, OverflowError) as exc:
        print(f"失败：{exc}", file=sys.stderr)
        return 1
    print("四格计数：", table)
    print("Drug-group report proportion:", format_stat(statistics['report_proportion_drug'], percent=True))
    print("Background report proportion:", format_stat(statistics['report_proportion_background'], percent=True))
    for name in ("PRR", "ROR"):
        item = statistics[name]
        print(f"{name} = {format_stat(item['estimate'])} | {args.confidence:.0%} CI "
              f"[{format_stat(item['ci_lower'])}, {format_stat(item['ci_upper'])}]")
    for warning in statistics["warnings"]:
        print("提示：", warning)
    print(f"结果已保存：{output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
