# SNS for source account
# RDS creation events are published into this topic
resource "aws_sns_topic" "rds_snapshots" {
  provider = aws.src
  name     = "rds_snapshots"
}

resource "aws_db_event_subscription" "snapshots" {
  provider = aws.src

  name      = "rds-snapshots"
  sns_topic = aws_sns_topic.rds_snapshots.arn
}

# Every event triggers src_backup_event lambda.
resource "aws_sns_topic_subscription" "rds_snapshots_lambda_subscription" {
  endpoint  = aws_lambda_function.src_backup_event.arn
  protocol  = "lambda"
  topic_arn = aws_sns_topic.rds_snapshots.arn
}

