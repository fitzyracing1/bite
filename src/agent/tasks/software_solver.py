from .base import SearchTarget, TaskPlugin


class SoftwareSolverTask(TaskPlugin):
    name = "software_solver"

    def get_targets(self) -> list[SearchTarget]:
        return [
            SearchTarget("GitHub Trending", "https://github.com/trending", 0.9),
            SearchTarget("Hacker News", "https://news.ycombinator.com/", 0.85),
            SearchTarget("ArXiv CS", "https://arxiv.org/list/cs/new", 0.86),
            SearchTarget("Hugging Face", "https://huggingface.co/models", 0.82),
            SearchTarget("TechCrunch", "https://techcrunch.com/", 0.7),
        ]

    def keywords(self) -> list[str]:
        return [
            "bug",
            "automation",
            "workflow",
            "sdk",
            "api",
            "integration",
            "devtool",
            "productivity",
            "cost reduction",
            "release",
        ]

    def objective_boost(self) -> float:
        return 1.15

    def skill_tags(self) -> set[str]:
        return {"problem-discovery", "solution-design", "source-validation", "evidence-scoring"}
