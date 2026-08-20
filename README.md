# livekit-playground

An all-in-one [LiveKit Agents](https://github.com/livekit/agents) playground for
testing [vLLM-Omni](https://github.com/vllm-project/vllm-omni) as a realtime
speech-to-speech inference backend.

vLLM-Omni exposes an OpenAI Realtime API-compatible `/v1/realtime` endpoint, so
the only integration point needed is `livekit-plugins-openai`'s
`RealtimeModel`, pointed at your vLLM-Omni server via `base_url` - no custom
plugin code required. The agent (`agent/agent.py`) is a trimmed-down version of
[livekit/agents' own realtime examples](https://github.com/livekit/agents/blob/main/examples/voice_agents/grok/grok_voice_agent_api.py),
and includes a `lookup_weather` [function tool](https://github.com/livekit/agents/blob/main/examples/voice_agents/basic_agent.py)
so you can confirm tool calling works through vLLM-Omni.

vLLM-Omni's `/v1/realtime` endpoint doesn't support server-side VAD/turn
detection, so the model's own `turn_detection` is left unset (which lets
LiveKit Agents disable it) and a local Silero VAD drives turn-taking instead,
via `turn_handling=TurnHandlingOptions(turn_detection="vad")`.

## Architecture

- `livekit-server` - self-hosted LiveKit server (dev keys, local only).
- `agent` - a LiveKit Agents worker that joins rooms and talks to vLLM-Omni
  over `/v1/realtime`.
- `frontend` - [livekit-examples/agent-starter-react](https://github.com/livekit-examples/agent-starter-react),
  the official LiveKit Agents web frontend, built from source and run in dev
  mode (no frontend code lives in this repo).
- **vLLM-Omni itself is *not* part of this stack.** It needs its own GPU host,
  so run it separately (see below) and point this stack at it.

## 1. Start vLLM-Omni externally

On a GPU host, following the current instructions for your chosen model at
https://github.com/vllm-project/vllm-omni (the project is under active
development, so check there for the exact flags needed to expose
`/v1/realtime` for the model you pick), e.g.:

```bash
vllm-omni serve <your-omni-model> --omni --host 0.0.0.0 --port 8000
```

Note the host/port you served it on - you'll need it below.

## 2. Configure this stack

```bash
cp .env.example .env
```

Edit `.env`:

```bash
VLLM_OMNI_BASE_URL=http://<gpu-host>:8000/v1
VLLM_OMNI_MODEL=<your-omni-model>
```

## 3. Run

```bash
docker compose up --build
```

This starts a local LiveKit server on `ws://localhost:7880` (dev keys
`devkey` / `devsecret1234567890devsecret12345`), the agent worker, and the frontend on
http://localhost:3000.

> `livekit-server/config.yaml` sets `rtc.node_ip: 127.0.0.1`, which assumes
> your browser runs on the same machine as `docker compose`. If you're
> connecting from another machine, change it to that host's LAN/public IP
> or you'll see "could not establish pc connection" in the browser.

## 4. Talk to it

Open http://localhost:3000, click connect, and start talking. Ask it
something like "what's the weather in Boston?" to confirm the
`lookup_weather` tool call round-trips through vLLM-Omni correctly.

## Files

```
docker-compose.yml       # livekit-server + agent + frontend
livekit-server/config.yaml
agent/agent.py           # RealtimeModel(base_url=vLLM-Omni) + one function_tool
agent/Dockerfile
agent/pyproject.toml
frontend/Dockerfile      # builds livekit-examples/agent-starter-react from source
.env.example
```
