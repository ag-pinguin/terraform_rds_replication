# IAM roles for source account

# IAM role for lambda
resource "aws_iam_role" "src_lambda_execution_role" {
  provider = aws.src

  name               = "rds_replication_src_lambda_execution_role"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

}

resource "aws_iam_role_policy" "src_lambda_execution_policy" {
  name   = "rds_replication_src_lambda_execution_policy"
  role   = aws_iam_role.src_lambda_execution_role.id
  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "rds:CopyDBSnapshot",
        "rds:DeleteDBSnapshot",
        "rds:DescribeDBInstances",
        "rds:DescribeDBSnapshots",
        "rds:ModifyDBSnapshotAttribute",
        "rds:DescribeDBSnapshotAttributes",
        "rds:DescribeDBClusters",
        "rds:CopyDBClusterSnapshot",
        "rds:DeleteDBClusterSnapshot",
        "rds:DescribeDBClusterInstances",
        "rds:DescribeDBClusterSnapshots",
        "rds:ModifyDBClusterSnapshotAttribute",
        "rds:DescribeDBClusterSnapshotAttributes",
        "rds:ListTagsForResource",
        "rds:AddTagsToResource"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "SNS:publish"
      ],
      "Resource": "${aws_sns_topic.rds_snapshots.arn}"
    }
  ]
}
EOF

}

resource "aws_iam_role_policy_attachment" "src_lambda_basic_execution_policy" {
  provider = aws.src

  role       = aws_iam_role.src_lambda_execution_role.id
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# IAM role for step function
resource "aws_iam_role" "src_state_execution_role" {
  provider = aws.src

  name               = "rds_replication_src_state_execution_role"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "states.${var.src_region}.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

}

resource "aws_iam_role_policy" "src_state_execution_policy" {
  name   = "rds_replication_src_state_execution_policy"
  role   = aws_iam_role.src_state_execution_role.id
  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Resource": [
        "${aws_lambda_function.src_copy_snapshot.arn}",
        "${aws_lambda_function.src_share_snapshot.arn}",
        "${aws_lambda_function.src_delete_snapshot.arn}",
        "${aws_lambda_function.dst_copy_snapshot.arn}"
      ]
    }
  ]
}
EOF

}

# IAM role for step invocation
resource "aws_iam_role" "src_step_invocation_role" {
  provider = aws.src

  name               = "rds_replication_src_step_invocation_role"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

}

resource "aws_iam_role_policy" "src_step_invocation_policy" {
  name   = "rds_replication_src_step_invocation_policy"
  role   = aws_iam_role.src_step_invocation_role.id
  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "states:StartExecution"
      ],
      "Resource": [
        "${aws_sfn_state_machine.src_rds_snapshot_sharing.id}"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "rds:DescribeDBInstances",
        "rds:DescribeDBSnapshots",
        "rds:DescribeDBSnapshotAttributes",
        "rds:DescribeDBClusters",
        "rds:DescribeDBClusterInstances",
        "rds:DescribeDBClusterSnapshots",
        "rds:DescribeDBClusterSnapshotAttributes"
      ],
      "Resource": "*"
    }
  ]
}
EOF

}

resource "aws_iam_role_policy_attachment" "src_lambda_state_basic_execution_policy" {
  provider = aws.src

  role       = aws_iam_role.src_step_invocation_role.id
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# This together with dst_lambda_execution_role allows the lambda to be
# Invoked on another account
resource "aws_iam_role" "src_lambda_cross_account_execution_role" {
  provider = aws.src

  name               = "rds_replication_src_lambda_cross_account_execution_role"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

}

resource "aws_iam_role_policy" "src_lambda_cross_account_execution_policy" {
  name   = "rds_replication_src_lambda_cross_account_execution_policy"
  role   = aws_iam_role.src_lambda_cross_account_execution_role.id
  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
        "Effect": "Allow",
        "Action": "sts:AssumeRole",
        "Resource": "${aws_iam_role.dst_lambda_execution_role.arn}"
    },
    {
      "Effect": "Allow",
      "Action": [
        "rds:CopyDBSnapshot",
        "rds:DeleteDBSnapshot",
        "rds:DescribeDBInstances",
        "rds:DescribeDBSnapshots",
        "rds:ModifyDBSnapshotAttribute",
        "rds:DescribeDBSnapshotAttributes",
        "rds:CopyDBClusterSnapshot",
        "rds:DeleteDBClusterSnapshot",
        "rds:DescribeDBClusterInstances",
        "rds:DescribeDBClusterSnapshots",
        "rds:ModifyDBClusterSnapshotAttribute",
        "rds:DescribeDBClusterSnapshotAttributes",
        "rds:ListTagsForResource"
      ],
      "Resource": "*"
    }
  ]
}
EOF

}

resource "aws_iam_role_policy_attachment" "src_lambda_cross_account_basic_execution_policy" {
  provider = aws.src

  role       = aws_iam_role.src_lambda_cross_account_execution_role.id
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

