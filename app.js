const API="http://127.0.0.1:8000";
async function runCrawl(){
  const site=document.getElementById("site").value.trim();
  if(!site){alert("Enter a website URL");return}
  setText("status","CRAWLING");
  setText("msg","Crawling...");
  try{
    const r=await fetch(API+"/api/crawl",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({url:site,max_pages:50})});
    const d=await r.json();
    if(!r.ok) throw new Error(d.detail||"Audit failed");
    setText("score",d.health);
    setText("pages",d.pages);
    setText("issues",Object.values(d.issues).reduce((a,b)=>a+b,0));
    setText("status","COMPLETE");
    setText("msg",`Audit ${d.crawl_id} complete`);
    document.getElementById("rows").innerHTML=d.results.map(p=>`<tr>
      <td class="url">${esc(p.url)}</td><td>${p.status||"ERR"}</td>
      <td>${esc(p.title||"—")}</td><td>${p.word_count}</td><td>${p.load_ms} ms</td>
      <td>${p.issues.length?p.issues.map(x=>`<span class="tag">${x}</span>`).join(" "):"OK"}</td>
    </tr>`).join("");
  }catch(e){setText("status","ERROR");setText("msg",e.message)}
}
function setText(id,v){document.getElementById(id).textContent=v}
function esc(s){return String(s).replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]))}
