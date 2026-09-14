
const API = window.GEORUSH_API || "http://127.0.0.1:8000";
let LAST_CRAWL = null;

const $ = (s) => document.querySelector(s);
const $$ = (s) => Array.from(document.querySelectorAll(s));

async function api(path, options = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 12000);
  try {
    const response = await fetch(`${API}${path}`, { ...options, signal: controller.signal });
    const text = await response.text();
    let data;
    try { data = JSON.parse(text); } catch { data = { detail: text }; }
    if (!response.ok) throw new Error(data.detail || `HTTP ${response.status}`);
    return data;
  } finally {
    clearTimeout(timer);
  }
}

function showPage(page, updateHash = true) {
  const valid = ["dashboard","keywords","rankings","competitors","audit","content","backlinks","analytics"];
  if (!valid.includes(page)) page = "dashboard";

  $$('[data-section]').forEach(section => { section.hidden = section.dataset.section !== page; });
  $$('.nav-link').forEach(link => link.classList.toggle('active', link.dataset.page === page));

  const titles = {
    dashboard:"SEO Command Center", keywords:"Keywords", rankings:"Rankings",
    competitors:"Competitors", audit:"Site Audit", content:"Content",
    backlinks:"Backlinks", analytics:"Analytics"
  };
  const title = $('#pageTitle');
  if (title) title.textContent = titles[page];

  if (updateHash && location.hash !== `#${page}`) {
    history.replaceState(null, '', `#${page}`);
  }
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function initNavigation() {
  $$('.nav-link').forEach(link => {
    link.addEventListener('click', event => {
      event.preventDefault();
      showPage(link.dataset.page);
    });
  });
  const initial = location.hash.replace('#','') || 'dashboard';
  showPage(initial, false);
  window.addEventListener('hashchange', () => showPage(location.hash.replace('#',''), false));
}

async function checkAPI() {
  try {
    await api('/api/health');
    if ($('#apiStatus')) $('#apiStatus').textContent = 'API ONLINE';
    if ($('#status')) $('#status').textContent = 'READY';
  } catch {
    if ($('#apiStatus')) $('#apiStatus').textContent = 'API OFFLINE';
    if ($('#status')) $('#status').textContent = 'DEMO';
  }
}

function rowHtml(x) {
  return `<tr>
    <td class="url">${escapeHtml(x.url)}</td>
    <td>${x.status_code ?? ''}</td>
    <td>${escapeHtml(x.title || '—')}</td>
    <td>${x.word_count ?? 0}</td>
    <td>${x.response_time_ms ?? 0} ms</td>
    <td>${escapeHtml((x.issues || []).join(', ') || 'None')}</td>
  </tr>`;
}

function renderResults(data) {
  LAST_CRAWL = data;
  if ($('#score')) $('#score').textContent = data.seo_score?.total ?? data.health ?? '—';
  if ($('#pages')) $('#pages').textContent = data.pages ?? 0;
  if ($('#issues')) $('#issues').textContent = data.issues ?? 0;
  if ($('#status')) $('#status').textContent = 'COMPLETE';

  const rows = $('#rows');
  if (!rows) return;
  rows.innerHTML = data.results?.length ? data.results.map(rowHtml).join('') : '<tr><td colspan="6">No crawl results.</td></tr>';
}

async function runCrawl() {
  const url = $('#site')?.value.trim();
  if (!url) { $('#msg').textContent = 'Enter a website URL.'; return; }
  if ($('#status')) $('#status').textContent = 'RUNNING';
  if ($('#msg')) $('#msg').textContent = 'Crawling...';
  $('#runAudit').disabled = true;
  try {
    const data = await api('/api/crawl', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({url, max_pages:25})
    });
    renderResults(data);
    if ($('#msg')) $('#msg').textContent = 'Audit complete.';
  } catch (error) {
    if ($('#status')) $('#status').textContent = 'API OFFLINE';
    if ($('#msg')) $('#msg').textContent = 'Live audit needs the Python API running at 127.0.0.1:8000.';
  } finally { $('#runAudit').disabled = false; }
}

async function performSearch() {
  const input = $('#globalSearch');
  const query = input?.value.trim().toLowerCase();
  if (!query) { $('#msg').textContent = 'Enter a search term.'; return; }
  $('#searchBtn').disabled = true;
  if ($('#msg')) $('#msg').textContent = 'Searching...';

  let results = [];
  let online = false;
  try {
    const data = await api('/api/search', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({query, limit:50})
    });
    results = data.results || [];
    online = true;
  } catch {
    // Safe offline fallback: search the latest crawl already loaded in this browser.
    results = (LAST_CRAWL?.results || []).filter(x => {
      const hay = `${x.url} ${x.title || ''} ${x.description || ''} ${x.h1 || ''} ${(x.issues || []).join(' ')}`.toLowerCase();
      return hay.includes(query);
    });
  }

  $('#rows').innerHTML = results.length ? results.map(rowHtml).join('') : '<tr><td colspan="6">No matching results. Run an audit first, or start the GEORUSH API for live search.</td></tr>';
  $('#msg').textContent = online ? `${results.length} result(s) found.` : (LAST_CRAWL ? `${results.length} offline result(s) found from the latest crawl.` : 'API offline — run the local API for live search.');
  $('#searchBtn').disabled = false;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
}

window.GEORUSH = { showPage, runCrawl, performSearch };

document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  checkAPI();
  $('#runAudit')?.addEventListener('click', runCrawl);
  $('#searchBtn')?.addEventListener('click', performSearch);
  $('#globalSearch')?.addEventListener('keydown', e => { if (e.key === 'Enter') performSearch(); });
});
