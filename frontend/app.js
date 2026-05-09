const API = "";
let activeTag = "";
let activeSource = "";
let searchQ = "";
let offset = 0;
let totalPapers = 0;
const PAGE = 30;

const SOURCE_LABELS = {
  arxiv: "arXiv",
  semantic_scholar: "Semantic Scholar",
  alignment_forum: "Alignment Forum",
  huggingface: "HuggingFace",
};

async function fetchJSON(url) {
  const r = await fetch(url);
  return r.json();
}

function buildQuery(off = 0) {
  const params = new URLSearchParams({ limit: PAGE, offset: off });
  if (activeTag) params.set("tag", activeTag);
  if (activeSource) params.set("source", activeSource);
  if (searchQ) params.set("q", searchQ);
  return `${API}/api/papers?${params}`;
}

function renderCard(p) {
  const tags = (p.tags || "").split(",").map(t => t.trim()).filter(Boolean);
  const source = p.source || "unknown";
  const sourceLabel = SOURCE_LABELS[source] || source;
  const meta = [p.authors, p.published].filter(Boolean).join(" · ");

  return `
    <div class="paper-card">
      <div class="paper-source ${source}">${sourceLabel}</div>
      <a class="paper-title" href="${p.url}" target="_blank" rel="noopener">${escHtml(p.title)}</a>
      ${meta ? `<div class="paper-meta">${escHtml(meta)}</div>` : ""}
      ${p.summary ? `<div class="paper-summary">${escHtml(p.summary)}</div>` : ""}
      <div class="paper-tags">
        ${tags.map(t => `<span class="paper-tag" onclick="setTag('${escAttr(t)}')">${escHtml(t)}</span>`).join("")}
      </div>
      <div class="paper-links">
        <a class="paper-link" href="${p.url}" target="_blank" rel="noopener">Abstract</a>
        ${p.pdf_url ? `<a class="paper-link" href="${p.pdf_url}" target="_blank" rel="noopener">PDF</a>` : ""}
      </div>
    </div>`;
}

async function loadPapers(append = false) {
  if (!append) offset = 0;
  const data = await fetchJSON(buildQuery(offset));
  totalPapers = data.total;

  document.getElementById("paper-count").textContent =
    `${totalPapers} paper${totalPapers !== 1 ? "s" : ""}`;

  const list = document.getElementById("paper-list");
  const empty = document.getElementById("empty-state");
  const more = document.getElementById("load-more-wrap");

  if (!append) list.innerHTML = "";

  if (data.papers.length === 0 && !append) {
    empty.style.display = "block";
    more.style.display = "none";
    return;
  }
  empty.style.display = "none";

  list.insertAdjacentHTML("beforeend", data.papers.map(renderCard).join(""));
  offset += data.papers.length;
  more.style.display = offset < totalPapers ? "block" : "none";
}

async function loadSidebar() {
  const [tags, sources, stats] = await Promise.all([
    fetchJSON(`${API}/api/tags`),
    fetchJSON(`${API}/api/sources`),
    fetchJSON(`${API}/api/stats`),
  ]);

  document.getElementById("stats-badge").textContent = `${stats.total} papers`;

  const tagList = document.getElementById("tag-list");
  tagList.innerHTML = `<button class="tag-btn active" data-tag="" onclick="setTag('')">All</button>`;
  tags.forEach(([tag, cnt]) => {
    const btn = document.createElement("button");
    btn.className = "tag-btn";
    btn.dataset.tag = tag;
    btn.textContent = `${tag} (${cnt})`;
    btn.onclick = () => setTag(tag);
    tagList.appendChild(btn);
  });

  const srcList = document.getElementById("source-list");
  srcList.innerHTML = `<button class="source-btn active" data-source="" onclick="setSource('')">All</button>`;
  sources.forEach(({ source, cnt }) => {
    const btn = document.createElement("button");
    btn.className = "source-btn";
    btn.dataset.source = source;
    btn.textContent = `${SOURCE_LABELS[source] || source} (${cnt})`;
    btn.onclick = () => setSource(source);
    srcList.appendChild(btn);
  });
}

function setTag(tag) {
  activeTag = tag;
  document.querySelectorAll(".tag-btn").forEach(b => b.classList.toggle("active", b.dataset.tag === tag));
  loadPapers();
}

function setSource(source) {
  activeSource = source;
  document.querySelectorAll(".source-btn").forEach(b => b.classList.toggle("active", b.dataset.source === source));
  loadPapers();
}

let searchTimeout;
document.getElementById("search-input").addEventListener("input", e => {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    searchQ = e.target.value.trim();
    loadPapers();
  }, 350);
});

document.getElementById("load-more").addEventListener("click", () => loadPapers(true));

document.getElementById("refresh-btn").addEventListener("click", async () => {
  const btn = document.getElementById("refresh-btn");
  btn.disabled = true;
  btn.textContent = "Refreshing...";
  try {
    const r = await fetch(`${API}/api/refresh`, { method: "POST" });
    const d = await r.json();
    await loadSidebar();
    await loadPapers();
    btn.textContent = d.message || "Done";
  } catch {
    btn.textContent = "Error";
  }
  setTimeout(() => { btn.disabled = false; btn.textContent = "↻ Refresh"; }, 3000);
});

function escHtml(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}
function escAttr(s) { return escHtml(s); }

loadSidebar();
loadPapers();
