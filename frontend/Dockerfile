# syntax=docker/dockerfile:1
#
# Runs livekit-examples/agent-starter-react (the official LiveKit Agents
# frontend starter) straight from source - no frontend code lives in this
# repo. `next dev` is used deliberately: the starter's token route refuses
# to run outside development mode as a safety guard, which is fine here
# since this is a local-only playground.
FROM node:24-slim

RUN apt-get update && apt-get install -y git ca-certificates && rm -rf /var/lib/apt/lists/*
RUN corepack enable

ARG AGENT_STARTER_REACT_REF=main
WORKDIR /app
RUN git clone --depth 1 --branch ${AGENT_STARTER_REACT_REF} \
    https://github.com/livekit-examples/agent-starter-react.git .

RUN pnpm install --frozen-lockfile

EXPOSE 3000
CMD ["pnpm", "exec", "next", "dev", "--turbopack", "-H", "0.0.0.0", "-p", "3000"]
