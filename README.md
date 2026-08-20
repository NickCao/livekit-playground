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

All three services run with `network_mode: host` (Linux only) so
`livekit-server` can bind its UDP media port range directly - Docker's
per-port NAT for a 100+ port UDP range is what causes WebRTC's "ICE failed"
even when the signaling WebSocket connects fine.

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

## Troubleshooting: agent goes silent after a tool call

Tool-call continuation is driven entirely by the framework, the same way for
every realtime backend (OpenAI, Grok, Gemini, ...): once `lookup_weather`
returns, `livekit-agents` sends the result back as a `function_call_output`
item, possibly updates `tool_choice`/`tools` on the session, then requests a
new response. `agent/agent.py` has no special-cased logic here, so if the
agent stops responding after a tool call, vLLM-Omni's `/v1/realtime` isn't
completing that continuation correctly.

Set `LK_OPENAI_DEBUG=1` in `.env` (or the `agent` environment) and re-run
`docker compose up --build` to log every raw `/v1/realtime` event and see
exactly where it stalls - e.g. whether vLLM-Omni ever acknowledges the
`function_call_output` item, or emits `response.created`/`response.done` for
the follow-up. Since full-duplex tool calling is part of vLLM-Omni's
experimental realtime runtime, a stall here likely needs to be reported/
tracked upstream at https://github.com/vllm-project/vllm-omni rather than
fixed in this playground.

## Troubleshooting: can't interrupt the agent

Barge-in works like this: local Silero VAD (`turn_handling=TurnHandlingOptions(
interruption={"mode": "vad"})`) detects you start speaking while the agent is
talking, and the framework then sends `conversation.item.truncate` and
`response.cancel` over `/v1/realtime` to stop the in-flight generation. If
those aren't handled correctly server-side, the agent's audio may keep
playing or the session may get stuck afterwards - the same class of problem
as the tool-call stall above. Use `LK_OPENAI_DEBUG=1` the same way to check
whether vLLM-Omni acknowledges `response.cancel` when you talk over it.

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
