#!/usr/bin/env python3
"""KernelMigrate: a benchmark for accelerated-code maintenance."""

from __future__ import annotations

import argparse
import html
import json
import math
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def task_map() -> dict[str, dict[str, Any]]:
    return {task["id"]: task for task in load_json(ROOT / "tasks.json")["tasks"]}


def semantic_probes(operation: str, implementation: str) -> tuple[int, int]:
    # The strings represent independently implemented contracts in the
    # simulator. A hardware executor replaces this with differential execution.
    aliases = {
        "axpy": {"axpy", "y=a*x+y"},
        "reduce_sum": {"reduce_sum", "sum"},
        "layer_norm": {"layer_norm", "normalize(x,eps)"},
        "matvec": {"matvec", "matrix_vector"},
        "bias_gelu": {"bias_gelu", "gelu(x+bias)"},
    }
    passed = 17 if implementation in aliases.get(operation, set()) else 0
    return passed, 17


def performance_ratio(task: dict[str, Any], solution: dict[str, Any]) -> float:
    launch = solution.get("launch", {})
    optimal = task["optimal"]
    penalties = 1.0
    if launch.get("block_size") not in optimal["block_size"]:
        penalties *= 1.18
    if launch.get("vector_width") not in optimal["vector_width"]:
        penalties *= 1.14
    if launch.get("waves") not in optimal["waves"]:
        penalties *= 1.10
    if solution.get("tuning", {}).get("generated_for") != task["target"]["arch"]:
        penalties *= 1.22
    return round(penalties, 4)


def grade_task(task: dict[str, Any], solution: dict[str, Any]) -> dict[str, Any]:
    if not solution:
        return {
            "id": task["id"],
            "title": task["title"],
            "score": 0,
            "raw_score": 0,
            "max_score": 100,
            "performance_ratio": None,
            "checks": [],
            "hard_failures": ["No candidate solution was submitted."],
        }

    checks: list[dict[str, Any]] = []

    def add(dimension: str, label: str, points: float, passed: bool) -> None:
        checks.append({
            "dimension": dimension,
            "label": label,
            "points": points if passed else 0,
            "possible": points,
            "passed": passed,
        })

    passed_probes, total_probes = semantic_probes(
        task["old"]["operation"], solution.get("implementation", "")
    )
    semantic_points = 35 * passed_probes / total_probes
    checks.append({
        "dimension": "semantic",
        "label": f"Differential probes ({passed_probes}/{total_probes})",
        "points": semantic_points,
        "possible": 35,
        "passed": passed_probes == total_probes,
    })

    add("migration", "Backend migrated", 6, solution.get("backend") == task["target"]["backend"])
    add("migration", "Runtime migrated", 5, solution.get("runtime") == task["target"]["runtime"])
    apis = solution.get("apis", [])
    add("migration", "Required APIs present", 9, all(api in apis for api in task["required_api"]))

    add("target", "Target architecture declared", 8, solution.get("target") == task["target"]["arch"])
    add("target", "Tuning generated for target", 7, solution.get("tuning", {}).get("generated_for") == task["target"]["arch"])

    ratio = performance_ratio(task, solution)
    perf_pass = ratio <= task["max_regression"]
    perf_points = 20 if perf_pass else max(0, 20 * (2 - ratio / task["max_regression"]))
    checks.append({
        "dimension": "performance",
        "label": f"Estimated regression {ratio:.2f}x (limit {task['max_regression']:.2f}x)",
        "points": round(perf_points, 2),
        "possible": 20,
        "passed": perf_pass,
    })

    joined = json.dumps(solution).lower()
    add("hygiene", "Legacy tokens removed", 5, not any(token.lower() in joined for token in task["forbidden"]))
    evidence = solution.get("validation", [])
    add("hygiene", "Validation evidence recorded", 5, all(x in evidence for x in ["build", "differential", "benchmark"]))

    raw = round(sum(check["points"] for check in checks), 2)
    cap = 100
    hard_failures = []
    if passed_probes != total_probes:
        cap = min(cap, 25)
        hard_failures.append("Semantic contract was not preserved.")
    if solution.get("target") != task["target"]["arch"]:
        cap = min(cap, 50)
        hard_failures.append("Candidate targets the wrong architecture.")
    return {
        "id": task["id"],
        "title": task["title"],
        "score": min(raw, cap),
        "raw_score": raw,
        "max_score": 100,
        "performance_ratio": ratio,
        "checks": checks,
        "hard_failures": hard_failures,
    }


def grade(candidate_dir: Path) -> dict[str, Any]:
    tasks = task_map()
    results = []
    for task_id, task in tasks.items():
        path = candidate_dir / task_id / "solution.json"
        solution = load_json(path) if path.exists() else {}
        results.append(grade_task(task, solution))
    score = round(sum(item["score"] for item in results) / len(results), 2)
    return {
        "benchmark": "KernelMigrate",
        "version": "0.1.0",
        "candidate": candidate_dir.name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "score": score,
        "max_score": 100,
        "tasks": results,
    }


def render_html(report: dict[str, Any]) -> str:
    cards = []
    for task in report["tasks"]:
        rows = "".join(
            "<li class='{kind}'><span>{mark} {label}</span><b>{points:g}/{possible:g}</b></li>".format(
                kind="pass" if check["passed"] else "fail",
                mark="✓" if check["passed"] else "×",
                label=html.escape(check["label"]),
                points=check["points"],
                possible=check["possible"],
            )
            for check in task["checks"]
        )
        warnings = "".join(
            f"<p class='warning'>⚠ {html.escape(message)}</p>"
            for message in task["hard_failures"]
        )
        cards.append(
            "<section><header><div><small>{}</small><h2>{}</h2></div><strong>{:g}</strong></header>{}<ul>{}</ul></section>".format(
                html.escape(task["id"]), html.escape(task["title"]), task["score"], warnings, rows
            )
        )
    template = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>KernelMigrate report</title>
<style>:root{--bg:#090d16;--card:#111827;--ink:#e8eefb;--muted:#91a0ba;--green:#49d6a5;--red:#ff7b8a;--blue:#77a7ff}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,sans-serif}
main{max-width:920px;margin:auto;padding:48px 20px}.hero{display:flex;justify-content:space-between;align-items:end;gap:20px}
h1{font-size:clamp(2.5rem,8vw,5rem);margin:.1em 0;line-height:1}.total{font-size:3rem;font-weight:800;color:var(--blue)}
section{background:var(--card);border:1px solid #243047;border-radius:16px;padding:22px;margin:16px 0}
section header{display:flex;justify-content:space-between;gap:16px}h2{margin:.2em 0 1em;font-size:1.25rem}
small{color:var(--muted);text-transform:uppercase;letter-spacing:.1em}ul{padding:0;margin:0;list-style:none}
li{display:flex;justify-content:space-between;gap:12px;border-top:1px solid #233047;padding:8px 0}.pass{color:var(--green)}.fail,.warning{color:var(--red)}
@media(max-width:560px){.hero{display:block}.total{font-size:2.4rem}}</style></head><body><main>
<div class="hero"><div><small>Kernel maintenance benchmark</small><h1>{candidate}</h1></div><div class="total">{score:g}/100</div></div>
{cards}</main></body></html>"""
    return (
        template.replace("{candidate}", html.escape(report["candidate"]))
        .replace("{score:g}", f"{report['score']:g}")
        .replace("{cards}", "".join(cards))
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    prepare = sub.add_parser("prepare")
    prepare.add_argument("destination", type=Path)
    run_grade = sub.add_parser("grade")
    run_grade.add_argument("candidate", type=Path)
    run_grade.add_argument("--output", type=Path, default=Path("results/latest"))
    args = parser.parse_args()

    if args.command == "list":
        for task in task_map().values():
            print(f"{task['id']}: {task['brief']}")
    elif args.command == "prepare":
        shutil.copytree(ROOT / "starter_solutions", args.destination, dirs_exist_ok=True)
        print(f"Prepared {args.destination}")
    elif args.command == "grade":
        report = grade(args.candidate)
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        (args.output / "report.html").write_text(render_html(report), encoding="utf-8")
        print(f"{report['candidate']}: {report['score']:g}/100")


if __name__ == "__main__":
    main()
