# Triggered periodically to check aurora snapshots for replication canidates
resource "aws_lambda_function" "src_check_aurora_backups" {
  provider = aws.src

  description      = "Checks Aurora snapshots"
  filename         = "${path.module}/bin/src_check_aurora_backups.zip"
  function_name    = "rds_replication_src_check_aurora_backups"
  handler          = "src_check_aurora_backups.lambda_handler"
  memory_size      = 128
  role             = aws_iam_role.src_lambda_execution_role.arn
  runtime          = "python3.6"
  source_code_hash = filebase64sha256("${path.module}/bin/src_check_aurora_backups.zip")
  timeout          = 300

  environment {
    variables = {
      "LOGLEVEL"      = var.log_level
      "REGION"        = var.src_region
      "SNS_TOPIC_ARN" = aws_sns_topic.rds_snapshots.arn
      "PATTERN"       = var.pattern
      "BACKUP_LAST_N" = var.backup_last
    }
  }
}

resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.src_check_aurora_backups.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.src_check_for_aurora_backups.arn
}

resource "aws_lambda_function" "src_backup_event" {
  provider = aws.src

  description      = "Triggered on RDS backup events"
  filename         = "${path.module}/bin/src_backup_event.zip"
  function_name    = "rds_replication_src_backup_event"
  handler          = "src_backup_event.lambda_handler"
  memory_size      = 128
  role             = aws_iam_role.src_step_invocation_role.arn
  runtime          = "python3.6"
  source_code_hash = filebase64sha256("${path.module}/bin/src_backup_event.zip")
  timeout          = 300

  environment {
    variables = {
      "LOGLEVEL"          = var.log_level
      "PATTERN"           = var.pattern
      "REGION"            = var.src_region
      "STATE_MACHINE_ARN" = aws_sfn_state_machine.src_rds_snapshot_sharing.id
    }
  }
}

# Allow to be executed from SNS
resource "aws_lambda_permission" "sns" {
  statement_id  = "AllowExecutionFromSNS"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.src_backup_event.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.rds_snapshots.arn
}

# Lambda function for copying snapshot we need to make a copy of an existing
# Snapshot to be able to share it
resource "aws_lambda_function" "src_copy_snapshot" {
  provider = aws.src

  description      = "Makes copy of RDS snapshot"
  filename         = "${path.module}/bin/src_copy_snapshot.zip"
  function_name    = "rds_replication_src_copy_snapshot"
  handler          = "src_copy_snapshot.lambda_handler"
  memory_size      = 128
  role             = aws_iam_role.src_lambda_execution_role.arn
  runtime          = "python3.6"
  source_code_hash = filebase64sha256("${path.module}/bin/src_copy_snapshot.zip")
  timeout          = 300

  environment {
    variables = {
      "DST_REGION" = var.dst_region
      "LOGLEVEL"   = var.log_level
      "SRC_REGION" = var.src_region
    }
  }
}

# Lambda function for sharing snapshots with destination account
resource "aws_lambda_function" "src_share_snapshot" {
  provider = aws.src

  description      = "Shares RDS snapshot with different account"
  filename         = "${path.module}/bin/src_share_snapshot.zip"
  function_name    = "rds_replication_src_share_snapshot"
  handler          = "src_share_snapshot.lambda_handler"
  memory_size      = 128
  role             = aws_iam_role.src_lambda_execution_role.arn
  runtime          = "python3.6"
  source_code_hash = filebase64sha256("${path.module}/bin/src_share_snapshot.zip")
  timeout          = 300

  environment {
    variables = {
      "REGION"      = var.dst_region
      "DST_ACCOUNT" = var.dst_account_id
      "LOGLEVEL"    = var.log_level
    }
  }
}

# Lambda function for deleting the shared snapshot after it has been copied by
# The destination account
resource "aws_lambda_function" "src_delete_snapshot" {
  provider = aws.src

  description      = "Deletes RDS snapshot"
  filename         = "${path.module}/bin/src_delete_snapshot.zip"
  function_name    = "rds_replication_src_delete_snapshot"
  handler          = "src_delete_snapshot.lambda_handler"
  memory_size      = 128
  role             = aws_iam_role.src_lambda_cross_account_execution_role.arn
  runtime          = "python3.6"
  source_code_hash = filebase64sha256("${path.module}/bin/src_delete_snapshot.zip")
  timeout          = 300

  environment {
    variables = {
      "DST_ARN"    = aws_iam_role.dst_lambda_execution_role.arn
      "DST_REGION" = var.dst_region
      "LOGLEVEL"   = var.log_level
    }
  }
}

# Lambda function that copies the shared snapshot
# This function exists on the source account, but gets invoked at the destination
resource "aws_lambda_function" "dst_copy_snapshot" {
  provider = aws.src

  description      = "Copies the shared snapshot"
  filename         = "${path.module}/bin/dst_copy_snapshot.zip"
  function_name    = "rds_replication_dst_copy_snapshot"
  handler          = "dst_copy_snapshot.lambda_handler"
  memory_size      = 128
  role             = aws_iam_role.src_lambda_cross_account_execution_role.arn
  runtime          = "python3.6"
  source_code_hash = filebase64sha256("${path.module}/bin/dst_copy_snapshot.zip")
  timeout          = 300

  environment {
    variables = {
      "DST_ARN"     = aws_iam_role.dst_lambda_execution_role.arn
      "DST_REGION"  = var.dst_region
      "LOGLEVEL"    = var.log_level
      "SRC_ACCOUNT" = var.src_account_id
    }
  }
}

