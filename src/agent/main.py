import argparse
from datetime import datetime, timezone
from pathlib import Path

from .config import AgentConfig
from .models import TaskProfile
from .presets import apply_preset
from .release import evaluate_release_readiness, generate_operator_runbook
from .reporter import generate_markdown_report
from .runner import run_agent, task_skill_overlap
from .software_factory import generate_code, generate_spec, package_release, run_tests
from .stability import analyze_stability
from .store import MemoryStore


TASK_CHOICES = ["trend_watch", "mars_founder", "security_watch", "aerospace_software"]


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def cmd_run(args: argparse.Namespace) -> None:
    cfg = _build_cfg_from_args(args)
    run_agent(task_name=args.task, cycles=args.cycles, interval_s=args.interval, cfg=cfg)
    print("Run complete.")


def cmd_train(args: argparse.Namespace) -> None:
    cfg = AgentConfig()
    store = MemoryStore(cfg.db_path)
    profile = store.get_task_profile(args.task)
    profile = TaskProfile(
        name=profile.name,
        novelty_weight=args.novelty if args.novelty is not None else profile.novelty_weight,
        reliability_weight=args.reliability if args.reliability is not None else profile.reliability_weight,
        speed_weight=args.speed if args.speed is not None else profile.speed_weight,
        notes=args.notes if args.notes is not None else profile.notes,
    )
    store.upsert_task_profile(profile)
    print(f"Updated profile for task={args.task}: {profile}")


def cmd_report(args: argparse.Namespace) -> None:
    cfg = AgentConfig()
    store = MemoryStore(cfg.db_path)
    content = generate_markdown_report(store, cfg.report_path)
    print(content)


def cmd_benchmark(args: argparse.Namespace) -> None:
    cfg = _build_cfg_from_args(args)

    run_agent(task_name=args.task, cycles=args.cycles, interval_s=args.interval, cfg=cfg)
    store = MemoryStore(cfg.db_path)
    summary = store.summarize_recent_cycle_metrics(task_name=args.task, cycles=args.cycles)
    profile = store.get_task_profile(args.task)
    notes = (
        f"benchmark task={args.task} mission={args.mission_name} samples={int(summary['samples'])}; "
        f"weights(novelty={profile.novelty_weight}, reliability={profile.reliability_weight}, speed={profile.speed_weight})"
    )
    store.save_task_benchmark(
        ts=_ts(),
        task_name=args.task,
        profile_name=profile.name,
        cycles=args.cycles,
        pass_rate=summary["pass_rate"],
        avg_findings=summary["avg_findings"],
        avg_confidence=summary["avg_confidence"],
        avg_error_rate=summary["avg_error_rate"],
        notes=notes,
    )
    print(
        "Benchmark complete "
        f"task={args.task} pass_rate={summary['pass_rate']:.2f} avg_findings={summary['avg_findings']:.2f} "
        f"avg_conf={summary['avg_confidence']:.2f} avg_error_rate={summary['avg_error_rate']:.2f}"
    )


def _build_cfg_from_args(args: argparse.Namespace) -> AgentConfig:
    cfg = AgentConfig(
        mission_name=args.mission_name,
        mission_statement=args.mission_statement,
        min_confidence=args.min_confidence,
        min_findings_per_cycle=args.min_findings,
        max_error_rate=args.max_error_rate,
        max_fetches_per_cycle=args.max_fetches_per_cycle,
        max_retries_per_target=args.max_retries_per_target,
        retry_backoff_s=args.retry_backoff_s,
        max_consecutive_failures=args.max_consecutive_failures,
        min_extracted_chars=args.min_extracted_chars,
        min_extraction_quality=args.min_extraction_quality,
        min_accept_confidence=args.min_accept_confidence,
        max_policy_violations_per_cycle=args.max_policy_violations_per_cycle,
        halt_on_policy_violation_limit=not args.disable_policy_halt,
    )
    return apply_preset(cfg, args.preset)


def cmd_regression_check(args: argparse.Namespace) -> None:
    cfg = _build_cfg_from_args(args)
    store = MemoryStore(cfg.db_path)

    run_agent(task_name=args.reference_task, cycles=args.cycles, interval_s=args.interval, cfg=cfg)
    baseline = store.summarize_recent_cycle_metrics(task_name=args.reference_task, cycles=args.cycles)

    run_agent(task_name=args.candidate_task, cycles=args.cycles, interval_s=args.interval, cfg=cfg)
    candidate = store.summarize_recent_cycle_metrics(task_name=args.candidate_task, cycles=args.cycles)

    overlap = task_skill_overlap(args.reference_task, args.candidate_task)
    drop = baseline["pass_rate"] - candidate["pass_rate"]
    passed = drop <= args.max_pass_rate_drop
    notes = (
        f"shared_skills={overlap['shared_skills']} list={overlap['shared_skill_list']} "
        f"baseline={baseline['pass_rate']:.2f} candidate={candidate['pass_rate']:.2f}"
    )
    store.save_regression_check(
        ts=_ts(),
        reference_task=args.reference_task,
        candidate_task=args.candidate_task,
        baseline_pass_rate=baseline["pass_rate"],
        candidate_pass_rate=candidate["pass_rate"],
        pass_rate_drop=drop,
        shared_skills=int(overlap["shared_skills"]),
        passed=passed,
        notes=notes,
    )
    print(
        f"Regression check passed={passed} reference={args.reference_task} candidate={args.candidate_task} "
        f"drop={drop:.2f} shared_skills={overlap['shared_skills']}"
    )


def cmd_stability_check(args: argparse.Namespace) -> None:
    cfg = _build_cfg_from_args(args)
    store = MemoryStore(cfg.db_path)
    if args.run_cycles > 0:
        run_agent(task_name=args.task, cycles=args.run_cycles, interval_s=args.interval, cfg=cfg)

    metrics = store.recent_cycle_metrics_for_task(
        task_name=args.task,
        limit=args.recent_window + args.baseline_window,
    )
    result = analyze_stability(
        metrics_desc=metrics,
        baseline_window=args.baseline_window,
        recent_window=args.recent_window,
    )
    rec_text = " | ".join(result["recommendations"])
    notes = (
        f"samples={len(metrics)}; windows(baseline={args.baseline_window}, recent={args.recent_window}); "
        f"status={result['status']}"
    )
    store.save_stability_check(
        ts=_ts(),
        task_name=args.task,
        baseline_window=args.baseline_window,
        recent_window=args.recent_window,
        baseline_pass_rate=result["baseline_pass_rate"],
        recent_pass_rate=result["recent_pass_rate"],
        pass_rate_drift=result["pass_rate_drift"],
        recent_avg_confidence=result["recent_avg_confidence"],
        recent_avg_error_rate=result["recent_avg_error_rate"],
        status=result["status"],
        recommendations=rec_text,
        notes=notes,
    )
    print(
        f"Stability check status={result['status']} drift={result['pass_rate_drift']:.2f} "
        f"recent_conf={result['recent_avg_confidence']:.2f} recent_err={result['recent_avg_error_rate']:.2f}"
    )


def cmd_release_check(args: argparse.Namespace) -> None:
    cfg = _build_cfg_from_args(args)
    store = MemoryStore(cfg.db_path)

    bench = store.recent_task_benchmarks(task_name=args.task, limit=1)
    reg = store.recent_regression_checks(limit=1)
    stab = store.recent_stability_checks(task_name=args.task, limit=1)

    benchmark_pass_rate = float(bench[0]["pass_rate"]) if bench else 0.0
    regression_passed = bool(reg[0]["passed"]) if reg else False
    stability_status = str(stab[0]["status"]) if stab else "critical"

    score, passed, status = evaluate_release_readiness(
        benchmark_pass_rate=benchmark_pass_rate,
        regression_passed=regression_passed,
        stability_status=stability_status,
    )
    notes = (
        f"status={status}; benchmark={benchmark_pass_rate:.2f}; regression={regression_passed}; "
        f"stability={stability_status}"
    )
    store.save_release_check(
        ts=_ts(),
        task_name=args.task,
        preset=args.preset,
        benchmark_pass_rate=benchmark_pass_rate,
        regression_passed=regression_passed,
        stability_status=stability_status,
        readiness_score=score,
        passed=passed,
        notes=notes,
    )
    print(
        f"Release check passed={passed} task={args.task} preset={args.preset} "
        f"readiness_score={score:.2f} status={status}"
    )


def cmd_runbook(args: argparse.Namespace) -> None:
    cfg = _build_cfg_from_args(args)
    store = MemoryStore(cfg.db_path)
    content = generate_operator_runbook(
        store=store,
        output_path=cfg.report_path.parent / "operator_runbook.md",
        task_name=args.task,
        preset=args.preset,
    )
    print(content)


def cmd_generate_spec(args: argparse.Namespace) -> None:
    result = generate_spec(
        product_name=args.product_name,
        output_dir=Path(args.output_dir),
        mission_statement=args.mission_statement,
    )
    print(f"{result.message} path={result.path}")


def cmd_generate_code(args: argparse.Namespace) -> None:
    result = generate_code(
        product_name=args.product_name,
        output_dir=Path(args.output_dir),
    )
    print(f"{result.message} path={result.path}")


def cmd_run_tests(args: argparse.Namespace) -> None:
    result = run_tests(Path(args.project_dir))
    print(f"{result.message} path={result.path}")


def cmd_package_release(args: argparse.Namespace) -> None:
    result = package_release(
        project_dir=Path(args.project_dir),
        artifact_dir=Path(args.artifact_dir),
    )
    print(f"{result.message} path={result.path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Autonomous Web Agent")
    sub = parser.add_subparsers(required=True)

    p_run = sub.add_parser("run", help="Run autonomous cycles")
    p_run.add_argument("--task", default="trend_watch", choices=TASK_CHOICES)
    p_run.add_argument("--preset", default="balanced", choices=["balanced", "conservative", "aggressive"])
    p_run.add_argument("--cycles", type=int, default=1)
    p_run.add_argument("--interval", type=int, default=0)
    p_run.add_argument("--mission-name", default="daily_trend_intel")
    p_run.add_argument(
        "--mission-statement",
        default="Track high-signal AI tooling changes daily with low false positives.",
    )
    p_run.add_argument("--min-confidence", type=float, default=0.55)
    p_run.add_argument("--min-findings", type=int, default=2)
    p_run.add_argument("--max-error-rate", type=float, default=0.35)
    p_run.add_argument("--max-fetches-per-cycle", type=int, default=12)
    p_run.add_argument("--max-retries-per-target", type=int, default=2)
    p_run.add_argument("--retry-backoff-s", type=float, default=0.7)
    p_run.add_argument("--max-consecutive-failures", type=int, default=6)
    p_run.add_argument("--min-extracted-chars", type=int, default=160)
    p_run.add_argument("--min-extraction-quality", type=float, default=0.45)
    p_run.add_argument("--min-accept-confidence", type=float, default=0.45)
    p_run.add_argument("--max-policy-violations-per-cycle", type=int, default=3)
    p_run.add_argument("--disable-policy-halt", action="store_true")
    p_run.set_defaults(func=cmd_run)

    p_train = sub.add_parser("train", help="Tune task profile weights")
    p_train.add_argument("--task", default="trend_watch", choices=TASK_CHOICES)
    p_train.add_argument("--novelty", type=float)
    p_train.add_argument("--reliability", type=float)
    p_train.add_argument("--speed", type=float)
    p_train.add_argument("--notes", type=str)
    p_train.set_defaults(func=cmd_train)

    p_report = sub.add_parser("report", help="Generate report")
    p_report.set_defaults(func=cmd_report)

    p_bench = sub.add_parser("benchmark", help="Run and record benchmark metrics")
    p_bench.add_argument("--task", default="trend_watch", choices=TASK_CHOICES)
    p_bench.add_argument("--preset", default="balanced", choices=["balanced", "conservative", "aggressive"])
    p_bench.add_argument("--cycles", type=int, default=3)
    p_bench.add_argument("--interval", type=int, default=0)
    p_bench.add_argument("--mission-name", default="task_benchmark")
    p_bench.add_argument("--mission-statement", default="Evaluate task profile quality on fixed targets.")
    p_bench.add_argument("--min-confidence", type=float, default=0.55)
    p_bench.add_argument("--min-findings", type=int, default=2)
    p_bench.add_argument("--max-error-rate", type=float, default=0.35)
    p_bench.add_argument("--max-fetches-per-cycle", type=int, default=12)
    p_bench.add_argument("--max-retries-per-target", type=int, default=2)
    p_bench.add_argument("--retry-backoff-s", type=float, default=0.7)
    p_bench.add_argument("--max-consecutive-failures", type=int, default=6)
    p_bench.add_argument("--min-extracted-chars", type=int, default=160)
    p_bench.add_argument("--min-extraction-quality", type=float, default=0.45)
    p_bench.add_argument("--min-accept-confidence", type=float, default=0.45)
    p_bench.add_argument("--max-policy-violations-per-cycle", type=int, default=3)
    p_bench.add_argument("--disable-policy-halt", action="store_true")
    p_bench.set_defaults(func=cmd_benchmark)

    p_reg = sub.add_parser("regression-check", help="Compare candidate task against reference task")
    p_reg.add_argument("--reference-task", default="trend_watch", choices=TASK_CHOICES)
    p_reg.add_argument("--candidate-task", default="mars_founder", choices=TASK_CHOICES)
    p_reg.add_argument("--preset", default="balanced", choices=["balanced", "conservative", "aggressive"])
    p_reg.add_argument("--cycles", type=int, default=3)
    p_reg.add_argument("--interval", type=int, default=0)
    p_reg.add_argument("--max-pass-rate-drop", type=float, default=0.15)
    p_reg.add_argument("--mission-name", default="regression_check")
    p_reg.add_argument("--mission-statement", default="Validate multi-task transfer without major forgetting.")
    p_reg.add_argument("--min-confidence", type=float, default=0.55)
    p_reg.add_argument("--min-findings", type=int, default=2)
    p_reg.add_argument("--max-error-rate", type=float, default=0.35)
    p_reg.add_argument("--max-fetches-per-cycle", type=int, default=12)
    p_reg.add_argument("--max-retries-per-target", type=int, default=2)
    p_reg.add_argument("--retry-backoff-s", type=float, default=0.7)
    p_reg.add_argument("--max-consecutive-failures", type=int, default=6)
    p_reg.add_argument("--min-extracted-chars", type=int, default=160)
    p_reg.add_argument("--min-extraction-quality", type=float, default=0.45)
    p_reg.add_argument("--min-accept-confidence", type=float, default=0.45)
    p_reg.add_argument("--max-policy-violations-per-cycle", type=int, default=3)
    p_reg.add_argument("--disable-policy-halt", action="store_true")
    p_reg.set_defaults(func=cmd_regression_check)

    p_stab = sub.add_parser("stability-check", help="Analyze drift and long-run stability")
    p_stab.add_argument("--task", default="trend_watch", choices=TASK_CHOICES)
    p_stab.add_argument("--preset", default="balanced", choices=["balanced", "conservative", "aggressive"])
    p_stab.add_argument("--run-cycles", type=int, default=0)
    p_stab.add_argument("--recent-window", type=int, default=8)
    p_stab.add_argument("--baseline-window", type=int, default=8)
    p_stab.add_argument("--interval", type=int, default=0)
    p_stab.add_argument("--mission-name", default="stability_check")
    p_stab.add_argument("--mission-statement", default="Detect drift and recommend runtime tuning.")
    p_stab.add_argument("--min-confidence", type=float, default=0.55)
    p_stab.add_argument("--min-findings", type=int, default=2)
    p_stab.add_argument("--max-error-rate", type=float, default=0.35)
    p_stab.add_argument("--max-fetches-per-cycle", type=int, default=12)
    p_stab.add_argument("--max-retries-per-target", type=int, default=2)
    p_stab.add_argument("--retry-backoff-s", type=float, default=0.7)
    p_stab.add_argument("--max-consecutive-failures", type=int, default=6)
    p_stab.add_argument("--min-extracted-chars", type=int, default=160)
    p_stab.add_argument("--min-extraction-quality", type=float, default=0.45)
    p_stab.add_argument("--min-accept-confidence", type=float, default=0.45)
    p_stab.add_argument("--max-policy-violations-per-cycle", type=int, default=3)
    p_stab.add_argument("--disable-policy-halt", action="store_true")
    p_stab.set_defaults(func=cmd_stability_check)

    p_rel = sub.add_parser("release-check", help="Run final release readiness checklist")
    p_rel.add_argument("--task", default="trend_watch", choices=TASK_CHOICES)
    p_rel.add_argument("--preset", default="balanced", choices=["balanced", "conservative", "aggressive"])
    p_rel.add_argument("--mission-name", default="release_check")
    p_rel.add_argument("--mission-statement", default="Evaluate deployment readiness signals.")
    p_rel.add_argument("--min-confidence", type=float, default=0.55)
    p_rel.add_argument("--min-findings", type=int, default=2)
    p_rel.add_argument("--max-error-rate", type=float, default=0.35)
    p_rel.add_argument("--max-fetches-per-cycle", type=int, default=12)
    p_rel.add_argument("--max-retries-per-target", type=int, default=2)
    p_rel.add_argument("--retry-backoff-s", type=float, default=0.7)
    p_rel.add_argument("--max-consecutive-failures", type=int, default=6)
    p_rel.add_argument("--min-extracted-chars", type=int, default=160)
    p_rel.add_argument("--min-extraction-quality", type=float, default=0.45)
    p_rel.add_argument("--min-accept-confidence", type=float, default=0.45)
    p_rel.add_argument("--max-policy-violations-per-cycle", type=int, default=3)
    p_rel.add_argument("--disable-policy-halt", action="store_true")
    p_rel.set_defaults(func=cmd_release_check)

    p_runbook = sub.add_parser("runbook", help="Generate operator runbook markdown")
    p_runbook.add_argument("--task", default="trend_watch", choices=TASK_CHOICES)
    p_runbook.add_argument("--preset", default="balanced", choices=["balanced", "conservative", "aggressive"])
    p_runbook.add_argument("--mission-name", default="runbook")
    p_runbook.add_argument("--mission-statement", default="Generate operator actions and escalation guidance.")
    p_runbook.add_argument("--min-confidence", type=float, default=0.55)
    p_runbook.add_argument("--min-findings", type=int, default=2)
    p_runbook.add_argument("--max-error-rate", type=float, default=0.35)
    p_runbook.add_argument("--max-fetches-per-cycle", type=int, default=12)
    p_runbook.add_argument("--max-retries-per-target", type=int, default=2)
    p_runbook.add_argument("--retry-backoff-s", type=float, default=0.7)
    p_runbook.add_argument("--max-consecutive-failures", type=int, default=6)
    p_runbook.add_argument("--min-extracted-chars", type=int, default=160)
    p_runbook.add_argument("--min-extraction-quality", type=float, default=0.45)
    p_runbook.add_argument("--min-accept-confidence", type=float, default=0.45)
    p_runbook.add_argument("--max-policy-violations-per-cycle", type=int, default=3)
    p_runbook.add_argument("--disable-policy-halt", action="store_true")
    p_runbook.set_defaults(func=cmd_runbook)

    p_spec = sub.add_parser("generate-spec", help="Generate a Mars software product specification")
    p_spec.add_argument("--product-name", default="Mars Mission Planner")
    p_spec.add_argument("--mission-statement", default="Build software for Mars mission planning and operations.")
    p_spec.add_argument("--output-dir", default="generated_software")
    p_spec.set_defaults(func=cmd_generate_spec)

    p_codegen = sub.add_parser("generate-code", help="Generate Mars software scaffold code")
    p_codegen.add_argument("--product-name", default="Mars Mission Planner")
    p_codegen.add_argument("--output-dir", default="generated_software")
    p_codegen.set_defaults(func=cmd_generate_code)

    p_tests = sub.add_parser("run-tests", help="Run tests for a generated Mars software project")
    p_tests.add_argument("--project-dir", required=True)
    p_tests.set_defaults(func=cmd_run_tests)

    p_pkg = sub.add_parser("package-release", help="Package generated Mars software as a release artifact")
    p_pkg.add_argument("--project-dir", required=True)
    p_pkg.add_argument("--artifact-dir", default="release_artifacts")
    p_pkg.set_defaults(func=cmd_package_release)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
