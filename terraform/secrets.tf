resource "aws_secretsmanager_secret" "slackbot_credentials" {
  name                    = "${var.environment}-slackbot-credentials"
  description             = "${var.environment} slackbot webhook URL"
  recovery_window_in_days = "7"
}

resource "aws_secretsmanager_secret_version" "slackbot_credentials" {
  secret_id = aws_secretsmanager_secret.slackbot_credentials.id
  secret_string = jsonencode(
    {
      webhook_url = ""
    }
  )
}