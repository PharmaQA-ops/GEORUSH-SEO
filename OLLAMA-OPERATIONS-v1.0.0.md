# GEORUSH Ollama Operations v1.0.0

## Ownership model

Ollama is GEORUSH-owned during an active GEORUSH session.

### Startup

GEORUSH stops: - `ollama.exe` - `ollama app.exe`

It then starts a controlled local Ollama server.

### On demand

Ollama is started when required by: - Site Audit - Run Ollama AI -
3-Agent Deep Research

### Shutdown

GEORUSH stops the controlled Ollama runtime when the desktop application
exits/signs out.

## Default model

`qwen3:0.6b`

## Low-spec workstation

Recommended runtime: `OLLAMA_LLM_LIBRARY=cpu_avx2`

This is intended for the current 4 GB RAM / GT 710 test workstation. A
higher-spec marketing laptop can be configured separately after
validation.

## Diagnostics

Check: `GET /api/ollama/runtime/status`

Start: `POST /api/ollama/runtime/start`

Stop: `POST /api/ollama/runtime/stop`

## Common error

If GEORUSH reports a Windows `wsarecv` / HTTP 500 runner failure, do not
start multiple Ollama instances manually. Exit GEORUSH and relaunch it
so GEORUSH can recreate its owned runtime.

## Model preparation

If the model is missing, GEORUSH can pull the configured model
automatically. Initial model download requires Internet access.

## Privacy

Model inference is local to the workstation. Public web evidence
collected for research still leaves the machine because web research
requires Internet access.
