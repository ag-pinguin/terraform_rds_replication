# Step function for RDS snapshot sharing
# Steps are:
# 1. source: make a snapshot copy "snapshot1"
# 2. source: share snapshot1
# 3. destination: copy snapshot1
# 4. source: delete snapshot1
#
# Result: snapshot has been copied to destination account

resource "aws_sfn_state_machine" "src_rds_snapshot_sharing" {
  provider = aws.src

  name     = "rds_snapshot_sharing"
  role_arn = aws_iam_role.src_state_execution_role.arn

  definition = <<EOF
{
  "Comment": "Shares RDS snapshots with a different account",
  "StartAt": "SrcCopySnapshot",
  "States": {
    "SrcCopySnapshot": {
      "Type": "Task",
      "Resource": "${aws_lambda_function.src_copy_snapshot.arn}",
      "Retry": [
        {
          "ErrorEquals": [ "SnapshotNotFoundException" ],
          "IntervalSeconds": 300,
          "MaxAttempts": 1,
          "BackoffRate": 1
        },
        {
          "ErrorEquals": [ "SnapshotSharingException" ],
          "IntervalSeconds": 300,
          "MaxAttempts": 10,
          "BackoffRate": 1
        },
        {
          "ErrorEquals": [ "States.ALL" ],
          "IntervalSeconds": 30,
          "MaxAttempts": 20,
          "BackoffRate": 1
        }
      ],
      "Next": "SrcShareSnapshot"
    },
    "SrcShareSnapshot": {
      "Type": "Task",
      "Resource": "${aws_lambda_function.src_share_snapshot.arn}",
      "Retry": [
        {
          "ErrorEquals": [ "SnapshotNotFoundException" ],
          "IntervalSeconds": 300,
          "MaxAttempts": 1,
          "BackoffRate": 1
        },
        {
          "ErrorEquals": [ "SnapshotSharingException" ],
          "IntervalSeconds": 300,
          "MaxAttempts": 10,
          "BackoffRate": 1
        },
        {
          "ErrorEquals": [ "States.ALL" ],
          "IntervalSeconds": 30,
          "MaxAttempts": 20,
          "BackoffRate": 1
        }
      ],
      "Next": "DstCopySnapshot"
    },
    "DstCopySnapshot": {
      "Type": "Task",
      "Resource": "${aws_lambda_function.dst_copy_snapshot.arn}",
      "Retry": [
        {
          "ErrorEquals": [ "SnapshotNotFoundException" ],
          "IntervalSeconds": 300,
          "MaxAttempts": 1,
          "BackoffRate": 1
        },
        {
          "ErrorEquals": [ "SnapshotSharingException" ],
          "IntervalSeconds": 300,
          "MaxAttempts": 3,
          "BackoffRate": 1
        },
        {
          "ErrorEquals": [ "States.ALL" ],
          "IntervalSeconds": 30,
          "MaxAttempts": 20,
          "BackoffRate": 1
        }
      ],
      "Next": "SrcDeleteSnapshot"
    },
    "SrcDeleteSnapshot": {
      "Type": "Task",
      "Resource": "${aws_lambda_function.src_delete_snapshot.arn}",
      "Retry": [
        {
          "ErrorEquals": [ "SnapshotNotFoundException" ],
          "IntervalSeconds": 300,
          "MaxAttempts": 1,
          "BackoffRate": 1
        },
        {
          "ErrorEquals": [ "SnapshotSharingException" ],
          "IntervalSeconds": 300,
          "MaxAttempts": 3,
          "BackoffRate": 1
        },
        {
          "ErrorEquals": [ "States.ALL" ],
          "IntervalSeconds": 30,
          "MaxAttempts": 20,
          "BackoffRate": 1
        }
      ],
      "End": true
    }
  }
}
EOF

}

