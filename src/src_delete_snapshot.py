'''
Copyright 2019  Pinguin AG, Mattis Haase

Licensed under the Apache License, Version 2.0 (the "License").

Inspired by https://github.com/awslabs/rds-snapshot-tool
'''

# src_copy_snapshot.py
# This lambda function deletes the snapshot copy that was created before sharing

import os
import logging

import boto3

from common import *

DST_ARN    = os.getenv('DST_ARN').strip()
DST_REGION = os.getenv('DST_REGION').strip()
LOGLEVEL   = os.getenv('LOGLEVEL', 'ERROR').strip()

logger = logging.getLogger()
logger.setLevel(LOGLEVEL.upper())

RDS = boto3.client('rds', region_name=DST_REGION)

STS = boto3.client('sts')
awsaccount = STS.assume_role(
        RoleArn         = DST_ARN,
        RoleSessionName ='awsaccount_session'
)

ACCESS_KEY    = awsaccount['Credentials']['AccessKeyId']
SECRET_KEY    = awsaccount['Credentials']['SecretAccessKey']
SESSION_TOKEN = awsaccount['Credentials']['SessionToken']

DST_RDS = boto3.client('rds', region_name=DST_REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY, aws_session_token=SESSION_TOKEN)

def lambda_handler(event, context):
    """Main method
    
    Arguments:
        event {dict} -- Lambda event object
        context {obj} -- Lambda context object
    """
    cluster = False
    if 'cluster' in event['SourceType']:
        cluster = True
    # We can only delete the shared snapshot if the destination has finished it's copy
    # First we check if it exists at all, and fail if it does not
    if cluster:
        response = DST_RDS.describe_db_cluster_snapshots(
            DBClusterSnapshotIdentifier = event['dst_snapshot_identifier']
        )
        snapshots = response['DBClusterSnapshots']
    else:
        response = DST_RDS.describe_db_snapshots(
            DBSnapshotIdentifier = event['dst_snapshot_identifier']
        )
        snapshots = response['DBSnapshots']
    logger.debug(response)
    if not snapshots:
        logger.error('Could not find DB snapshot {}'.format(event['local_copy_snapshot_identifier']))
        raise SnapshotNotFoundException
    for snapshot in snapshots:
        if not snapshot['Status'] == 'available':
            log_message = 'Snapshot {} still creating, retrying..'.format(snapshot['DBSnapshotIdentifier'])
            logger.info(log_message)
            raise SnapshotSharingException(log_message)
    # Generating name for our local snapshot copy
    logger.info('Deleting snapshot {}'.format(event['local_copy_snapshot_identifier']))
    try:
        if cluster:
            response = RDS.delete_db_cluster_snapshot(
                DBClusterSnapshotIdentifier = event['local_copy_snapshot_identifier']
            )
        else:
            response = RDS.delete_db_snapshot(
                DBSnapshotIdentifier = event['local_copy_snapshot_identifier']
            )
        logger.info('Response: {}'.format(response))
    except Exception as e:
        log_message = 'Exception while trying to delete: {}'.format(e)
        logger.error(log_message)
        raise SnapshotSharingException(log_message)
