# we will use agentcore starter toolkit to deploy our agent

# configure and deplpoy
uv run agentcore configure -e agent.py
uv run agentcore launch --env OPENWEATHER_API_KEY='api-key-here' --env OPENAI_API_KEY='api-key-here'
uv run agentcore status

# test deployment
uv run agentcore invoke '{"prompt": "Hello. What do you do?"}'