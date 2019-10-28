# Roles granting source account access to destination.
resource "aws_iam_role" "dst_lambda_execution_role" {
  provider = aws.dst

  name               = "rds_replication_dst_lambda_execution_role"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "${var.src_account_id}"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

}

resource "aws_iam_role_policy" "dst_lambda_execution_policy" {
  provider = aws.dst

  name   = "rds_replication_dst_lambda_execution_policy"
  role   = aws_iam_role.dst_lambda_execution_role.id
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

# IAM rule for the cleanup lambda function
resource "aws_iam_role" "dst_delete_old_snapshots_role" {
  provider = aws.dst

  name               = "rds_replication_dst_delete_old_snapshots_role"
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

resource "aws_iam_role_policy" "dst_delete_old_snapshots_policy" {
  provider = aws.dst

  name   = "rds_replication_dst_delete_old_snapshots_policy"
  role   = aws_iam_role.dst_delete_old_snapshots_role.id
  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "rds:DeleteDBSnapshot",
        "rds:DescribeDBInstances",
        "rds:DescribeDBSnapshots",
        "rds:DescribeDBSnapshotAttributes",
        "rds:DescribeDBClusters",
        "rds:DeleteDBClusterSnapshot",
        "rds:DescribeDBClusterInstances",
        "rds:DescribeDBClusterSnapshots",
        "rds:ModifyDBClusterSnapshotAttribute",
        "rds:DescribeDBClusterSnapshotAttributes"
      ],
      "Resource": "*"
    }
  ]
}
EOF

}

resource "aws_iam_role_policy_attachment" "dst_delete_old_snapshots_basic_execution_policy" {
  provider = aws.dst

  role       = aws_iam_role.dst_delete_old_snapshots_role.id
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

