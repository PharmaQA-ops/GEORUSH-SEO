
const API = "http://127.0.0.1:8000";
const $ = (s) => document.querySelector(s);

async function checkAPI(){
  try {
    const r=await fetch(`${API}/api/health`);
    const d=await r.json();
    const el=$("#apiStatus");
    if(el){el.textContent=d.status==="ok"?"API ONLINE":"API ERROR";el.className="online";}
  } catch(e) {
    const el=$("#apiStatus");
    if(el){el.textContent="API OFFLINE";el.className="offline";}
  }
}
async function startCrawl(){
  const url=($("#siteUrl")||$("#url"))?.value?.trim();
  const limit=parseInt(($("#pageLimit")||$("#limit"))?.value||25);
  if(!url) return alert("Enter a website URL.");
  try{
    const r=await fetch(`${API}/api/crawl`,{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({url,max_pages:limit})});
    const d=await r.json();
    renderResults(d);
  }catch(e){alert("Cannot connect to GEORUSH API. Start main.py first.");}
}
function renderResults(d){
  const health=$("#crawlHealth")||$("#health");
  const pages=$("#pages");
  const issues=$("#issues");
  if(health) health.textContent=d.health;
  if(pages) pages.textContent=d.pages;
  if(issues) issues.textContent=d.issues;
  const body=$("#resultsBody")||document.querySelector("tbody");
  if(!body)return;
  body.innerHTML=d.results.map(x=>`<tr>
    <td>${x.url}</td><td>${x.status_code}</td><td>${x.title||"—"}</td>
    <td>${x.word_count}</td><td>${x.issue_count}</td>
    <td>${x.issues.join(", ")||"None"}</td>
  </tr>`).join("");
}
document.addEventListener("DOMContentLoaded",()=>{
  checkAPI();
  const b=$("#startCrawl")||$("#startBtn")||document.querySelector("button");
  if(b)b.addEventListener("click",startCrawl);
});

async function analyzeKeywords(rows){
  const r=await fetch(`${API}/api/keywords/analyze`,{
    method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({rows})
  });
  return await r.json();
}
