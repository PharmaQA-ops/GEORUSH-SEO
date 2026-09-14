
const API = window.GEORUSH_API || "http://127.0.0.1:8000";
let LAST_CRAWL = null;
function qs(s){return document.querySelector(s)}
function qsa(s){return Array.from(document.querySelectorAll(s))}
async function api(path,options={}){
 const r=await fetch(`${API}${path}`,options),t=await r.text(); let d;
 try{d=JSON.parse(t)}catch{d={detail:t}}
 if(!r.ok)throw new Error(d.detail||`HTTP ${r.status}`); return d;
}
function normalizePage(text){
 const x=(text||"").trim().toLowerCase();
 const map={"dashboard":"dashboard","keywords":"keywords","rankings":"rankings","competitors":"competitors",
 "site audit":"audit","audit":"audit","content":"content","backlinks":"backlinks","analytics":"analytics"};
 return map[x]||x.replace(/[^a-z0-9]+/g,"-");
}
function navItems(){return qsa("nav a,nav button,.sidebar a,.sidebar button,.menu a,.menu button,[data-page],[role='navigation'] a")}
function setActiveNav(a){navItems().forEach(x=>x.classList.remove("active"));if(a)a.classList.add("active")}
function showPage(page){
 const aliases={ "site-audit":"audit" }; page=aliases[page]||page;
 qsa("[data-section],[data-page-section],.georush-page-section").forEach(s=>s.style.display="none");
 const target=qs(`[data-section="${page}"]`)||qs(`[data-page-section="${page}"]`)||qs(`#${page}`);
 if(target)target.style.display="";
 const title=qs("#pageTitle"); if(title)title.textContent=page==="audit"?"Site Audit":page[0].toUpperCase()+page.slice(1);
 if(!target&&page!=="dashboard"){
  const host=qs("main")||qs(".main-content")||qs(".content")||document.body;
  let p=qs("#georush-module-placeholder");
  if(!p){p=document.createElement("section");p.id="georush-module-placeholder";p.style.cssText="padding:32px;margin:24px;border-radius:16px;background:#fff";host.appendChild(p)}
  p.innerHTML=`<h2>${page==="audit"?"Site Audit":page[0].toUpperCase()+page.slice(1)}</h2><p>GEORUSH ${page} module.</p>`;p.style.display="";
 }
 window.scrollTo({top:0,behavior:"smooth"});
}
function initSidebarNavigation(){
 document.addEventListener("click",e=>{
  const el=e.target.closest("a,button,[data-page],li,.nav-item,.menu-item,.sidebar-item,div,span"); if(!el)return;
  const sidebar=el.closest("nav,.sidebar,.menu,[role='navigation']"); if(!sidebar)return;
  const page=normalizePage(el.dataset.page||el.getAttribute("aria-label")||el.textContent);
  if(!["dashboard","keywords","rankings","competitors","audit","content","backlinks","analytics"].includes(page))return;
  e.preventDefault();e.stopPropagation();setActiveNav(el);showPage(page);
  try{history.pushState({page},"",`#${page}`)}catch(_){}
 },true);
}
function initHash(){const p=(location.hash||"#dashboard").slice(1)||"dashboard";showPage(p);const n=navItems().find(x=>normalizePage(x.dataset.page||x.textContent)===p);if(n)setActiveNav(n)}
window.addEventListener("popstate",initHash);
async function checkAPI(){
 try{await api("/api/health");const e=qs("#apiStatus");if(e){e.textContent="API ONLINE";e.className="online"}}catch(_){const e=qs("#apiStatus");if(e){e.textContent="DEMO / API OFFLINE";e.className="offline"}}
}
function initTableSearch(){
 qsa('input[type="search"],input[placeholder*="Search" i],input[id*="search" i]').forEach(i=>{
  if(i.dataset.searchReady)return;i.dataset.searchReady="1";
  i.addEventListener("input",()=>{const t=i.value.toLowerCase();qsa("table tbody tr").forEach(r=>r.style.display=!t||r.innerText.toLowerCase().includes(t)?"":"none")})
 })
}
function renderResults(d){
 LAST_CRAWL=d; const score=d.seo_score?.total??d.health??0;
 if(qs("#crawlHealth"))qs("#crawlHealth").textContent=score;
 if(qs("#pages"))qs("#pages").textContent=d.pages??0;
 if(qs("#issues"))qs("#issues").textContent=d.issues??0;
 const b=qs("#resultsBody")||document.querySelector("tbody");
 if(b&&d.results)b.innerHTML=d.results.map(x=>`<tr><td>${x.url}</td><td>${x.status_code??""}</td><td>${x.title||"—"}</td><td>${x.word_count??0}</td><td>${x.response_time_ms??""}</td><td>${(x.issues||[]).join(", ")||"None"}</td></tr>`).join("");
}
async function startCrawl(){
 const url=(qs("#siteUrl")||qs("#url"))?.value?.trim(),limit=parseInt((qs("#pageLimit")||qs("#limit"))?.value||25);
 if(!url){alert("Enter a website URL.");return}
 try{renderResults(await api("/api/crawl",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({url,max_pages:limit})}))}
 catch(_){alert("Start the GEORUSH API locally. GitHub Pages can serve the UI but cannot run Python.")}
}
async function searchSite(query,limit=25){
 try{const d=await api("/api/search",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({query,limit})});return d.results||[]}
 catch(_){const q=query.toLowerCase();return(LAST_CRAWL?.results||[]).filter(x=>`${x.url} ${x.title||""} ${x.description||""} ${x.h1||""}`.toLowerCase().includes(q)).slice(0,limit)}
}
async function runAI(question){
 try{return await api("/api/ai/ask",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({question,context:LAST_CRAWL||{}}))}
 catch(_){return{summary:"GEORUSH AI demo mode. Connect the API for live analysis.",insights:["Run a site audit.","Connect GSC.","Connect Analytics."]}}
}
document.addEventListener("DOMContentLoaded",()=>{
 checkAPI();initTableSearch();initSidebarNavigation();initHash();
 const b=qs("#startCrawl")||qs("#startBtn");if(b)b.addEventListener("click",startCrawl);
 const s=qs("#globalSearch")||qs("#searchInput");if(s)s.addEventListener("keydown",async e=>{if(e.key==="Enter"){const r=await searchSite(s.value.trim());const b=qs("#resultsBody");if(b)b.innerHTML=r.map(x=>`<tr><td>${x.url}</td><td>${x.title||"—"}</td><td>${x.word_count??0}</td><td>${(x.issues||[]).join(", ")||"None"}</td></tr>`).join("")}});
});
