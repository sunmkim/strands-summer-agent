resource "aws_bedrockagentcore_memory" "example" {
  name                  = "example_memory"
  event_expiry_duration = 30
}