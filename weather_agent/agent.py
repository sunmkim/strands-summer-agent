import os
from strands import Agent
from strands.models.litellm import LiteLLMModel
from tools import get_aqi, get_current_weather

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
    system_prompt=system_prompt,
    tools=[get_aqi, get_current_weather]
)

# Ask the agent a question
agent("I am in Doha, Qatar. Should I go jogging outside?")