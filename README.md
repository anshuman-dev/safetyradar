# PaperRadar ⚡

> AI safety & alignment research feed — papers from everywhere, in one place.

PaperRadar aggregates the latest research on **AI safety, LLM alignment, robotic safety, and interpretability** from across the web and delivers them in a clean, filterable feed updated daily.

**Live:** https://safetyradar-production.up.railway.app

---

## Sources

| Source | What it pulls |
|---|---|
| **arXiv** | cs.AI, cs.LG, cs.RO, cs.CL, stat.ML — filtered for safety/alignment keywords |
| **Semantic Scholar** | Semantic search across alignment, interpretability, robustness topics |
| **AI Alignment Forum** | Latest posts via RSS |
| **HuggingFace Papers** | Daily papers filtered for safety-relevant titles |

## Topic Tags

`AI Safety` · `Alignment` · `LLM Safety` · `Interpretability` · `Robotic Safety` · `Adversarial Robustness` · `Governance & Policy`

---

## Stack

- **Backend:** FastAPI + SQLite
- **Scraping:** [Apify](https://apify.com) (web automation) + direct APIs
- **Agent:** [Zynd AI](https://zynd.ai) — paper categorization agent registered on the Zynd network
- **Pipeline scheduling:** [Superplane](https://superplane.com) — daily canvas triggers the refresh pipeline
- **Hosting:** Railway
- **Frontend:** Vanilla JS + CSS, no framework

---

## Run Locally

```bash
# Clone
git clone https://github.com/anshuman-dev/paperradar
cd paperradar

# Create venv (requires Python 3.12)
python3.12 -m venv venv
./venv/bin/pip install -r requirements.txt

# Set env vars
cp .env.example .env  # add your APIFY_API_TOKEN

# Seed papers
./venv/bin/python3.12 pipeline/run.py

# Start server
./venv/bin/python3.12 -m uvicorn backend.main:app --port 8000 --reload
```

Open `http://localhost:8000`

## Pipeline

```bash
# Fetch new papers from all sources and store them
./venv/bin/python3.12 pipeline/run.py

# Start the Zynd AI categorizer agent (optional, for agent network demo)
./venv/bin/python3.12 -m backend.agent.zynd_service
```

---

## API

| Endpoint | Description |
|---|---|
| `GET /api/papers` | List papers — supports `?tag=`, `?source=`, `?q=`, `?limit=`, `?offset=` |
| `GET /api/tags` | All tags with counts |
| `GET /api/sources` | All sources with counts |
| `GET /api/stats` | Total paper count by source |
| `POST /api/refresh` | Trigger a fresh pipeline run |

---

Built for [Bot-a-thon 2026](https://bot-a-thon.theayacommunity.com) by the Aya Community.
