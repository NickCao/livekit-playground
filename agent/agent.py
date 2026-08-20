import logging
import os

from dotenv import load_dotenv

from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    RunContext,
    cli,
    room_io,
)
from livekit.agents.llm import function_tool
from livekit.plugins import openai

logger = logging.getLogger("vllm-omni-agent")

load_dotenv()

# vLLM-Omni is expected to expose an OpenAI Realtime API-compatible
# /v1/realtime endpoint (see https://github.com/vllm-project/vllm-omni).
# Pointing livekit-plugins-openai's RealtimeModel at it is the only
# integration point needed - no custom plugin required.
VLLM_OMNI_BASE_URL = os.environ.get("VLLM_OMNI_BASE_URL", "http://vllm-omni:8000/v1")
VLLM_OMNI_MODEL = os.environ.get("VLLM_OMNI_MODEL", "")
VLLM_OMNI_API_KEY = os.environ.get("VLLM_OMNI_API_KEY", "not-needed")


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="You are a helpful voice assistant speaking through vLLM-Omni. "
            "Keep responses concise and conversational, without emojis, asterisks, "
            "or other characters that don't make sense when spoken aloud. "
            "Use the lookup_weather tool whenever the user asks about weather, so we "
            "can confirm tool calling works end to end.",
        )

    async def on_enter(self) -> None:
        self.session.generate_reply(instructions="greet the user and introduce yourself")

    # all functions annotated with @function_tool will be passed to the LLM
    @function_tool
    async def lookup_weather(
        self, context: RunContext, location: str, latitude: str, longitude: str
    ) -> str:
        """Called when the user asks for weather related information.
        Ensure the user's location (city or region) is provided.
        When given a location, please estimate the latitude and longitude of the location and
        do not ask the user for them.

        Args:
            location: The location they are asking for
            latitude: The latitude of the location, do not ask user for it
            longitude: The longitude of the location, do not ask user for it
        """
        logger.info(f"Looking up weather for {location}")
        return "sunny with a temperature of 70 degrees."


server = AgentServer()


@server.rtc_session()
async def entrypoint(ctx: JobContext) -> None:
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    session = AgentSession(
        llm=openai.realtime.RealtimeModel(
            base_url=VLLM_OMNI_BASE_URL,
            api_key=VLLM_OMNI_API_KEY,
            model=VLLM_OMNI_MODEL,
        ),
    )

    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_options=room_io.RoomOptions(),
    )


if __name__ == "__main__":
    cli.run_app(server)
