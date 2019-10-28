# rds_replication

## Summary

This project sets up RDS and Aurora snapshot replication to a different account
(in case of loss of account) and region (in case of nuclear war).

## How it works

For RDS snapshots: we subscribe to RDS snapshot events via SNS. Every event
triggers src_backup_event. If it is a snapshot completed event, it will start
a step function. This step function will first copy the snapshot to the target
region within the same account, then to the target account, and finally delete
the additional copy it created in the source account.

For Aurora snapshots: Aurora snapshots do not have events so we check for them
on a regular basis. If we find one, we emit an event to SNS, which is picket up
by src_backup_event.

## Created resources

### Source Account

* Cloudwatch event to delete old snapshots
* IAM roles & policies (see permissions)
* Stepfunction and multiple Lambda functions
* SNS topic 'rds_replication'

### Destination Account

* Cloudwatch event to delete old snapshots
* IAM roles & policies (see permissions)
* Lambda function to delete old snapshots

## Granted permissions

The module can read and delete all DB snapshots in both accounts. Both accounts
only have access to their own snapshots. The source account can trigger a lambda
function in the destination account.

Please check src_iam.tf and dst_iam.tf for details.

## Variables

* backup_last: how many snapshots should be replicated from src to dst
* dst_account_id: destination account id
* dst_region: destination region
* log_level: python logging log levels: DEBUG|INFO|WARNING|ERROR
* pattern: regex which snapshots should be replicated
* retention: how many days to keep backups for
* schedule_expression: how often to clean up backups
* src_account_id: source account id
* src_region: source region