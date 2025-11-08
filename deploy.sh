# configure agent (writes a Dockerfile)
uv run agentcore configure --entrypoint weather_agent/agent.py

# deploy
uv run agentcore launch