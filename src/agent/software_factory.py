import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FactoryResult:
    ok: bool
    message: str
    path: Path | None = None


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
    return slug or "aerospace_app"


def generate_spec(product_name: str, output_dir: Path, mission_statement: str) -> FactoryResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    slug = _slug(product_name)
    spec_path = output_dir / f"{slug}_spec.md"

    spec = [
        f"# Product Spec: {product_name}",
        "",
        "## Mission",
        f"- {mission_statement}",
        "",
        "## Problem",
        "- Aerospace teams need repeatable mission-planning workflows and software evidence trails.",
        "",
        "## Core Capabilities",
        "- Ingest mission constraints (vehicle, orbit, payload, weather windows).",
        "- Produce validated mission plans with risk flags.",
        "- Record traceable decisions and assumptions for review.",
        "",
        "## Non-Functional Requirements",
        "- Deterministic outputs from same inputs.",
        "- Structured logs and test coverage >= 80% for planning logic.",
        "- Exportable plan artifacts in JSON and Markdown.",
        "",
        "## Interfaces",
        "- CLI: create-plan, score-risk, export-report.",
        "- Python API: mission_planner.core module.",
        "",
        "## Test Strategy",
        "- Unit tests for constraints and scoring.",
        "- Integration test for end-to-end plan generation.",
    ]
    spec_path.write_text("\n".join(spec) + "\n", encoding="utf-8")
    return FactoryResult(True, "Specification generated.", spec_path)


def generate_code(product_name: str, output_dir: Path) -> FactoryResult:
    slug = _slug(product_name)
    root = output_dir / slug
    pkg = root / "mission_planner"
    tests = root / "tests"

    pkg.mkdir(parents=True, exist_ok=True)
    tests.mkdir(parents=True, exist_ok=True)

    (tests / "__init__.py").write_text("", encoding="utf-8")

    (root / "README.md").write_text(
        "# Aerospace Mission Planner\n\n"
        "Generated scaffold for aerospace mission-planning software.\n",
        encoding="utf-8",
    )

    (pkg / "__init__.py").write_text(
        "from .core import build_plan, score_risk\n",
        encoding="utf-8",
    )

    (pkg / "core.py").write_text(
        "from dataclasses import dataclass\n\n"
        "@dataclass\n"
        "class MissionInput:\n"
        "    payload_mass_kg: float\n"
        "    orbit_altitude_km: float\n"
        "    launch_window_hours: float\n\n"
        "def score_risk(inp: MissionInput) -> float:\n"
        "    score = 0.0\n"
        "    if inp.payload_mass_kg > 5000:\n"
        "        score += 0.35\n"
        "    if inp.orbit_altitude_km > 800:\n"
        "        score += 0.25\n"
        "    if inp.launch_window_hours < 2:\n"
        "        score += 0.30\n"
        "    return min(1.0, score)\n\n"
        "def build_plan(inp: MissionInput) -> dict:\n"
        "    risk = score_risk(inp)\n"
        "    return {\n"
        "        'payload_mass_kg': inp.payload_mass_kg,\n"
        "        'orbit_altitude_km': inp.orbit_altitude_km,\n"
        "        'launch_window_hours': inp.launch_window_hours,\n"
        "        'risk_score': risk,\n"
        "        'risk_band': 'high' if risk >= 0.7 else 'medium' if risk >= 0.35 else 'low',\n"
        "    }\n",
        encoding="utf-8",
    )

    (pkg / "cli.py").write_text(
        "import argparse\n"
        "import json\n"
        "from .core import MissionInput, build_plan\n\n"
        "def main() -> None:\n"
        "    p = argparse.ArgumentParser(description='Aerospace Mission Planner')\n"
        "    p.add_argument('--payload-mass-kg', type=float, required=True)\n"
        "    p.add_argument('--orbit-altitude-km', type=float, required=True)\n"
        "    p.add_argument('--launch-window-hours', type=float, required=True)\n"
        "    args = p.parse_args()\n"
        "    inp = MissionInput(args.payload_mass_kg, args.orbit_altitude_km, args.launch_window_hours)\n"
        "    print(json.dumps(build_plan(inp), indent=2))\n\n"
        "if __name__ == '__main__':\n"
        "    main()\n",
        encoding="utf-8",
    )

    (tests / "test_core.py").write_text(
        "import unittest\n\n"
        "from mission_planner.core import MissionInput, build_plan, score_risk\n\n"
        "class CoreTests(unittest.TestCase):\n"
        "    def test_score_risk_low(self):\n"
        "        inp = MissionInput(payload_mass_kg=1200, orbit_altitude_km=450, launch_window_hours=6)\n"
        "        self.assertLess(score_risk(inp), 0.35)\n\n"
        "    def test_build_plan_has_keys(self):\n"
        "        inp = MissionInput(payload_mass_kg=6000, orbit_altitude_km=900, launch_window_hours=1.5)\n"
        "        plan = build_plan(inp)\n"
        "        self.assertIn('risk_score', plan)\n"
        "        self.assertIn('risk_band', plan)\n\n"
        "if __name__ == '__main__':\n"
        "    unittest.main()\n",
        encoding="utf-8",
    )

    (root / "pyproject.toml").write_text(
        "[build-system]\n"
        "requires = ['setuptools>=61.0']\n"
        "build-backend = 'setuptools.build_meta'\n\n"
        "[project]\n"
        f"name = '{slug}'\n"
        "version = '0.1.0'\n"
        "description = 'Generated aerospace mission planning scaffold'\n"
        "requires-python = '>=3.10'\n",
        encoding="utf-8",
    )

    return FactoryResult(True, "Software scaffold generated.", root)


def run_tests(project_dir: Path) -> FactoryResult:
    if not project_dir.exists():
        return FactoryResult(False, "Project directory does not exist.")

    cmd = ["/opt/homebrew/bin/python3.13", "-m", "unittest", "-v", "tests.test_core"]
    proc = subprocess.run(cmd, cwd=project_dir, text=True, capture_output=True)
    combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
    out_path = project_dir / "test_output.txt"
    out_path.write_text(combined, encoding="utf-8")

    if "Ran 0 tests" in combined:
        return FactoryResult(False, "No tests were executed. See test_output.txt", out_path)

    if proc.returncode == 0:
        return FactoryResult(True, "Tests passed.", out_path)
    return FactoryResult(False, "Tests failed. See test_output.txt", out_path)


def package_release(project_dir: Path, artifact_dir: Path) -> FactoryResult:
    if not project_dir.exists():
        return FactoryResult(False, "Project directory does not exist.")

    artifact_dir.mkdir(parents=True, exist_ok=True)
    base_name = artifact_dir / project_dir.name
    archive_path = Path(shutil.make_archive(str(base_name), "zip", root_dir=project_dir))

    manifest = {
        "project": project_dir.name,
        "archive": archive_path.name,
        "includes": ["mission_planner", "tests", "README.md", "pyproject.toml"],
    }
    manifest_path = artifact_dir / f"{project_dir.name}_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return FactoryResult(True, "Release package created.", archive_path)
