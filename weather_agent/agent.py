import os
from typing import Tuple, List, Dict
from strands import Agent
from strands.models.litellm import LiteLLMModel
from dotenv import load_dotenv
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from tools import get_aqi, get_current_weather
from prompts import SYSTEM_PROMPT

load_dotenv()

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

    # Create an agent with default settings
    agent = Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[get_aqi, get_current_weather]
    )
    
    usr_input = payload.get("prompt")
    print(f"User query: '{usr_input}'")

    tool_name = None
    # session_id = context.session_id

    try: 
        async for event in agent.stream_async(usr_input):
            print(event)
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