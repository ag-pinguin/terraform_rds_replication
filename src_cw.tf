# Event to trigger scanning Aurora backups
resource "aws_cloudwatch_event_rule" "src_check_for_aurora_backups" {
  provider = aws.src

  name                = "rds-replication-trigger-src-check-aurora-backups"
  description         = "Triggers Lambda rds_replication_src_check_aurora_backups"
  schedule_expression = var.schedule_expression
}

resource "aws_cloudwatch_event_target" "src_check_for_aurora_backups" {
  rule = aws_cloudwatch_event_rule.src_check_for_aurora_backups.name
  arn  = aws_lambda_function.src_check_aurora_backups.arn
}

