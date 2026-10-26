# Autonomous Web Agent (Modular + Re-trainable)

This project is a bounded-autonomy software agent that can:
- Propose and track objectives
- Navigate the web (static fetch + optional browser mode)
- Extract findings
- Score confidence
- Produce reports
- Be trained on one specific task now and re-trained later on new tasks

## Why this design works for your goal
The core engine stays task-agnostic. Task-specific behavior is isolated in task modules and profiles.
That lets you train one task today without locking the system to only that task.

## Project layout
- `src/agent/main.py`: CLI entrypoint
- `src/agent/runner.py`: autonomous loop orchestration
- `src/agent/objectives.py`: objective generation and prioritization
- `src/agent/fetchers.py`: static + optional browser navigation
- `src/agent/extract.py`: extraction and scoring helpers
- `src/agent/store.py`: SQLite memory and run history
- `src/agent/reporter.py`: digest report generation
- `src/agent/tasks/`: task plugins

## Quick start
1. Create a virtual environment and install dependencies:
   - `python3 -m venv .venv`
   - `source .venv/bin/activate`
   - `pip install -r requirements.txt`
2. Optional (for browser mode):
   - `python -m playwright install chromium`
3. Run one cycle:
   - `PYTHONPATH=src python -m agent.main run --task trend_watch --cycles 1`
4. Run with Day 1 mission contract and thresholds:
   - `PYTHONPATH=src python -m agent.main run --task trend_watch --cycles 3 --interval 10 --mission-name daily_trend_intel --mission-statement "Track high-signal AI tooling changes daily with low false positives." --min-confidence 0.55 --min-findings 2 --max-error-rate 0.35`
5. Run with Day 2 loop hardening controls:
   - `PYTHONPATH=src python -m agent.main run --task trend_watch --cycles 3 --interval 10 --max-fetches-per-cycle 12 --max-retries-per-target 2 --retry-backoff-s 0.7 --max-consecutive-failures 6`
6. Run continuous mode:
   - `PYTHONPATH=src python -m agent.main run --task trend_watch --cycles 20 --interval 20`
7. Train/tune a task profile with feedback weights:
   - `PYTHONPATH=src python -m agent.main train --task trend_watch --novelty 1.2 --reliability 1.5 --speed 0.8`
8. Generate latest report:
   - `PYTHONPATH=src python -m agent.main report`
9. Run benchmark and record baseline metrics:
   - `PYTHONPATH=src python -m agent.main benchmark --task trend_watch --cycles 3`
10. Run Mars founder benchmark profile:
   - `PYTHONPATH=src python -m agent.main benchmark --task mars_founder --cycles 3 --mission-name mars_company_builder --mission-statement "Find high-leverage steps to build a Mars-focused aerospace company."`
11. Run with Day 7 policy/risk gates:
   - `PYTHONPATH=src python -m agent.main run --task mars_founder --cycles 5 --min-accept-confidence 0.5 --max-policy-violations-per-cycle 2`
12. Run Day 8 regression check against forgetting:
   - `PYTHONPATH=src python -m agent.main regression-check --reference-task trend_watch --candidate-task mars_founder --cycles 3 --max-pass-rate-drop 0.15`
13. Run Day 9 stability check for drift diagnostics:
   - `PYTHONPATH=src python -m agent.main stability-check --task mars_founder --run-cycles 6 --recent-window 6 --baseline-window 6`
14. Run Day 10 release readiness check:
   - `PYTHONPATH=src python -m agent.main release-check --task mars_founder --preset conservative`
15. Generate Day 10 operator runbook:
   - `PYTHONPATH=src python -m agent.main runbook --task mars_founder --preset conservative`

## Mars Software Production Mode
Use this mode when you want the system to produce software artifacts for Mars mission operations.

1. Run Mars software intelligence cycle:
   - `PYTHONPATH=src python -m agent.main run --task aerospace_software --preset conservative --cycles 1`
2. Generate product specification:
   - `PYTHONPATH=src python -m agent.main generate-spec --product-name "Mars Mission Planner" --output-dir generated_software --mission-statement "Build software for Mars mission planning and operations."`
3. Generate code scaffold:
   - `PYTHONPATH=src python -m agent.main generate-code --product-name "Mars Mission Planner" --output-dir generated_software`
4. Run generated tests:
   - `PYTHONPATH=src python -m agent.main run-tests --project-dir generated_software/mars_mission_planner`
5. Package release artifact:
   - `PYTHONPATH=src python -m agent.main package-release --project-dir generated_software/mars_mission_planner --artifact-dir release_artifacts`

Generated outputs:
- Spec: `generated_software/mars_mission_planner_spec.md`
- Code project: `generated_software/mars_mission_planner/`
- Test log: `generated_software/mars_mission_planner/test_output.txt`
- Release zip: `release_artifacts/mars_mission_planner.zip`

## Day 1 outputs
- Mission contract is enforced per run using threshold flags.
- Each cycle records metrics in SQLite: findings, average confidence, error count, action count, and pass/fail.
- Report includes the latest mission scoring snapshot.

## Day 2 outputs
- Deterministic action caps via max fetch budget per cycle.
- Retry/backoff per target fetch.
- Circuit-breaker stop when consecutive failures exceed threshold.
- Failure categorization logged per cycle (policy, timeout, network, parse, unknown).

## Day 3 outputs
- Finding deduplication by objective+source+title fingerprint.
- Objective lifecycle transitions enforced: pending -> in_progress -> done/deferred/failed.
- Audit summaries in report: event level counts and objective status counts.

## Day 4 outputs
- URL normalization for policy checks and tracking (drops fragments and utm params).
- Extraction quality guards using text length and quality score thresholds.
- Reliability calibration uses source reliability plus extraction quality.
- Final source URLs are persisted from actual fetch results.

## Day 5 outputs
- Dedicated `mars_founder` task profile and objective templates.
- Benchmark command records baseline metrics: pass rate, avg findings, avg confidence, avg error rate.
- Benchmark history is persisted in SQLite and summarized in reports.

## Day 6 outputs
- Decision trace logging for each target attempt and acceptance/rejection outcome.
- Confidence band summaries (high/medium/low) in reports.
- Recommended next actions section based on benchmark and confidence/error trends.

## Day 7 outputs
- Policy block rules for URL/content keyword matches.
- Confidence risk gate rejects low-confidence findings before persistence.
- Explicit stop condition can halt run when policy violation threshold is reached.
- Halt events are persisted and summarized in reports.

## Day 8 outputs
- Second task plugin (`security_watch`) for multi-task readiness.
- Shared-skill overlap checks between reference and candidate tasks.
- Regression-check command compares pass-rate drop to anti-forgetting threshold.
- Regression results are persisted and summarized in reports.

## Day 9 outputs
- Stability-check command for long-run drift detection using recent vs baseline windows.
- Automatic tuning recommendations based on confidence/error and pass-rate drift.
- Stability records persisted in SQLite and summarized in reports.

## Day 10 outputs
- Deployment-ready presets: balanced, conservative, aggressive.
- Release-check command computes readiness score using benchmark, regression, and stability signals.
- Operator runbook command generates a markdown runbook with preflight, commands, and escalation guidance.
- Release checks are persisted and summarized in reports.

## Safety controls
- Domain allowlist enforcement
- Max actions per cycle
- Robots and terms compliance is your responsibility before deployment
- No login/credential automation built in

## Notes
- This is an autonomy framework, not unrestricted self-direction.
- Keep objective proposals bounded by your policy rules.

## Plans

This project is free, and its license stays as is. Support it through [GitHub Sponsors](https://github.com/sponsors/fitzyracing1):

- **Free**: use the code, community support.
- **Pro ($49/month)**: priority issues and support.
- **Team ($199/month)**: priority support for your team plus early access.
