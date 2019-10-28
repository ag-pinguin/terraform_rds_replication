# Event to trigger deleting old snaphots
resource "aws_cloudwatch_event_rule" "dst_delete_old_snapshots" {
  provider = aws.dst

  name                = "rds-replication-trigger-dst-delete-old-snapshots"
  description         = "Triggers Lambda rds_replication_dst_delete_old_snapshots"
  schedule_expression = var.schedule_expression
}

resource "aws_cloudwatch_event_target" "dst_delete_old_snapshots" {
  provider = aws.dst

  rule = aws_cloudwatch_event_rule.dst_delete_old_snapshots.name
  arn  = aws_lambda_function.dst_delete_old_snapshots.arn
}

