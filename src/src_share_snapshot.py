'''
Copyright 2019  Pinguin AG, Mattis Haase

Licensed under the Apache License, Version 2.0 (the "License").

Inspired by https://github.com/awslabs/rds-snapshot-tool
'''

# src_share_snapshot.py
# shares the snapshot created in the previous step

import os
import logging

import boto3

from common import *

LOGLEVEL    = os.getenv('LOGLEVEL', 'ERROR').strip()
REGION      = os.getenv('REGION').strip()
DST_ACCOUNT = os.getenv('DST_ACCOUNT').strip()

logger = logging.getLogger()
logger.setLevel(LOGLEVEL.upper())

RDS = boto3.client('rds', region_name=REGION)

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

    # Sanity check: does the snapshot actually exist?
    if cluster:
        response = RDS.describe_db_cluster_snapshots(
            DBClusterSnapshotIdentifier = event['local_copy_snapshot_identifier']
        )
        snapshots = response['DBClusterSnapshots']
    else:
        response = RDS.describe_db_snapshots(
            DBSnapshotIdentifier = event['local_copy_snapshot_identifier']
        )
        snapshots = response['DBSnapshots']
    logger.debug(response)
    if not snapshots:
        logger.error('Could not find DB snapshot {}'.format(event['SourceIdentifier']))
        raise SnapshotNotFoundException

    # To share a snapshot, one needs to modify the DB snapshot with the
    try:
        if cluster:
            response = RDS.modify_db_cluster_snapshot_attribute(
                DBClusterSnapshotIdentifier = event['local_copy_snapshot_identifier'],
                AttributeName               = 'restore',
                ValuesToAdd                 = [ DST_ACCOUNT ]
            )
        else:
            response = RDS.modify_db_snapshot_attribute(
                DBSnapshotIdentifier = event['local_copy_snapshot_identifier'],
                AttributeName        = 'restore',
                ValuesToAdd          = [ DST_ACCOUNT ]
            )
    except Exception as e:
        logger.error('Exception sharing {}: {}'.format(event['local_copy_snapshot_identifier'], e))
        raise SnapshotSharingException('Could not share Snapshot')
    return event
