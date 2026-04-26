from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup


class DomainPolicyError(RuntimeError):
    pass


class WebNavigator:
    def __init__(self, allowed_domains: set[str], timeout_s: float, user_agent: str):
        self.allowed_domains = allowed_domains
        self.timeout_s = timeout_s
        self.user_agent = user_agent

    def _assert_allowed(self, url: str) -> None:
        host = urlparse(url).netloc.lower()
        host = host[4:] if host.startswith("www.") else host
        if host not in self.allowed_domains:
            raise DomainPolicyError(f"Domain not allowed: {host}")

    def normalize_url(self, url: str) -> str:
        parsed = urlparse(url)
        scheme = parsed.scheme or "https"
        host = parsed.netloc.lower()
        host = host[4:] if host.startswith("www.") else host

        filtered_qs = [
            (k, v)
            for k, v in parse_qsl(parsed.query, keep_blank_values=True)
            if not k.lower().startswith("utm_")
        ]

        normalized = urlunparse(
            (
                scheme,
                host,
                parsed.path or "/",
                "",
                urlencode(filtered_qs),
                "",
            )
        )
        return normalized

    def fetch(self, url: str) -> tuple[str, str]:
        normalized_url = self.normalize_url(url)
        self._assert_allowed(normalized_url)
        req = Request(normalized_url, headers={"User-Agent": self.user_agent})
        with urlopen(req, timeout=self.timeout_s) as resp:
            final_url = resp.geturl()
            payload = resp.read().decode("utf-8", errors="replace")
        return payload, final_url

    def extract_title_and_text(self, html: str) -> tuple[str, str]:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        title = (soup.title.string or "Untitled").strip() if soup.title else "Untitled"
        body = " ".join(soup.get_text(" ").split())
        return title[:300], body[:4000]

    def close(self) -> None:
        return None
