import httpx
import time

S2_API = "https://api.semanticscholar.org/graph/v1/paper/search"
FIELDS = "paperId,title,authors,abstract,year,externalIds,openAccessPdf,publicationDate,fieldsOfStudy"

QUERIES = [
    "AI safety alignment",
    "LLM safety robustness",
    "mechanistic interpretability",
    "AI alignment scalable oversight",
]


def fetch_recent(max_per_query: int = 20):
    papers = {}

    with httpx.Client(timeout=30) as client:
        for query in QUERIES:
            try:
                r = client.get(S2_API, params={
                    "query": query,
                    "fields": FIELDS,
                    "limit": max_per_query,
                })
                time.sleep(2)
                data = r.json()
                for item in data.get("data", []):
                    pid = item.get("paperId", "")
                    if not pid or pid in papers:
                        continue

                    ext = item.get("externalIds") or {}
                    arxiv_id = ext.get("ArXiv", "")
                    url = f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else f"https://www.semanticscholar.org/paper/{pid}"
                    pdf = (item.get("openAccessPdf") or {}).get("url", "")

                    authors = item.get("authors") or []
                    papers[pid] = {
                        "id": f"s2:{pid}",
                        "title": item.get("title", "").strip(),
                        "authors": ", ".join(a.get("name", "") for a in authors[:5]),
                        "abstract": (item.get("abstract") or "").strip(),
                        "url": url,
                        "pdf_url": pdf,
                        "source": "semantic_scholar",
                        "published": item.get("publicationDate") or str(item.get("year", "")),
                        "categories": ", ".join(item.get("fieldsOfStudy") or []),
                    }
            except Exception as e:
                print(f"[s2] error for query '{query}': {e}")

    return list(papers.values())
