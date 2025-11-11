provider "aws" {
  region = "us-east-1"
}

# Agentcore memory resource
resource "aws_bedrockagentcore_memory" "weather_bot_memory" {
  name                  = "weather_bot_memory"
  event_expiry_duration = 7
}