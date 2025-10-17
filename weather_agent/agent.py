import os
from typing import Tuple, List, Dict
from strands import Agent
from strands.models.litellm import LiteLLMModel
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from tools import get_aqi, get_current_weather
from prompts import SYSTEM_PROMPT


# initialize runtime app
app = BedrockAgentCoreApp()

# create a liteLLM model for OpenAI's gpt-5-nano
model = LiteLLMModel(
    client_args={
        "api_key": os.getenv("OPENAI_API_KEY")
    },
    model_id="openai/gpt-5-nano"
)

# Create an agent with default settings
agent = Agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=[get_aqi, get_current_weather]
)

@app.entrypoint
def invoke_strands_agent(payload: Dict):
    """
    Invoke our strands agent with a payload (prompt)
    """
    usr_input = payload.get("prompt")
    print(f"User query: '{usr_input}'")

    # Prompt agent
    resp = agent(usr_input)
    print('Response: ', resp)
    return resp.message

if __name__ == "__main__":
    app.run()