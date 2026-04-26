import hashlib
from datetime import datetime, timezone

from .models import Objective


def _obj_id(seed: str) -> str:
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]


def default_objectives_for_task(task_name: str) -> list[Objective]:
    now = datetime.now(timezone.utc).isoformat()

    if task_name == "trend_watch":
        seeds = [
            ("Track notable new AI repos this week", "site:github.com ai agent framework released", 0.95),
            ("Find practical browser automation updates", "browser automation release notes", 0.85),
            ("Compare major model provider announcements", "model provider new feature release", 0.8),
        ]
    elif task_name == "security_watch":
        seeds = [
            ("Find new vulnerability advisories", "security advisory CVE browser automation", 0.95),
            ("Track dependency exploit reports", "dependency exploit report python package", 0.9),
            ("Monitor incident response postmortems", "incident postmortem outage analysis", 0.8),
            ("Track zero-day mitigation guidance", "zero day mitigation guidance cisa", 0.88),
        ]
    elif task_name == "mars_founder":
        seeds = [
            ("Track Mars mission procurement opportunities", "mars mission procurement request for proposal aerospace", 0.98),
            ("Find launch and licensing regulatory changes", "commercial launch licensing update FAA", 0.93),
            ("Monitor propulsion and ISRU breakthroughs", "in-situ resource utilization mars propulsion breakthrough", 0.9),
            ("Track space startup funding and filings", "space startup funding sec filing", 0.86),
        ]
    elif task_name == "aerospace_software":
        seeds = [
            (
                "Generate Mars mission planning software requirements",
                "mars mission planning software requirements telemetry guidance",
                0.99,
            ),
            (
                "Design flight software architecture for Mars operations",
                "mars flight software architecture fault tolerance avionics",
                0.95,
            ),
            (
                "Build verification and simulation test strategy",
                "mars simulation verification test strategy software",
                0.92,
            ),
            (
                "Package release artifacts for mission planning product",
                "software release packaging aerospace mission planner",
                0.88,
            ),
        ]
    elif task_name == "software_solver":
        seeds = [
            (
                "Find costly manual engineering workflows to automate",
                "developer workflow automation repetitive manual process",
                0.97,
            ),
            (
                "Identify integration pain points in modern stacks",
                "api integration pain point engineering team",
                0.94,
            ),
            (
                "Discover newly released dev tools with unmet onboarding needs",
                "new developer tool release onboarding setup complexity",
                0.9,
            ),
            (
                "Track high-signal bug classes suitable for productized fixes",
                "common production bug class root cause fix template",
                0.88,
            ),
        ]
    else:
        seeds = [
            ("General tech landscape scan", "software release notes this week", 0.7),
            ("Identify high-signal sources", "engineering blog launch update", 0.65),
        ]

    out: list[Objective] = []
    for title, query, priority in seeds:
        seed = f"{task_name}|{title}|{query}"
        out.append(
            Objective(
                id=_obj_id(seed),
                title=title,
                query=query,
                priority=priority,
                status="pending",
                created_at=now,
                updated_at=now,
                metadata={"task": task_name},
            )
        )
    return out


def reprioritize(objectives: list[Objective], novelty_boost: float = 1.0) -> list[Objective]:
    for obj in objectives:
        obj.priority = round(obj.priority * novelty_boost, 4)
    return sorted(objectives, key=lambda x: x.priority, reverse=True)
