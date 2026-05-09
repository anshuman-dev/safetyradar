import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from backend.database import init_db, get_conn
from backend.scrapers import arxiv, semantic_scholar, apify_scraper
from backend.agent.categorizer import tag_paper


def run_pipeline(use_apify: bool = True) -> int:
    init_db()
    conn = get_conn()
    new_count = 0

    sources = [
        ("arXiv", arxiv.fetch_recent),
        ("Semantic Scholar", semantic_scholar.fetch_recent),
    ]
    if use_apify:
        sources += [
            ("AI Alignment Forum", apify_scraper.fetch_alignment_forum),
            ("HuggingFace Papers", apify_scraper.fetch_huggingface_papers),
        ]

    for name, fetcher in sources:
        print(f"\n[pipeline] Fetching from {name}...")
        try:
            papers = fetcher()
            print(f"[pipeline] Got {len(papers)} papers from {name}")
        except Exception as e:
            print(f"[pipeline] Error fetching {name}: {e}")
            papers = []

        for paper in papers:
            existing = conn.execute("SELECT id FROM papers WHERE id = ?", (paper["id"],)).fetchone()
            if existing:
                continue
            paper = tag_paper(paper)
            conn.execute(
                """INSERT OR IGNORE INTO papers
                   (id, title, authors, abstract, url, pdf_url, source, published, categories, tags, summary)
                   VALUES (:id, :title, :authors, :abstract, :url, :pdf_url, :source, :published, :categories, :tags, :summary)""",
                paper,
            )
            new_count += 1

    conn.commit()
    conn.close()
    print(f"\n[pipeline] Done. {new_count} new papers stored.")
    return new_count


if __name__ == "__main__":
    run_pipeline()
