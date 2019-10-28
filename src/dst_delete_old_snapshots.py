'''
Copyright 2019  Pinguin AG, Mattis Haase

Licensed under the Apache License, Version 2.0 (the "License").

Inspired by https://github.com/awslabs/rds-snapshot-tool
'''

# dst_delete_old_snapshots
# This lambda function triggers daily to delete old snapshots.
# It:
# 1. describe-db-snapshots and describe-db-cluster-snapshots
# 2. for every db instance or cluster snapshot that begins with 'replication':
# 3. delete oldest snapshot if number of snapshots > RETENTION, until
#    number of snapshots == RETENTION

import os
import logging

from operator import itemgetter

import boto3

DST_REGION = os.getenv('DST_REGION').strip()
RETENTION  = int(os.getenv('RETENTION').strip())
LOGLEVEL   = os.getenv('LOGLEVEL', 'ERROR').strip()

logger = logging.getLogger()
logger.setLevel(LOGLEVEL.upper())

RDS = boto3.client('rds', region_name=DST_REGION)

def lambda_handler(event, context):
    """Main method
    
    Arguments:
        event {dict} -- Lambda event object
        context {obj} -- Lambda context object
    """
    logger.info('Looking for old replicated snapshots to delete')
    snapshots = get_snapshots()
    for instance, instance_snapshots in snapshots.items():
        # sort by snapshot date ascending. we want to delete oldest snapshots
        # first
        instance_snapshots = sorted(
            instance_snapshots,
            key     = itemgetter('SnapshotCreateTime'),
            reverse = False
        )
        number_of_snapshots = len(instance_snapshots)
        logger.debug('Snapshots for instance {}: {}'.format(instance, number_of_snapshots))
        for snapshot in instance_snapshots:
            if number_of_snapshots > RETENTION:
                try:
                    logger.debug('Snapshot object: {}'.format(snapshot))
                    if 'DBClusterSnapshotArn' in snapshot:
                        deleting = snapshot['DBClusterSnapshotIdentifier']
                        logger.info('Deleting {}'.format(deleting))
                        RDS.delete_db_cluster_snapshot(
                            DBClusterSnapshotIdentifier = deleting
                        )
                    else:
                        deleting = snapshot['DBSnapshotIdentifier']
                        RDS.delete_db_snapshot(
                            DBSnapshotIdentifier = snapshot['DBSnapshotIdentifier']
                        )
                        logger.info('Deleting {}'.format(deleting))
                    number_of_snapshots = number_of_snapshots - 1
                    logger.debug('Snapshots left for instance {}: {}'.format(instance, number_of_snapshots))
                except Exception as e:
                    logger.error('Exception deleting Snapshot: {}'.format(e))
            logger.info('Desired number of snapshots reached for identifier: {}'.format(instance))

def get_snapshots():
    """Finds all RDS and Aurora snapshots
    
    Returns:
        dict -- All snapshot objects
    """
    snapshots = {}
    try:
        logger.info('Fetching DB snapshots')
        response = RDS.describe_db_snapshots()
        logger.debug(response)
        if response:
            for snapshot in response['DBSnapshots']:
                if snapshot['DBInstanceIdentifier'] not in snapshots:
                    snapshots[snapshot['DBInstanceIdentifier']] = []
                if snapshot['DBSnapshotIdentifier'].startswith('replication'):
                    logger.info('Found replicated snapshot {}'.format(snapshot['DBSnapshotIdentifier']))
                    snapshots[snapshot['DBInstanceIdentifier']].append(snapshot)
        logger.debug('snapshots object: {}'.format(snapshots))
    except Exception as e:
        log_message = 'Exception while fetching DB snapshots: {}'.format(e)
        logger.error(log_message)
    try:
        logger.info('Fetching Aurora Cluster snapshots')
        cluster_response = RDS.describe_db_cluster_snapshots()
        logger.debug(cluster_response)
        if cluster_response:
            for snapshot in cluster_response['DBClusterSnapshots']:
                if snapshot['DBClusterIdentifier'] not in snapshots:
                    snapshots[snapshot['DBClusterIdentifier']] = []
                if snapshot['DBClusterSnapshotIdentifier'].startswith('replication'):
                    logger.info('Found replicated snapshot {}'.format(snapshot['DBClusterSnapshotIdentifier']))
                    snapshots[snapshot['DBClusterIdentifier']].append(snapshot)
        logger.debug('snapshots object: {}'.format(snapshots))
    except Exception as e:
        log_message = 'Exception while fetching DB Cluster snapshots: {}'.format(e)
        logger.error(log_message)
    return snapshots
