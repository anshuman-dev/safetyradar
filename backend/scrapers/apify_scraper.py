import os
import re
import httpx
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("APIFY_API_TOKEN", "")

SAFETY_KEYWORDS = {
    "safety", "alignment", "robustness", "interpretability",
    "adversarial", "jailbreak", "hallucination", "reward hacking",
    "rlhf", "constitutional", "red team", "llm safety", "ai safety",
    "misalignment", "corrigib", "oversight", "deception",
}


def _client():
    return ApifyClient(TOKEN)


def _is_relevant(text: str) -> bool:
    t = text.lower()
    return any(kw in t for kw in SAFETY_KEYWORDS)


def fetch_alignment_forum(max_items: int = 30):
    """Scrape AI Alignment Forum via Apify (light cheerio), fallback to GraphQL."""
    client = _client()
    papers = []
    try:
        run = client.actor("apify/cheerio-scraper").call(
            run_input={
                "startUrls": [{"url": "https://www.alignmentforum.org/allPosts"}],
                "maxCrawlPages": 2,
                "maxConcurrency": 1,
                "pageFunction": """
async function pageFunction(context) {
    const { $, request } = context;
    const results = [];
    $('a').each((i, el) => {
        const href = $(el).attr('href') || '';
        const title = $(el).text().trim();
        if (href.includes('/posts/') && title.length > 20) {
            results.push({
                title,
                url: href.startsWith('http') ? href : 'https://www.alignmentforum.org' + href
            });
        }
    });
    return results;
}
""",
            },
            memory_mbytes=256,
            timeout_secs=120,
        )
        dataset = client.dataset(run["defaultDatasetId"])
        seen = set()
        for item in dataset.iterate_items():
            title = (item.get("title") or "").strip()
            url = item.get("url", "")
            if not title or url in seen:
                continue
            seen.add(url)
            papers.append({
                "id": f"af:{abs(hash(url))}",
                "title": title,
                "authors": "",
                "abstract": "",
                "url": url,
                "pdf_url": "",
                "source": "alignment_forum",
                "published": "",
                "categories": "AI Alignment",
            })
            if len(papers) >= max_items:
                break
        print(f"[apify/alignment_forum] got {len(papers)} via actor")
    except Exception as e:
        print(f"[apify/alignment_forum] actor failed ({e}), using GraphQL fallback")
        papers = _fetch_alignment_forum_graphql(max_items)
    return papers


def fetch_huggingface_papers(max_items: int = 30):
    """Scrape HuggingFace daily papers via Apify (light cheerio), fallback to direct."""
    client = _client()
    papers = []
    try:
        run = client.actor("apify/cheerio-scraper").call(
            run_input={
                "startUrls": [{"url": "https://huggingface.co/papers"}],
                "maxCrawlPages": 1,
                "maxConcurrency": 1,
                "pageFunction": """
async function pageFunction(context) {
    const { $, request } = context;
    const results = [];
    $('article h3 a, .paper-title a').each((i, el) => {
        const title = $(el).text().trim();
        const href = $(el).attr('href') || '';
        if (title && href.includes('/papers/')) {
            results.push({
                title,
                url: 'https://huggingface.co' + href
            });
        }
    });
    return results;
}
""",
            },
            memory_mbytes=256,
            timeout_secs=120,
        )
        dataset = client.dataset(run["defaultDatasetId"])
        for item in dataset.iterate_items():
            title = (item.get("title") or "").strip()
            url = item.get("url", "")
            if not title or not _is_relevant(title):
                continue
            papers.append({
                "id": f"hf:{url.split('/')[-1]}",
                "title": title,
                "authors": "",
                "abstract": "",
                "url": url,
                "pdf_url": "",
                "source": "huggingface",
                "published": "",
                "categories": "LLM Safety",
            })
            if len(papers) >= max_items:
                break
        print(f"[apify/huggingface] got {len(papers)} via actor")
    except Exception as e:
        print(f"[apify/huggingface] actor failed ({e}), using direct fetch")
        papers = _fetch_huggingface_direct(max_items)
    return papers


def _fetch_alignment_forum_graphql(max_items: int = 30):
    """Fallback: AlignmentForum RSS feed."""
    papers = []
    try:
        import xml.etree.ElementTree as ET
        r = httpx.get(
            "https://www.alignmentforum.org/feed.xml",
            timeout=20,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; SafetyRadar/1.0)"},
        )
        root = ET.fromstring(r.text)
        channel = root.find("channel")
        if channel is None:
            return papers
        for item in channel.findall("item"):
            title_el = item.find("title")
            link_el = item.find("link")
            desc_el = item.find("description")
            pub_el = item.find("pubDate")
            title = title_el.text.strip() if title_el is not None else ""
            url = link_el.text.strip() if link_el is not None else ""
            desc = re.sub(r"<[^>]+>", "", desc_el.text or "") if desc_el is not None else ""
            pub = pub_el.text[:10] if pub_el is not None else ""
            if not title or not url:
                continue
            papers.append({
                "id": f"af:{abs(hash(url))}",
                "title": title,
                "authors": "",
                "abstract": desc[:400].strip(),
                "url": url,
                "pdf_url": "",
                "source": "alignment_forum",
                "published": pub,
                "categories": "AI Alignment",
            })
        papers = papers[:max_items]
        print(f"[alignment_forum/rss] got {len(papers)}")
    except Exception as e:
        print(f"[alignment_forum/rss] error: {e}")
    return papers


def _fetch_huggingface_direct(max_items: int = 30):
    """Fallback: parse HuggingFace papers page with httpx."""
    papers = []
    try:
        r = httpx.get(
            "https://huggingface.co/papers",
            timeout=20,
            headers={"User-Agent": "Mozilla/5.0 (compatible; SafetyRadar/1.0)"},
            follow_redirects=True,
        )
        # Match paper links like /papers/2506.xxxxx
        found = re.findall(
            r'href="(/papers/\d{4}\.\d{4,5})"[^>]*>([^<]{10,})</a>',
            r.text,
        )
        seen = set()
        for href, title in found:
            title = title.strip()
            url = f"https://huggingface.co{href}"
            if url in seen or not _is_relevant(title):
                continue
            seen.add(url)
            papers.append({
                "id": f"hf:{href.split('/')[-1]}",
                "title": title,
                "authors": "",
                "abstract": "",
                "url": url,
                "pdf_url": "",
                "source": "huggingface",
                "published": "",
                "categories": "LLM Safety",
            })
        papers = papers[:max_items]
        print(f"[huggingface/direct] got {len(papers)}")
    except Exception as e:
        print(f"[huggingface/direct] error: {e}")
    return papers
