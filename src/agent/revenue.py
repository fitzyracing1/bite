import csv
from pathlib import Path
from typing import Iterable


def lead_score(confidence: float, novelty: float) -> float:
    return round((0.7 * confidence) + (0.3 * novelty), 4)


def revenue_angle(title: str, snippet: str) -> str:
    text = f"{title} {snippet}".lower()
    if "security" in text or "compliance" in text:
        return "Security/compliance advisory outreach"
    if "api" in text or "sdk" in text or "framework" in text:
        return "Implementation services and integration retainers"
    if "benchmark" in text or "performance" in text:
        return "Optimization consulting package"
    if "launch" in text or "product" in text or "release" in text:
        return "Early-adopter enablement and training"
    return "General AI automation consulting outreach"


def append_leads_csv(path: Path, leads: Iterable[dict[str, str | int | float]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(leads)
    headers = [
        "finding_id",
        "discovered_at",
        "objective_id",
        "objective_title",
        "title",
        "source_url",
        "confidence",
        "novelty",
        "lead_score",
        "revenue_angle",
    ]
    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if not exists:
            writer.writeheader()
        if not rows:
            return 0
        for row in rows:
            writer.writerow(
                {
                    "finding_id": row["id"],
                    "discovered_at": row["discovered_at"],
                    "objective_id": row["objective_id"],
                    "objective_title": row["objective_title"],
                    "title": row["title"],
                    "source_url": row["source_url"],
                    "confidence": row["confidence"],
                    "novelty": row["novelty"],
                    "lead_score": lead_score(float(row["confidence"]), float(row["novelty"])),
                    "revenue_angle": revenue_angle(str(row["title"]), str(row["snippet"])),
                }
            )
    return len(rows)
