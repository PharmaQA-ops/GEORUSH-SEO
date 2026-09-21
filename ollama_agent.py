"""GEORUSH local AI agent provider using Ollama.
Optimized for low-RAM local machines.
"""
import json
import os
import re
import httpx

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:0.6b")
TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "180"))

class OllamaAgentError(RuntimeError):
    pass

def status() -> dict:
    try:
        r = httpx.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=8)
        r.raise_for_status()
        data = r.json()
        models = [m.get("name") for m in data.get("models", [])]
        configured = OLLAMA_MODEL in models
        return {"provider":"Ollama","online":True,"configured_model":OLLAMA_MODEL,"model_available":configured,"models":models,"base_url":OLLAMA_BASE_URL,"local":True}
    except Exception as exc:
        return {"provider":"Ollama","online":False,"configured_model":OLLAMA_MODEL,"model_available":False,"models":[],"base_url":OLLAMA_BASE_URL,"local":True,"error":str(exc)}

def _extract_json(text: str):
    text=(text or "").strip()
    if text.startswith("```"):
        text=re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
        text=re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except Exception:
        pass
    m=re.search(r"\{.*\}", text, re.S)
    if m:
        try: return json.loads(m.group(0))
        except Exception: pass
    return {"raw":text}

def chat(system: str, evidence: dict, previous: dict | None = None) -> dict:
    evidence_text=json.dumps(evidence, ensure_ascii=False, default=str)[:6000]
    prompt=system+"\n\nEVIDENCE PACK (use only this evidence):\n"+evidence_text
    if previous:
        prompt+="\n\nPRIOR AGENT OUTPUTS:\n"+json.dumps(previous, ensure_ascii=False, default=str)[:3500]
    payload={
        "model":OLLAMA_MODEL,
        "messages":[
            {"role":"system","content":"You are a GEORUSH SEO research agent. Use only supplied evidence. Never invent rankings, traffic, backlinks, revenue or facts. Be concise. Return valid JSON only."},
            {"role":"user","content":prompt}
        ],
        "stream":False,
        "format":"json",
        "think":False,
        "keep_alive":"0",
        "options":{"temperature":0.2,"num_ctx":1024,"num_predict":320}
    }
    try:
        r=httpx.post(f"{OLLAMA_BASE_URL}/api/chat",json=payload,timeout=TIMEOUT)
        r.raise_for_status()
        data=r.json()
        text=((data.get("message") or {}).get("content") or "").strip()
        if not text: raise OllamaAgentError("Ollama returned an empty response")
        return _extract_json(text)
    except httpx.TimeoutException as exc:
        raise OllamaAgentError(f"Ollama inference timed out after {TIMEOUT:.0f}s. The local model is reachable but the prompt/model workload was too slow.") from exc
    except httpx.HTTPStatusError as exc:
        raise OllamaAgentError(f"Ollama HTTP {exc.response.status_code}: {exc.response.text[:500]}") from exc
    except OllamaAgentError:
        raise
    except Exception as exc:
        raise OllamaAgentError(str(exc)) from exc

def run_agent(role: str, evidence: dict, previous: dict | None = None) -> dict:
    return chat(role,evidence,previous)
