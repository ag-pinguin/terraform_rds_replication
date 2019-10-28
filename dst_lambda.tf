# Triggered periodically to clean up old snapshots
resource "aws_lambda_function" "dst_delete_old_snapshots" {
  provider = aws.dst

  description      = "Delete old snapshots"
  filename         = "${path.module}/bin/dst_delete_old_snapshots.zip"
  function_name    = "rds_replication_dst_delete_old_snapshots"
  handler          = "dst_delete_old_snapshots.lambda_handler"
  memory_size      = 128
  role             = aws_iam_role.dst_delete_old_snapshots_role.arn
  runtime          = "python3.6"
  source_code_hash = filebase64sha256("${path.module}/bin/dst_delete_old_snapshots.zip")
  timeout          = 300

  environment {
    variables = {
      "LOGLEVEL"   = var.log_level
      "DST_REGION" = var.dst_region
      "RETENTION"  = var.retention
    }
  }
}

resource "aws_lambda_permission" "dst_allow_cloudwatch" {
  provider = aws.dst

  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.dst_delete_old_snapshots.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.dst_delete_old_snapshots.arn
}

