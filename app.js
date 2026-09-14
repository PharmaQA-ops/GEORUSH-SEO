
const API = window.GEORUSH_API || "http://127.0.0.1:8000";
let LAST_CRAWL = null;

const $ = (s) => document.querySelector(s);
const $$ = (s) => Array.from(document.querySelectorAll(s));

async function api(path, options = {}) {
  const response = await fetch(`${API}${path}`, options);
  const text = await response.text();
  let data;
  try { data = JSON.parse(text); } catch { data = {detail:text}; }
  if (!response.ok) throw new Error(data.detail || `HTTP ${response.status}`);
  return data;
}

function showPage(page) {
  if (page === "site-audit") page = "audit";
  $$("[data-section]").forEach(s => s.hidden = true);
  const target = $(`[data-section="${page}"]`);
  if (target) target.hidden = false;

  $$(".nav-link").forEach(b => b.classList.toggle("active", b.dataset.page === page));

  const titles = {
    dashboard:"SEO Command Center", keywords:"Keywords", rankings:"Rankings",
    competitors:"Competitors", audit:"Site Audit", content:"Content",
    backlinks:"Backlinks", analytics:"Analytics"
  };
  $("#pageTitle").textContent = titles[page] || "GEORUSH SEO";
  history.replaceState(null, "", `#${page}`);
}

function initNavigation() {
  $$(".nav-link").forEach(button => {
    button.addEventListener("click", () => showPage(button.dataset.page));
  });

  const initial = location.hash.replace("#","") || "dashboard";
  showPage(initial);

  window.addEventListener("hashchange", () => {
    showPage(location.hash.replace("#","") || "dashboard");
  });
}

async function checkAPI() {
  try {
    await api("/api/health");
    $("#apiStatus").textContent = "API ONLINE";
    $("#status").textContent = "READY";
  } catch {
    $("#apiStatus").textContent = "API OFFLINE";
    $("#status").textContent = "DEMO";
  }
}

function renderResults(data) {
  LAST_CRAWL = data;
  $("#score").textContent = data.seo_score?.total ?? data.health ?? "—";
  $("#pages").textContent = data.pages ?? 0;
  $("#issues").textContent = data.issues ?? 0;
  $("#status").textContent = "COMPLETE";

  const rows = $("#rows");
  if (!data.results?.length) {
    rows.innerHTML = '<tr><td colspan="6">No crawl results.</td></tr>';
    return;
  }

  rows.innerHTML = data.results.map(x => `
    <tr>
      <td class="url">${escapeHtml(x.url)}</td>
      <td>${x.status_code ?? ""}</td>
      <td>${escapeHtml(x.title || "—")}</td>
      <td>${x.word_count ?? 0}</td>
      <td>${x.response_time_ms ?? 0} ms</td>
      <td>${escapeHtml((x.issues || []).join(", ") || "None")}</td>
    </tr>
  `).join("");
}

async function runCrawl() {
  const url = $("#site").value.trim();
  if (!url) {
    $("#msg").textContent = "Enter a website URL.";
    return;
  }

  $("#status").textContent = "RUNNING";
  $("#msg").textContent = "Crawling...";

  try {
    const data = await api("/api/crawl", {
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({url, max_pages:25})
    });
    renderResults(data);
    $("#msg").textContent = "Audit complete.";
  } catch (error) {
    $("#status").textContent = "API OFFLINE";
    $("#msg").textContent = "Start the Python API to run a live audit.";
  }
}

async function performSearch() {
  const query = $("#globalSearch").value.trim().toLowerCase();
  if (!query) {
    $("#msg").textContent = "Enter a search term.";
    return;
  }

  let results = [];
  try {
    const data = await api("/api/search", {
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({query, limit:50})
    });
    results = data.results || [];
  } catch {
    results = (LAST_CRAWL?.results || []).filter(x => {
      const hay = `${x.url} ${x.title || ""} ${x.description || ""} ${x.h1 || ""} ${(x.issues || []).join(" ")}`.toLowerCase();
      return hay.includes(query);
    });
  }

  $("#rows").innerHTML = results.length
    ? results.map(x => `<tr><td class="url">${escapeHtml(x.url)}</td><td>${x.status_code ?? ""}</td><td>${escapeHtml(x.title || "—")}</td><td>${x.word_count ?? 0}</td><td>${x.response_time_ms ?? 0} ms</td><td>${escapeHtml((x.issues || []).join(", ") || "None")}</td></tr>`).join("")
    : '<tr><td colspan="6">No matching results.</td></tr>';

  $("#msg").textContent = `${results.length} result(s) found.`;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, c => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"
  }[c]));
}

document.addEventListener("DOMContentLoaded", () => {
  initNavigation();
  checkAPI();

  $("#runAudit").addEventListener("click", runCrawl);
  $("#searchBtn").addEventListener("click", performSearch);
  $("#globalSearch").addEventListener("keydown", e => {
    if (e.key === "Enter") performSearch();
  });
});
