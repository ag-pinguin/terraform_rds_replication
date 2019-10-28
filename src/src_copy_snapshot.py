'''
Copyright 2019  Pinguin AG, Mattis Haase

Licensed under the Apache License, Version 2.0 (the "License").

Inspired by https://github.com/awslabs/rds-snapshot-tool
'''

# src_copy_snapshot.py
# This lambda function creates a manual copy of a snapshot, for later sharing

import os
import logging

import boto3

from common import *

LOGLEVEL = os.getenv('LOGLEVEL', 'ERROR').strip()
DST_REGION   = os.getenv('DST_REGION').strip()
SRC_REGION   = os.getenv('SRC_REGION').strip()

logger = logging.getLogger()
logger.setLevel(LOGLEVEL.upper())

SRC_RDS = boto3.client('rds', region_name=SRC_REGION)
DST_RDS = boto3.client('rds', region_name=DST_REGION)

def lambda_handler(event, context):
    """Main method
    
    Arguments:
        event {dict} -- Lambda event object
        context {obj} -- Lambda context object
    """
    cluster = False
    if 'cluster' in event['SourceType']:
        cluster = True
    logger.debug('event: {}'.format(event))

    # Sanity check: does the snapshot actually exist? If not we want to fail fast
    if cluster:
        response = SRC_RDS.describe_db_cluster_snapshots(
            DBClusterSnapshotIdentifier = event['SourceIdentifier']
        )
        snapshots = response['DBClusterSnapshots']
    else:
        response = SRC_RDS.describe_db_snapshots(
            DBSnapshotIdentifier = event['SourceIdentifier']
        )
        snapshots = response['DBSnapshots']
    logger.debug(response)
    if not snapshots:
        logger.error('Could not find DB snapshot {}'.format(event['SourceIdentifier']))
        raise SnapshotNotFoundException

    # Generating name for our local snapshot copy
    local_copy_name = 'rds-replication-{}'.format(event['SourceIdentifier']).replace(':', '-')
    logger.info('Copying snapshot {} locally to {}'.format(event['SourceIdentifier'], local_copy_name))
    try:
        if cluster:
            response = DST_RDS.copy_db_cluster_snapshot(
                SourceDBClusterSnapshotIdentifier = event['SourceArn'],
                TargetDBClusterSnapshotIdentifier = local_copy_name,
                SourceRegion                      = SRC_REGION
            )
        else:
            response = DST_RDS.copy_db_snapshot(
                SourceDBSnapshotIdentifier = event['SourceArn'],
                TargetDBSnapshotIdentifier = local_copy_name,
                SourceRegion               = SRC_REGION
            )
        logger.info('Response: {}'.format(response))
    except Exception as e:
        log_message = 'Copy pending: {}'.format(event['SourceIdentifier'])
        logger.error(log_message)
        raise SnapshotSharingException(log_message)
    event['local_copy_snapshot_identifier'] = local_copy_name
    logger.debug('Returning: {}'.format(event))
    return event
