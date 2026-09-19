const configuredAPI = window.GEORUSH_API || "";
const API = configuredAPI || ((window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") ? "http://127.0.0.1:8000" : "");
let LAST_CRAWL = null;
let INTELLIGENCE = {competitors:null, radar:null, recommendations:[], ai:null};
const $ = s => document.querySelector(s);
const $$ = s => Array.from(document.querySelectorAll(s));

async function api(path, options = {}) {
  const controller = new AbortController();
  const timeoutMs = options.timeoutMs || (/research|intelligence|ai\//i.test(path) ? 15 * 60 * 1000 : 30000);
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(`${API}${path}`, {...options, timeoutMs: undefined, signal: controller.signal});
    const text = await response.text();
    let data; try { data = JSON.parse(text); } catch { data = {detail:text}; }
    if (!response.ok) throw new Error(data.detail || `HTTP ${response.status}`);
    return data;
  } finally { clearTimeout(timer); }
}

const titles = {dashboard:"SEO Command Center",keywords:"Keywords",rankings:"Rankings",competitors:"Competitors",audit:"Site Audit",content:"Content",backlinks:"Backlinks",analytics:"Analytics",reports:"Reports"};
function showPage(page, updateHash=true) {
  if (!titles[page]) page="dashboard";
  $$('[data-section]').forEach(s => s.hidden = s.dataset.section !== page);
  $$('.nav-link').forEach(a => a.classList.toggle('active', a.dataset.page===page));
  if ($('#pageTitle')) $('#pageTitle').textContent=titles[page];
  if (updateHash && location.hash !== `#${page}`) history.replaceState(null,'',`#${page}`);
  renderModule(page);
  window.scrollTo({top:0,behavior:'smooth'});
}
function initNavigation(){
  $$('.nav-link').forEach(a=>a.addEventListener('click',e=>{e.preventDefault();showPage(a.dataset.page);}));
  showPage(location.hash.replace('#','')||'dashboard',false);
  window.addEventListener('hashchange',()=>showPage(location.hash.replace('#',''),false));
}
async function checkAPI(){if(!API){$('#apiStatus').textContent='CLOUD API NOT CONFIGURED';return;}try{await api('/api/health');$('#apiStatus').textContent='API ONLINE';}catch{$('#apiStatus').textContent='API OFFLINE';}}
function escapeHtml(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));}
function rowHtml(x){return `<tr><td class="url">${escapeHtml(x.url)}</td><td>${x.status_code??''}</td><td>${escapeHtml(x.title||'—')}</td><td>${x.word_count??0}</td><td>${x.response_time_ms??0} ms</td><td>${escapeHtml((x.issues||[]).join(', ')||'None')}</td></tr>`;}
function renderResults(data){LAST_CRAWL=data; localStorage.setItem('GEORUSH_LAST_CRAWL',JSON.stringify(data));$('#score').textContent=data.seo_score?.total??'—';$('#pages').textContent=data.pages??0;$('#issues').textContent=data.issues??0;$('#status').textContent='COMPLETE';$('#rows').innerHTML=data.results?.length?data.results.map(rowHtml).join(''):'<tr><td colspan="6">No crawl results.</td></tr>';renderAllModules();}
function loadSaved(){try{const x=JSON.parse(localStorage.getItem('GEORUSH_LAST_CRAWL')||'null');if(x&&Array.isArray(x.results))LAST_CRAWL=x;}catch{}}
async function runCrawl(){const url=$('#site')?.value.trim();if(!url){$('#msg').textContent='Enter a website URL.';return;}$('#status').textContent='RUNNING';$('#msg').textContent='Crawling...';$('#runAudit').disabled=true;try{const data=await api('/api/crawl',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url,max_pages:25})});renderResults(data);$('#msg').textContent='Audit complete.';}catch(e){$('#status').textContent='API OFFLINE';$('#msg').textContent=!API?'Cloud API is not configured yet. Deploy the API and set api-config.js.':'Crawl failed: '+(e.message||'API unavailable.');}finally{$('#runAudit').disabled=false;}}
async function performSearch(){const q=$('#globalSearch')?.value.trim().toLowerCase();if(!q){$('#msg').textContent='Enter a search term.';return;}$('#searchBtn').disabled=true;$('#msg').textContent='Searching...';let results=[];let online=false;try{const d=await api('/api/search',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query:q,limit:50})});results=d.results||[];online=true;}catch{results=(LAST_CRAWL?.results||[]).filter(x=>`${x.url} ${x.title||''} ${x.description||''} ${x.h1||''} ${(x.issues||[]).join(' ')}`.toLowerCase().includes(q));}$('#rows').innerHTML=results.length?results.map(rowHtml).join(''):'<tr><td colspan="6">No matching results.</td></tr>';$('#msg').textContent=online?`${results.length} result(s) found.`:`${results.length} offline result(s) found.`;$('#searchBtn').disabled=false;showPage('dashboard');}

function metric(label,value,sub=''){return `<div class="metric"><small>${escapeHtml(label)}</small><strong>${escapeHtml(value)}</strong><span>${escapeHtml(sub)}</span></div>`;}
function pages(){return LAST_CRAWL?.results||[];}
function issueSeverity(issue){if(/HTTP_ERROR|CRAWL_ERROR|BROKEN/i.test(issue))return'Critical';if(/MISSING|DUPLICATE|MULTIPLE|TOO_LONG|THIN/i.test(issue))return'Warning';return'Info';}

let KEYWORDS = [];

function demoKeywords(){
  return [
    {query:"pharma logistics",intent:"Commercial",clicks:42,impressions:1280,ctr:3.28,position:8.4},
    {query:"pharmaceutical logistics company",intent:"Commercial",clicks:31,impressions:910,ctr:3.41,position:11.2},
    {query:"cold chain logistics india",intent:"Informational",clicks:27,impressions:1460,ctr:1.85,position:14.7},
    {query:"dangerous goods logistics",intent:"Commercial",clicks:19,impressions:740,ctr:2.57,position:9.8},
    {query:"pharma freight forwarding",intent:"Transactional",clicks:14,impressions:510,ctr:2.75,position:18.3},
    {query:"gaerish logistics",intent:"Navigational",clicks:88,impressions:640,ctr:13.75,position:2.1}
  ];
}
function keywordOpportunity(k){
  const volume=Number(k.impressions)||0, pos=Number(k.position)||99, ctr=Number(k.ctr)||0;
  let score=(Math.min(volume/1000,10)*4)+(Math.max(0,25-pos)*2)+(Math.max(0,5-ctr)*3);
  return Math.max(0,Math.min(100,Math.round(score)));
}
function renderKeywordTable(){
  const filter=($('#keywordFilter')?.value||'').toLowerCase();
  const intent=$('#keywordIntentFilter')?.value||'';
  const rows=KEYWORDS.filter(k=>
    (!filter || String(k.query).toLowerCase().includes(filter)) &&
    (!intent || k.intent===intent)
  );
  const totalClicks=KEYWORDS.reduce((n,k)=>n+(Number(k.clicks)||0),0);
  const totalImp=KEYWORDS.reduce((n,k)=>n+(Number(k.impressions)||0),0);
  const avgPos=KEYWORDS.length?KEYWORDS.reduce((n,k)=>n+(Number(k.position)||0),0)/KEYWORDS.length:0;
  const opp=KEYWORDS.filter(k=>keywordOpportunity(k)>=50).length;
  if($('#keywordMetrics')) $('#keywordMetrics').innerHTML=
    metric('Keywords',KEYWORDS.length,'Loaded')+
    metric('Clicks',totalClicks.toLocaleString(),'Total')+
    metric('Impressions',totalImp.toLocaleString(),'Total')+
    metric('Opportunities',opp,'Score ≥ 50')+
    metric('Avg. Position',avgPos?avgPos.toFixed(1):'—','All keywords');
  if($('#keywordRows')) $('#keywordRows').innerHTML=rows.length?rows.map(k=>`<tr><td><b>${escapeHtml(k.query)}</b></td><td>${escapeHtml(k.intent||'—')}</td><td>${Number(k.clicks||0).toLocaleString()}</td><td>${Number(k.impressions||0).toLocaleString()}</td><td>${Number(k.ctr||0).toFixed(2)}%</td><td>${Number(k.position||0).toFixed(1)}</td><td><span class="badge">${keywordOpportunity(k)}</span></td></tr>`).join(''):'<tr><td colspan="7">No matching keywords.</td></tr>';
}
function parseCsv(text){
  const lines=text.replace(/\r/g,'').split('\n').filter(Boolean);
  if(!lines.length)return [];
  const parseLine=line=>{const out=[];let cur='',quote=false;for(let i=0;i<line.length;i++){const c=line[i];if(c==='"' && line[i+1]==='"'){cur+='"';i++;continue;}if(c==='"'){quote=!quote;continue;}if(c===','&&!quote){out.push(cur.trim());cur='';}else cur+=c;}out.push(cur.trim());return out;};
  const headers=parseLine(lines[0]).map(x=>x.toLowerCase());
  const find=(names)=>{const i=headers.findIndex(h=>names.some(n=>h===n||h.includes(n)));return i;};
  const qi=find(['query','keyword','top queries']), ci=find(['clicks','click']), ii=find(['impressions','impression']), ti=find(['ctr']), pi=find(['position','average position']);
  return lines.slice(1).map(line=>{
    const v=parseLine(line);
    const ctrRaw=String(v[ti]??'').replace('%','');
    return {query:v[qi]||'',intent:'Commercial',clicks:Number(v[ci]||0),impressions:Number(v[ii]||0),ctr:Number(ctrRaw||0),position:Number(v[pi]||0)};
  }).filter(x=>x.query);
}
function initKeywords(){
  $('#keywordDemo')?.addEventListener('click',()=>{KEYWORDS=demoKeywords();$('#keywordSource').textContent='DEMO DATA';renderKeywordTable();});
  $('#keywordFilter')?.addEventListener('input',renderKeywordTable);
  $('#keywordIntentFilter')?.addEventListener('change',renderKeywordTable);
  $('#keywordCsv')?.addEventListener('change',async e=>{
    const f=e.target.files?.[0];if(!f)return;
    KEYWORDS=parseCsv(await f.text());$('#keywordSource').textContent='GSC CSV';renderKeywordTable();
  });
}


async function discoverCompetitors(){
  const target=$('#site')?.value.trim(); if(!target)return;
  const btn=$('#discoverCompetitors'); if(btn)btn.disabled=true;
  if($('#competitorResult'))$('#competitorResult').innerHTML='<div class="empty-state">Discovering relevant competitor domains and analyzing them...</div>';
  try{
    const keywords=KEYWORDS.slice(0,8).map(x=>x.query);
    const d=await api('/api/competitor/discover',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({target,keywords,limit:5})});
    INTELLIGENCE.competitors=d;
    renderCompetitorIntelligence(d);
  }catch(e){
    if($('#competitorResult'))$('#competitorResult').innerHTML=`<div class="empty-state">Competitor discovery failed: ${escapeHtml(e.message||'API unavailable')}</div>`;
  }finally{if(btn)btn.disabled=false;}
}
function renderCompetitorIntelligence(d){
  const comps=d?.competitors?.competitors||[];
  const target=d?.competitors?.target||d?.target||{};
  if(!$('#competitorResult'))return;
  if(!comps.length){$('#competitorResult').innerHTML='<div class="empty-state">No automatic competitors were discovered. Add a competitor URL manually.</div>';return;}
  const ts=target.signals||{};
  $('#competitorResult').innerHTML=`<div class="intel-summary"><b>Target:</b> ${escapeHtml(d.target||'')} · <b>Top discovered competitor:</b> ${escapeHtml(comps[0].url||'')}</div>
  <div class="table-wrap"><table><thead><tr><th>Domain</th><th>Signal Score</th><th>Words</th><th>H1</th><th>Response</th><th>Canonical</th><th>HTTPS</th></tr></thead><tbody>${comps.map(c=>{const s=c.signals||{};return `<tr><td><b>${escapeHtml(c.url)}</b></td><td>${c.signal_score??0}</td><td>${s.word_count??0}</td><td>${s.h1_count??0}</td><td>${c.response_time_ms??0} ms</td><td>${s.canonical?'Yes':'No'}</td><td>${s.https?'Yes':'No'}</td></tr>`}).join('')}</tbody></table></div>`;
}
async function runRadar(url){
  try{
    const d=await api('/api/radar/scan',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url})});
    INTELLIGENCE.radar=d; return d;
  }catch(e){return {error:e.message||'Radar unavailable'};}
}
async function runMultiAgentResearch(){
  const target=$('#site')?.value.trim(); if(!target)return;
  const btn=$('#deepResearch'); if(btn)btn.disabled=true;
  const box=$('#deepResearchResult');
  if(box)box.innerHTML='<div class="empty-state"><b>GEORUSH 3-Agent Local Deep Research running...</b><br>Agent 1: competitor research · Agent 2: SEO/keyword research · Agent 3: critical review and synthesis.<br>This may take a few minutes.</div>' ;
  try{
    const keywords=KEYWORDS.slice(0,10).map(x=>x.query);
    const d=await api('/api/research/multi-agent',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({target,keywords,competitor_limit:5})});
    if(!d.success)throw new Error(d.error||'Research failed');
    const r=d.report||{}; const c=d.agents?.competitor||{}; const seo=d.agents?.seo||{};
    const rows=(r.critical_findings||[]).map(x=>`<tr><td>${escapeHtml(x.priority||'—')}</td><td>${escapeHtml(x.finding||x.area||'—')}</td><td>${escapeHtml(x.recommendation||x.action||'—')}</td></tr>`).join('');
    const opp=(r.opportunities||[]).map(x=>`<li>${escapeHtml(typeof x==='string'?x:(x.opportunity||x.action||JSON.stringify(x)))}</li>`).join('');
    const plan=(r.action_plan||[]).map(x=>`<tr><td>${escapeHtml(x.timeframe||'—')}</td><td>${(x.actions||[]).map(a=>escapeHtml(a)).join('<br>')}</td></tr>`).join('');
    box.innerHTML=`<div class="report-header"><h2>GEORUSH AI — 3-Agent Deep Research</h2><p>${escapeHtml(target)} · ${new Date().toLocaleString()}</p></div>
    <div class="intel-summary"><b>Executive summary:</b> ${escapeHtml(r.executive_summary||'—')}<br><b>Confidence:</b> ${escapeHtml(r.confidence||'—')}<br><b>Top competitor:</b> ${escapeHtml(r.top_competitor||'—')}<br><small>Three-agent research: competitor analyst + SEO/keyword analyst + critical reviewer.</small></div>
    ${rows?`<h3>Critical Findings</h3><table class="report-table"><thead><tr><th>Priority</th><th>Finding</th><th>Recommendation</th></tr></thead><tbody>${rows}</tbody></table>`:''}
    ${opp?`<h3>Opportunities</h3><ul>${opp}</ul>`:''}
    ${plan?`<h3>Action Plan</h3><table class="report-table"><thead><tr><th>Timeframe</th><th>Actions</th></tr></thead><tbody>${plan}</tbody></table>`:''}
    <h3>Research Evidence</h3><p>${d.evidence?.search_results?.length||0} search result records and ${d.evidence?.pages?.length||0} website pages were collected for the agents.</p>
    <details><summary>Agent 1 — Competitor Research</summary><pre>${escapeHtml(JSON.stringify(c,null,2))}</pre></details>
    <details><summary>Agent 2 — SEO / Keyword Research</summary><pre>${escapeHtml(JSON.stringify(seo,null,2))}</pre></details>
    <details><summary>Agent 3 — Critical Review</summary><pre>${escapeHtml(JSON.stringify(r,null,2))}</pre></details>
    <p><b>Limitations:</b> ${(r.limitations||[]).map(x=>escapeHtml(x)).join(' · ')||'None reported.'}</p>`;
  }catch(e){if(box)box.innerHTML=`<div class="empty-state"><b>Deep research failed.</b><br>${escapeHtml(e.message||'API unavailable')}</div>`;}
  finally{if(btn)btn.disabled=false;}
}
async function buildFullIntelligence(){
  const target=$('#site')?.value.trim();if(!target)return null;
  const keywords=KEYWORDS.slice(0,8).map(x=>x.query);
  const d=await api('/api/intelligence/full',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({target,keywords,competitor_limit:5,radar:true})});
  INTELLIGENCE=d;
  return d;
}
function intelligenceHtml(d){
  const comps=d?.competitors?.competitors||[];
  const radar=d?.radar?.summary||{};
  const rec=d?.recommendations||[];
  const gem=d?.ollama||{};
  const gemOk=gem && gem.success!==false && Array.isArray(gem.recommendations);
  const gemRows=gemOk ? gem.recommendations : [];
  const actionPlan=gemOk ? (gem.action_plan||[]) : [];
  const fallbackRec=rec.length ? `<table class="report-table"><thead><tr><th>Priority</th><th>Area</th><th>Recommendation</th></tr></thead><tbody>${rec.map(r=>`<tr><td>${escapeHtml(r.priority)}</td><td>${escapeHtml(r.area)}</td><td>${escapeHtml(r.action)}</td></tr>`).join('')}</tbody></table>` : '<p>No rules-based recommendations generated.</p>';
  return `<div class="report-section"><h3>Automatic Competitor Analysis</h3><p>GEORUSH discovered and inspected ${comps.length} competitor domain(s) using the target's keyword/topic signals.</p>
  ${comps.length?`<table class="report-table"><thead><tr><th>Competitor</th><th>Signal Score</th><th>Words</th><th>H1</th><th>Response</th><th>HTTPS</th></tr></thead><tbody>${comps.map(c=>{const s=c.signals||{};return `<tr><td>${escapeHtml(c.url)}</td><td>${c.signal_score??0}</td><td>${s.word_count??0}</td><td>${s.h1_count??0}</td><td>${c.response_time_ms??0} ms</td><td>${s.https?'Yes':'No'}</td></tr>`}).join('')}</tbody></table>`:'<p>No competitor data returned.</p>'}</div>
  <div class="report-section"><h3>Cloudflare Radar / URL Scanner</h3><p>Radar provides supplementary security, performance, technology and network signals. ${radar.radar_url?`<a href="${escapeHtml(radar.radar_url)}" target="_blank" rel="noopener">Open Cloudflare Radar scan</a>`:'Radar scan link unavailable.'}</p>
  <table class="report-table"><tbody><tr><th>Radar Rank</th><td>${escapeHtml(radar.radar_rank??'Not available')}</td></tr><tr><th>Country</th><td>${escapeHtml(radar.country??'Not available')}</td></tr><tr><th>ASN</th><td>${escapeHtml(radar.asn??'Not available')}</td></tr><tr><th>Security verdict</th><td>${radar.malicious===true?'Malicious verdict reported':'No malicious verdict reported / not available'}</td></tr><tr><th>API status</th><td>${radar.configured?'Configured':'Public Radar link only — API credentials not configured'}</td></tr></tbody></table></div>
  <div class="report-section"><h3>GEORUSH AI — Local Ollama Agent</h3>${gemOk?`<div class="intel-summary"><b>Overall priority:</b> ${escapeHtml(gem.overall_priority||'—')}<br><b>Executive summary:</b> ${escapeHtml(gem.executive_summary||'—')}<br><small>Model: ${escapeHtml(gem.model||'Ollama')} · Evidence-driven GEORUSH agent</small></div>
  <table class="report-table"><thead><tr><th>Priority</th><th>Area</th><th>Finding</th><th>Recommendation</th><th>Evidence</th></tr></thead><tbody>${gemRows.map(r=>`<tr><td>${escapeHtml(r.priority)}</td><td>${escapeHtml(r.area)}</td><td>${escapeHtml(r.finding)}</td><td>${escapeHtml(r.recommendation)}</td><td>${escapeHtml(r.evidence)}</td></tr>`).join('')}</tbody></table>
  ${actionPlan.length?`<h4>AI Action Plan</h4><table class="report-table"><thead><tr><th>Timeframe</th><th>Actions</th></tr></thead><tbody>${actionPlan.map(x=>`<tr><td>${escapeHtml(x.timeframe)}</td><td>${(x.actions||[]).map(a=>escapeHtml(a)).join('<br>')}</td></tr>`).join('')}</tbody></table>`:''}
  ${gem.data_gaps?.length?`<p><b>Data gaps:</b> ${gem.data_gaps.map(x=>escapeHtml(x)).join(' · ')}</p>`:''}`:`<div class="empty-state"><b>Local Ollama Agent not available.</b><br>${escapeHtml(gem.error||'Start Ollama and ensure the configured local model is installed.')}<br><br><b>GEORUSH fallback recommendations</b><br>${fallbackRec}</div>`}</div>
  <div class="report-section"><h3>GEORUSH Rules-Based Recommendations</h3>${fallbackRec}</div>`;
}

function reportData(){
  const ps=pages(), score=LAST_CRAWL?.seo_score||{}, counts={};
  ps.forEach(p=>(p.issues||[]).forEach(i=>counts[i]=(counts[i]||0)+1));
  return {ps,score,counts};
}
function chartBarHtml(ps){
  const items=ps.slice(0,10).map((p,i)=>({label:(p.url||'Page '+(i+1)).replace(/^https?:\/\//,'').replace(/\/$/,'').slice(0,18),value:Number(p.word_count||0)}));
  const max=Math.max(...items.map(x=>x.value),1);
  return `<div class="chart-card"><h4>Words by crawled page</h4><p>Page content volume from the latest audit.</p><div class="report-bar-chart">${items.map(x=>`<div class="report-bar" style="--bar-h:${Math.max(4,(x.value/max)*150)}px"><i></i><em>${x.value.toLocaleString()}</em><span>${escapeHtml(x.label)}</span></div>`).join('')}</div></div>`;
}
function chartPieHtml(counts){
  const entries=Object.entries(counts).sort((a,b)=>b[1]-a[1]).slice(0,4);
  if(!entries.length) return `<div class="chart-card"><h4>Issue mix</h4><p>No issues detected.</p></div>`;
  const total=entries.reduce((n,x)=>n+x[1],0);
  let acc=0, stops=[];
  const shades=['#172535','#64748b','#a8b2bd','#d8dee5'];
  entries.forEach((e,i)=>{const start=acc/total*360;acc+=e[1];const end=acc/total*360;stops.push(`${shades[i]} ${start}deg ${end}deg`)});
  while(stops.length<4){const s=stops.length===0?'#172535':'#d8dee5';stops.push(`${s} 0deg 0deg`);}
  return `<div class="chart-card"><h4>Issue mix</h4><p>Distribution of the most frequent detected issues.</p><div class="report-pie-wrap"><div class="report-pie" style="background:conic-gradient(${stops.join(',')})"></div><div class="report-legend">${entries.map((e,i)=>`<div><i style="background:${shades[i]}"></i><span>${escapeHtml(e[0])}: <b>${e[1]}</b></span></div>`).join('')}</div></div></div>`;
}
function buildReportHtml(){
  const {ps,score,counts}=reportData();
  const title=$('#reportTitle')?.value.trim()||'GEORUSH SEO Audit Report';
  const company=$('#reportCompany')?.value.trim()||LAST_CRAWL?.url||'Website';
  const issues=Object.entries(counts).sort((a,b)=>b[1]-a[1]);
  const totalWords=ps.reduce((n,p)=>n+(p.word_count||0),0);
  const totalIssues=Object.values(counts).reduce((a,b)=>a+b,0);
  return `<div class="report-header"><h2>${escapeHtml(title)}</h2><p><b>${escapeHtml(company)}</b> · Generated ${new Date().toLocaleString()}</p></div>
  <div class="report-kpis">
    <div class="report-kpi"><small>SEO Score</small><strong>${escapeHtml(score.total??'—')}</strong></div>
    <div class="report-kpi"><small>Pages Crawled</small><strong>${ps.length}</strong></div>
    <div class="report-kpi"><small>Total Issues</small><strong>${totalIssues}</strong></div>
    <div class="report-kpi"><small>Total Words</small><strong>${totalWords.toLocaleString()}</strong></div>
  </div>
  <div class="report-charts">${chartPieHtml(counts)}${chartBarHtml(ps)}</div>
  <div class="report-section"><h3>Priority Issues</h3>${issues.length?`<table class="report-table"><thead><tr><th>Issue</th><th>Pages</th><th>Severity</th></tr></thead><tbody>${issues.map(([i,n])=>`<tr><td>${escapeHtml(i)}</td><td>${n}</td><td>${issueSeverity(i)}</td></tr>`).join('')}</tbody></table>`:'<p>No issues detected.</p>'}</div>
  <div class="report-section"><h3>Page Summary</h3><table class="report-table"><thead><tr><th>URL</th><th>Status</th><th>Title</th><th>Words</th><th>Load</th><th>Issues</th></tr></thead><tbody>${ps.map(p=>`<tr><td>${escapeHtml(p.url)}</td><td>${p.status_code??0}</td><td>${escapeHtml(p.title||'—')}</td><td>${p.word_count??0}</td><td>${p.response_time_ms??0} ms</td><td>${escapeHtml((p.issues||[]).join(', ')||'None')}</td></tr>`).join('')}</tbody></table></div>
  <div class="report-foot">Generated by GEORUSH SEO Intelligence.</div>`;
}
async function generateReport(){
  if(!pages().length){$('#reportPreview').innerHTML='<div class="empty-state">Run an audit first.</div>';return;}
  $('#reportPreview').innerHTML='<div class="empty-state">Building SEO report, competitor analysis, Cloudflare Radar signals and GEORUSH AI recommendations...</div>';
  try{
    const d=await buildFullIntelligence();
    $('#reportPreview').innerHTML=buildReportHtml()+intelligenceHtml(d);
  }catch(e){
    $('#reportPreview').innerHTML=buildReportHtml()+`<div class="report-section"><h3>Intelligence Add-on</h3><p>Automatic intelligence unavailable: ${escapeHtml(e.message||'API unavailable')}.</p></div>`;
  }
}
function downloadBlob(name,type,text){const blob=new Blob([text],{type});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(a.href),1000);}
async function downloadReport(){
  if(!pages().length){await generateReport();if(!pages().length)return;}
  if(!INTELLIGENCE?.competitors){await generateReport();}
  const title=($('#reportTitle')?.value||'GEORUSH SEO Audit Report').replace(/[^\w-]+/g,'-');
  const reportCss=`body{font:14px Arial;margin:40px;color:#172535}.report-kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.report-kpi{border:1px solid #ddd;padding:12px}.report-kpi small{display:block;color:#667}.report-kpi strong{font-size:24px}.report-charts{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin:20px 0}.chart-card{border:1px solid #ddd;border-radius:8px;padding:15px}.report-bar-chart{display:flex;align-items:flex-end;gap:8px;height:190px;border-bottom:1px solid #ddd}.report-bar{flex:1;position:relative;height:100%;display:flex;align-items:flex-end;justify-content:center}.report-bar i{display:block;width:70%;height:var(--bar-h);background:#172535;border-radius:3px 3px 0 0}.report-bar span{position:absolute;bottom:-25px;font-size:9px}.report-pie-wrap{display:flex;gap:20px;align-items:center}.report-pie{width:150px;height:150px;border-radius:50%}table{width:100%;border-collapse:collapse}th,td{border-bottom:1px solid #ddd;padding:8px;text-align:left;font-size:12px}@media(max-width:800px){.report-charts{grid-template-columns:1fr}}`;
  const doc=`<!doctype html><html><head><meta charset="utf-8"><title>${escapeHtml(title)}</title><style>${reportCss}</style></head><body>${buildReportHtml()}${intelligenceHtml(INTELLIGENCE)}</body></html>`;
  downloadBlob(`${title}.html`,'text/html;charset=utf-8',doc);
}
async function printReport(){
  if(!pages().length){await generateReport();if(!pages().length)return;}
  if(!INTELLIGENCE?.competitors){await generateReport();}
  const report=$('#reportPreview');if(!report)return;
  document.body.classList.add('printing-report');window.print();
  setTimeout(()=>document.body.classList.remove('printing-report'),1000);
}
function renderReports(){if($('#reportPreview')&&pages().length&&!$('#reportPreview').dataset.generated){generateReport();$('#reportPreview').dataset.generated='1';}}

function renderKeywords(){const el=$('#keywordRows');if(!el)return;$('#keywordSource').textContent='GSC REQUIRED';$('#keywordMetrics').innerHTML=metric('Queries','—','Connect GSC')+metric('Clicks','—','Connect GSC')+metric('Impressions','—','Connect GSC')+metric('Avg. Position','—','Connect GSC');el.innerHTML='<tr><td colspan="7">Real keyword queries are not available until Google Search Console is connected. Your crawl data is ready for GSC mapping.</td></tr>';}
function renderRankings(){const ps=pages();$('#rankingMetrics').innerHTML=metric('Pages',ps.length,ps.length?'Crawled pages':'Run audit')+metric('HTTP 200',ps.filter(p=>p.status_code===200).length,'Healthy responses')+metric('Pages with issues',ps.filter(p=>(p.issues||[]).length).length,'Needs attention')+metric('Best content depth',ps.length?Math.max(...ps.map(p=>p.word_count||0)):'—','Words');$('#rankingRows').innerHTML=ps.length?ps.slice().sort((a,b)=>(b.word_count||0)-(a.word_count||0)).map(p=>`<tr><td>${escapeHtml(p.url)}</td><td>${(p.issues||[]).length?'Needs optimization':'Healthy'}</td><td>${p.word_count||0}</td><td>${p.h1_count??(p.h1?1:0)}</td><td>${escapeHtml((p.issues||[]).join(', ')||'None')}</td></tr>`).join(''):'<tr><td colspan="5">Run an audit first.</td></tr>';}
async function inspectCompetitor(){const url=$('#competitorUrl').value.trim();if(!url)return;$('#inspectCompetitor').disabled=true;$('#competitorResult').innerHTML='<div class="empty-state">Inspecting competitor...</div>';try{const d=await api('/api/competitor/inspect',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url})});if(d.error)throw new Error(d.error);const s=d.signals||{};$('#competitorResult').innerHTML=`<div class="compare-card"><h3>${escapeHtml(d.final_url||d.url)}</h3><div class="metric-grid">${metric('HTTP Status',d.status,'Response')}${metric('Load',`${d.response_time_ms} ms`,'Response time')}${metric('Words',s.word_count||0,'Page content')}${metric('H1 Count',s.h1_count||0,'Headings')}${metric('Internal Links',s.internal_links||0,'Discovered')}${metric('External Links',s.external_links||0,'Discovered')}</div><p><b>Title:</b> ${escapeHtml(s.title||'—')}</p><p><b>Description:</b> ${escapeHtml(s.description||'—')}</p></div>`;}catch(e){$('#competitorResult').innerHTML=`<div class="empty-state">Competitor inspection failed: ${escapeHtml(e.message||'Unknown error')}</div>`;}finally{$('#inspectCompetitor').disabled=false;}}
function renderAudit(){const ps=pages();const score=LAST_CRAWL?.seo_score||{};$('#auditGrade').textContent=score.grade?`${score.grade} • ${score.total}`:'NO AUDIT';const counts={};ps.forEach(p=>(p.issues||[]).forEach(i=>counts[i]=(counts[i]||0)+1));$('#auditMetrics').innerHTML=metric('SEO Score',score.total??'—',score.grade||'Run audit')+metric('Pages',ps.length,'Crawled')+metric('Issue types',Object.keys(counts).length,'Unique checks')+metric('Total issues',Object.values(counts).reduce((a,b)=>a+b,0),'Across pages');$('#issueSummary').innerHTML=Object.entries(counts).sort((a,b)=>b[1]-a[1]).map(([i,n])=>`<div class="issue-card"><span class="severity ${issueSeverity(i).toLowerCase()}">${issueSeverity(i)}</span><b>${escapeHtml(i)}</b><strong>${n}</strong><small>page${n===1?'':'s'}</small></div>`).join('')||'<div class="empty-state">No issues detected.</div>';$('#auditRows').innerHTML=ps.length?ps.map(p=>`<tr><td>${escapeHtml(p.url)}</td><td>${p.status_code??0}</td><td>${p.issues?.length?issueSeverity(p.issues[0]):'Healthy'}</td><td>${escapeHtml((p.issues||[]).join(', ')||'None')}</td><td>${p.response_time_ms??0} ms</td></tr>`).join(''):'<tr><td colspan="5">Run an audit first.</td></tr>';}
function renderContent(){const ps=pages();const thin=ps.filter(p=>(p.word_count||0)<300).length;const missingDesc=ps.filter(p=>!p.description).length;const multiH1=ps.filter(p=>(p.h1_count||0)>1).length;$('#contentMetrics').innerHTML=metric('Pages',ps.length,'Crawled')+metric('Thin pages',thin,'Under 300 words')+metric('Missing descriptions',missingDesc,'Meta description')+metric('Multiple H1',multiH1,'Heading structure');$('#contentRows').innerHTML=ps.length?ps.map(p=>`<tr><td>${escapeHtml(p.url)}</td><td>${escapeHtml(p.title||'—')}</td><td>${p.word_count||0}</td><td>${p.description?escapeHtml(p.description.slice(0,100)):'Missing'}</td><td>${p.h1_count??(p.h1?1:0)}</td><td>${escapeHtml((p.issues||[]).filter(i=>/TITLE|DESCRIPTION|H1|THIN_CONTENT/i.test(i)).join(', ')||'None')}</td></tr>`).join(''):'<tr><td colspan="6">Run an audit first.</td></tr>';}
function renderBacklinks(){const ps=pages();const internal=ps.reduce((n,p)=>n+(p.internal_links||0),0),external=ps.reduce((n,p)=>n+(p.external_links||0),0);$('#backlinkMetrics').innerHTML=metric('Pages',ps.length,'Crawled')+metric('Internal links',internal,'Discovered')+metric('External links',external,'Discovered')+metric('Avg internal/page',ps.length?(internal/ps.length).toFixed(1):'—','Crawl signal');$('#backlinkRows').innerHTML=ps.length?ps.map(p=>`<tr><td>${escapeHtml(p.url)}</td><td>${p.internal_links??0}</td><td>${p.external_links??0}</td><td>${(p.internal_links||0)>0?'Connected':'Orphan-like signal'}</td></tr>`).join(''):'<tr><td colspan="4">Run an audit first.</td></tr>';}
function renderAnalytics(){const ps=pages();const avg=ps.length?Math.round(ps.reduce((n,p)=>n+(p.response_time_ms||0),0)/ps.length):0;$('#analyticsMetrics').innerHTML=metric('Pages crawled',ps.length,'Crawler')+metric('Avg load',avg?`${avg} ms`:'—','Response time')+metric('HTTP 200',ps.filter(p=>p.status_code===200).length,'Healthy responses')+metric('Total words',ps.reduce((n,p)=>n+(p.word_count||0),0).toLocaleString(),'Crawled content');$('#analyticsCrawlerStatus').textContent=ps.length?`${ps.length} pages loaded from latest audit`:'No audit loaded';}
function renderCompetitor(){if(!$('#competitorUrl').value && $('#site').value)$('#competitorUrl').value='';}
function renderAllModules(){renderKeywordTable();renderRankings();renderAudit();renderContent();renderBacklinks();renderAnalytics();renderCompetitor();}
function renderModule(page){if(page==='keywords')renderKeywordTable();if(page==='reports')renderReports();if(page==='rankings')renderRankings();if(page==='audit')renderAudit();if(page==='content')renderContent();if(page==='backlinks')renderBacklinks();if(page==='analytics')renderAnalytics();}
window.GEORUSH={showPage,runCrawl,performSearch};
document.addEventListener('DOMContentLoaded',()=>{loadSaved();initNavigation();checkAPI();if(LAST_CRAWL)renderResults(LAST_CRAWL);$('#runAudit')?.addEventListener('click',runCrawl);$('#searchBtn')?.addEventListener('click',performSearch);$('#globalSearch')?.addEventListener('keydown',e=>{if(e.key==='Enter')performSearch();});$('#inspectCompetitor')?.addEventListener('click',inspectCompetitor);$('#discoverCompetitors')?.addEventListener('click',discoverCompetitors);initKeywords();$('#generateReport')?.addEventListener('click',generateReport);$('#fullIntelReport')?.addEventListener('click',generateReport);$('#deepResearch')?.addEventListener('click',runMultiAgentResearch);$('#downloadReport')?.addEventListener('click',downloadReport);$('#downloadReportCsv')?.addEventListener('click',downloadReportCsv);$('#printReport')?.addEventListener('click',printReport);});
