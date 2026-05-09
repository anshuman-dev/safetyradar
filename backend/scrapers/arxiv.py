import httpx
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

ARXIV_API = "https://export.arxiv.org/api/query"
NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

SAFETY_QUERIES = [
    "AI safety",
    "alignment LLM",
    "robotic safety",
    "value alignment",
    "reward hacking",
    "interpretability transformer",
    "adversarial robustness",
    "AI alignment",
    "safe reinforcement learning",
    "constitutional AI",
]

CATEGORIES = ["cs.AI", "cs.LG", "cs.RO", "cs.CL", "stat.ML"]


def _parse_entry(entry):
    title_el = entry.find("atom:title", NS)
    abstract_el = entry.find("atom:summary", NS)
    published_el = entry.find("atom:published", NS)
    id_el = entry.find("atom:id", NS)

    if not all([title_el is not None, id_el is not None]):
        return None

    arxiv_id = id_el.text.strip().split("/abs/")[-1]
    authors = [
        a.find("atom:name", NS).text
        for a in entry.findall("atom:author", NS)
        if a.find("atom:name", NS) is not None
    ]
    cats = [
        c.get("term", "")
        for c in entry.findall("atom:category", NS)
    ]

    return {
        "id": f"arxiv:{arxiv_id}",
        "title": (title_el.text or "").strip().replace("\n", " "),
        "authors": ", ".join(authors[:5]),
        "abstract": (abstract_el.text or "").strip().replace("\n", " ") if abstract_el is not None else "",
        "url": f"https://arxiv.org/abs/{arxiv_id}",
        "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}",
        "source": "arxiv",
        "published": (published_el.text or "")[:10] if published_el is not None else "",
        "categories": ", ".join(cats),
    }


def fetch_recent(days: int = 7, max_results: int = 50):
    papers = {}
    since = (datetime.utcnow() - timedelta(days=days)).strftime("%Y%m%d")

    for query in SAFETY_QUERIES:
        cat_filter = " OR ".join(f"cat:{c}" for c in CATEGORIES)
        search = f'({cat_filter}) AND all:"{query}"'
        params = {
            "search_query": search,
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
        try:
            r = httpx.get(ARXIV_API, params=params, timeout=30)
            root = ET.fromstring(r.text)
            for entry in root.findall("atom:entry", NS):
                p = _parse_entry(entry)
                if p and p["id"] not in papers:
                    papers[p["id"]] = p
        except Exception as e:
            print(f"[arxiv] error for query '{query}': {e}")

    return list(papers.values())
