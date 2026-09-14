
const API = window.GEORUSH_API || "http://127.0.0.1:8000";

function qs(s){return document.querySelector(s);}
function qsa(s){return Array.from(document.querySelectorAll(s));}

async function api(path, options={}){
  const r=await fetch(`${API}${path}`,options);
  const text=await r.text();
  let data; try{data=JSON.parse(text)}catch{data={detail:text}};
  if(!r.ok) throw new Error(data.detail||`HTTP ${r.status}`);
  return data;
}

async function checkAPI(){
  try{
    const d=await api("/api/health");
    const el=qs("#apiStatus");
    if(el){el.textContent="API ONLINE";el.className="online";}
    return d;
  }catch(e){
    const el=qs("#apiStatus");
    if(el){el.textContent="API OFFLINE";el.className="offline";}
  }
}

function rowText(row){
  return row.innerText.toLowerCase();
}

function initTableSearch(){
  const inputs=qsa('input[type="search"], input[placeholder*="Search" i], input[id*="search" i]');
  inputs.forEach(input=>{
    if(input.dataset.searchReady) return;
    input.dataset.searchReady="1";
    input.addEventListener("input",()=>{
      const term=input.value.trim().toLowerCase();
      const tables=qsa("table");
      tables.forEach(table=>{
        const rows=qsa("tbody tr",table);
        rows.forEach(row=>{row.style.display=!term||rowText(row).includes(term)?"":"none";});
      });
      qsa("[data-search-target]").forEach(el=>{
        const term2=term;
        el.style.display=!term2||rowText(el).includes(term2)?"":"none";
      });
    });
  });
}

async function startCrawl(){
  const url=(qs("#siteUrl")||qs("#url"))?.value?.trim();
  const limit=parseInt((qs("#pageLimit")||qs("#limit"))?.value||25);
  if(!url){alert("Enter a website URL.");return;}
  try{
    const d=await api("/api/crawl",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({url,max_pages:limit})});
    renderResults(d);
  }catch(e){alert("Crawler API error: "+e.message);}
}

function renderResults(d){
  const map={health:"#crawlHealth",pages:"#pages",issues:"#issues"};
  if(qs(map.health))qs(map.health).textContent=d.seo_score?.total??d.health??0;
  if(qs(map.pages))qs(map.pages).textContent=d.pages??0;
  if(qs(map.issues))qs(map.issues).textContent=d.issues??0;
  const body=qs("#resultsBody")||document.querySelector("tbody");
  if(body && d.results){
    body.innerHTML=d.results.map(x=>`<tr>
      <td>${x.url}</td><td>${x.status_code}</td><td>${x.title||"—"}</td>
      <td>${x.word_count??0}</td><td>${x.issue_count??(x.issues||[]).length}</td>
      <td>${(x.issues||[]).join(", ")||"None"}</td>
    </tr>`).join("");
    initTableSearch();
  }
}

async function searchSite(query, limit=25){
  const d=await api("/api/search",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({query,limit})});
  return d.results||[];
}

async function analyzeContent(text, keyword=""){
  return await api("/api/content/analyze",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({text,keyword})});
}

document.addEventListener("DOMContentLoaded",()=>{
  checkAPI();
  initTableSearch();
  const b=qs("#startCrawl")||qs("#startBtn");
  if(b)b.addEventListener("click",startCrawl);
  const search=qs("#globalSearch")||qs("#searchInput");
  if(search){
    search.addEventListener("keydown",async e=>{
      if(e.key==="Enter"){
        const term=search.value.trim();
        if(!term)return;
        try{
          const results=await searchSite(term);
          const body=qs("#resultsBody");
          if(body)body.innerHTML=results.map(x=>`<tr><td>${x.url}</td><td>${x.title||"—"}</td><td>${x.word_count}</td><td>${(x.issues||[]).join(", ")||"None"}</td></tr>`).join("");
        }catch(err){console.error(err);alert("Search error: "+err.message);}
      }
    });
  }
});
