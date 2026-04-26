from .base import SearchTarget, TaskPlugin


class MarsFounderTask(TaskPlugin):
    name = "mars_founder"

    def get_targets(self) -> list[SearchTarget]:
        return [
            SearchTarget("NASA News", "https://www.nasa.gov/news/", 0.95),
            SearchTarget("ESA Newsroom", "https://www.esa.int/Newsroom", 0.9),
            SearchTarget("FAA Commercial Space", "https://www.faa.gov/space", 0.92),
            SearchTarget("SAM Contract Opportunities", "https://sam.gov/content/opportunities", 0.86),
            SearchTarget("SEC Filings Search", "https://www.sec.gov/search-filings", 0.83),
        ]

    def keywords(self) -> list[str]:
        return [
            "mars",
            "launch",
            "propulsion",
            "lunar",
            "contract",
            "license",
            "payload",
            "isru",
            "funding",
            "aerospace",
        ]

    def objective_boost(self) -> float:
        return 1.2

    def skill_tags(self) -> set[str]:
        return {"regulatory-monitoring", "procurement-analysis", "source-validation", "evidence-scoring"}
