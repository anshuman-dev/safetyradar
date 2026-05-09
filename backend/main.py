import sqlite3
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

from backend.database import init_db, get_conn, DB_PATH

app = FastAPI(title="SafetyRadar API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")


@app.on_event("startup")
def startup():
    init_db()
    # Seed DB in background if empty
    conn = get_conn()
    count = conn.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
    conn.close()
    if count == 0:
        import threading
        threading.Thread(target=_seed, daemon=True).start()


def _seed():
    try:
        from pipeline.run import run_pipeline
        run_pipeline(use_apify=False)
    except Exception as e:
        print(f"[startup] seed error: {e}")


@app.get("/api/papers")
def list_papers(
    tag: str = Query(None),
    source: str = Query(None),
    q: str = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
):
    conn = get_conn()
    conditions = []
    params = []

    if tag:
        conditions.append("tags LIKE ?")
        params.append(f"%{tag}%")
    if source:
        conditions.append("source = ?")
        params.append(source)
    if q:
        conditions.append("(title LIKE ? OR abstract LIKE ? OR authors LIKE ?)")
        params += [f"%{q}%", f"%{q}%", f"%{q}%"]

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    rows = conn.execute(
        f"SELECT * FROM papers {where} ORDER BY published DESC, fetched_at DESC LIMIT ? OFFSET ?",
        params + [limit, offset],
    ).fetchall()
    total = conn.execute(f"SELECT COUNT(*) FROM papers {where}", params).fetchone()[0]
    conn.close()
    return {"total": total, "papers": [dict(r) for r in rows]}


@app.get("/api/papers/{paper_id:path}")
def get_paper(paper_id: str):
    conn = get_conn()
    row = conn.execute("SELECT * FROM papers WHERE id = ?", (paper_id,)).fetchone()
    conn.close()
    if not row:
        return {"error": "not found"}
    return dict(row)


@app.get("/api/tags")
def list_tags():
    conn = get_conn()
    rows = conn.execute("SELECT tags FROM papers WHERE tags IS NOT NULL AND tags != ''").fetchall()
    conn.close()
    tag_counts: dict[str, int] = {}
    for row in rows:
        for tag in row["tags"].split(","):
            t = tag.strip()
            if t:
                tag_counts[t] = tag_counts.get(t, 0) + 1
    return sorted(tag_counts.items(), key=lambda x: -x[1])


@app.get("/api/sources")
def list_sources():
    conn = get_conn()
    rows = conn.execute("SELECT source, COUNT(*) as cnt FROM papers GROUP BY source ORDER BY cnt DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/stats")
def stats():
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
    sources = conn.execute("SELECT source, COUNT(*) as cnt FROM papers GROUP BY source").fetchall()
    conn.close()
    return {"total": total, "by_source": [dict(r) for r in sources]}


@app.post("/api/refresh")
def refresh():
    from pipeline.run import run_pipeline
    count = run_pipeline()
    return {"message": f"Fetched and stored {count} new papers"}


# Serve frontend
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
