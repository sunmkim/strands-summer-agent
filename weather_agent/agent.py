import os
from typing import Tuple, List, Dict
from dotenv import load_dotenv
from strands import Agent
from strands.models.litellm import LiteLLMModel
from MemoryHook import MemoryHook
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from memory_utils import create_memory_resource, create_memory_session
from tools import get_aqi, get_current_weather
from prompts import SYSTEM_PROMPT

load_dotenv()

# set ids for memory
ACTOR_ID = "user_1" # can be any unique identifier
SESSION_ID = "session_1" 
MEMORY_NAME = "weather_bot_memory"

# initialize runtime app
app = BedrockAgentCoreApp()

# create a liteLLM model for OpenAI's gpt-5-nano
model = LiteLLMModel(
    client_args={
        "api_key": os.getenv("OPENAI_API_KEY")
    },
    model_id="openai/gpt-5-nano"
)

@app.entrypoint
async def invoke_strands_agent(payload: Dict):
    """
    Invoke our strands agent with a payload (prompt)
    """

    # create memory manager and user session
    memory = create_memory_resource(
        memory_name=MEMORY_NAME
    )
    user_session = create_memory_session(
        actor_id=ACTOR_ID,
        session_id=SESSION_ID,
        memory_id=memory.id
    )

    # Create an agent with default settings
    agent = Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[get_aqi, get_current_weather],
        hooks=[MemoryHook(ACTOR_ID, SESSION_ID, user_session)],
    )
    
    usr_input = payload.get("prompt")
    print(f"User query: '{usr_input}'")

    tool_name = None

    # async streaming of the LLM response
    try: 
        async for event in agent.stream_async(usr_input):
            if (
                "current_tool_use" in event
                and event["current_tool_use"].get("name") != tool_name
            ):
                tool_name = event["current_tool_use"]["name"]
                yield f"*Using tool: {tool_name}* \n\n"

            if "data" in event:
                yield event["data"]
    except Exception as err:
        yield f"Error: {str(err)}"

if __name__ == "__main__":
    print("Agent running...")
    app.run()