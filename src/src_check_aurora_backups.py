'''
Copyright 2019  Pinguin AG, Mattis Haase

Licensed under the Apache License, Version 2.0 (the "License").

Inspired by https://github.com/awslabs/rds-snapshot-tool
'''

# src_check_aurora_backups.py
# Automated RDS snapshot create events but Aurora snapshots do not.
# So we have to look through snapshots with a script periodically, emitting an
# event for all new ones.
#
# 1. search for DB clusters that match PATTERN
# 2. search for last BACKUP_LAST_N snapshots for those DB clusters without tag
#    'rds-replication-replicated'
# 3. emit an SNS event for each one
# 4. if response 200: set tag 'rds-replication-replicated' on snapshot

import json
import logging
import os
import re

from operator import itemgetter

import boto3

LOGLEVEL      = os.getenv('LOGLEVEL', 'ERROR').strip()
REGION        = os.getenv('REGION').strip()
SNS_TOPIC_ARN = os.getenv('SNS_TOPIC_ARN').strip()
PATTERN       = os.getenv('PATTERN').strip()
BACKUP_LAST_N = int(os.getenv('BACKUP_LAST_N').strip())


logger = logging.getLogger()
logger.setLevel(LOGLEVEL.upper())

SNS = boto3.client('sns', region_name=REGION)
RDS = boto3.client('rds', region_name=REGION)

def lambda_handler(event, context):
    """Main method
    
    Arguments:
        event {dict} -- Lambda event object
        context {obj} -- Lambda context object
    """
    logger.debug('event: {}'.format(event))

    # Get all clusters which match PATTERN
    clusters = get_clusters()

    for cluster in clusters:
        # get BACKUP_LAST_N snapshots for cluster without replication tag
        snapshots = get_snapshots(cluster)
        for snapshot in snapshots:
            event_submitted = submit_event(snapshot)
            if event_submitted:
                tag_snapshot(snapshot)

def get_clusters():
    """Returns cluster identifiers whose pattern matches PATTERn
    
    Returns:
        list -- Matching cluster identifiers
    """
    logger.info('Getting Clusters')
    clusters = []
    response = RDS.describe_db_clusters()
    if not response['DBClusters']:
        logger.info('No DB Clusters found')
        return
    for cluster in response['DBClusters']:
        logger.debug('Checking if {} matches PATTERN'.format(cluster['DBClusterIdentifier']))
        if re.search(PATTERN, cluster['DBClusterIdentifier']):
            clusters.append(cluster['DBClusterIdentifier'])
        logger.info('Clusters which match the pattern: {}'.format(clusters))
    return clusters

def get_snapshots(cluster):
    """returns a list of the BACKUP_LAST_N snapshots for cluster
    
    Arguments:
        cluster {str} -- DBClusterIdentifier
    
    Returns:
        list -- Matching snapshot objects
    """
    logger.info('Getting snapshots for cluster {}'.format(cluster))
    snapshots = []
    # get all automated snapshots. manual snapshots are not replicated by this
    # if you want to replicate manual snapshots, keep in mind they already emit
    # an event, so you want to edit src_backup_event.py
    response = RDS.describe_db_cluster_snapshots(
        DBClusterIdentifier = cluster,
        SnapshotType        = 'automated'
    )
    try:
        if not response['DBClusterSnapshots']:
            logger.info('No Snapshots found for cluster {}'.format(cluster))
            return snapshots
        # sort list so its easier to get the last BACKUP_LAST_N
        snapshots = sorted(
            response['DBClusterSnapshots'],
            key     = itemgetter('SnapshotCreateTime'),
            reverse = True
        )
        # return the latest BACKUP_LAST_N snapshots without tag rds-replication-replicated
        to_be_replicated = []
        for snapshot in snapshots[:BACKUP_LAST_N]:
            logger.debug('Checking snapshot {} for tags'.format(snapshot['DBClusterSnapshotArn']))
            tag_response = RDS.list_tags_for_resource(
                ResourceName = snapshot['DBClusterSnapshotArn']
            )
            logger.debug('tag_response for {}: {}'.format(snapshot['DBClusterSnapshotIdentifier'], tag_response))
            replication_flag = True
            if 'TagList' in tag_response:
                for tag in tag_response['TagList']:
                    if tag['Key'] == 'rds-replication-replicated':
                        logger.debug('Snapshot {} already tagged'.format(snapshot['DBClusterSnapshotIdentifier']))
                        replication_flag = False
            if replication_flag:
                logger.debug('Adding {} to be replicated'.format(snapshot['DBClusterSnapshotIdentifier']))
                to_be_replicated.append(snapshot)
        logger.info('Snapshots to be replicated for cluster {}: {}'.format(cluster, to_be_replicated))
        return to_be_replicated
    except Exception as e:
        logger.error('Exception while getting snapshots for cluster {}: {}'.format(cluster, e))
        return []

def submit_event(snapshot):
    """emits SNS event looking like an 'Automated Snapshot created' event
    
    Arguments:
        snapshot {dict} -- Snapshot object
    
    Returns:
        boolean -- True if event has been submitted, else False
    """
    # 
    logger.info('Publishing event for {} to {}'.format(snapshot['DBClusterSnapshotIdentifier'], SNS_TOPIC_ARN))
    event = {
        'Event Message' : 'Automated snapshot created',
        'Event Source'  : 'db-cluster-snapshot',
        'Source ID'     : snapshot['DBClusterSnapshotIdentifier']
    }
    logger.debug('Event: {}'.format(event))
    try:
        publish_response = SNS.publish(
          TopicArn = SNS_TOPIC_ARN,
          Message  = json.dumps(event)
        )
    except Exception as e:
        logger.error('Exception: {}'.format(e))
        return False
    logger.info('Event published')
    logger.debug(event)
    return True

def tag_snapshot(snapshot):
    """Tag replicated snapshots
    
    Arguments:
        snapshot {dict} -- Snapshot object
    
    Returns:
        Boolean -- True if tagging worked else False
    """
    try:
        logger.info('Tagging snapshot {}'.format(snapshot['DBClusterSnapshotIdentifier']))
        tagging_response = RDS.add_tags_to_resource(
            ResourceName = snapshot['DBClusterSnapshotArn'],
            Tags         = [
                {
                    'Key'  : 'rds-replication-replicated',
                    'Value': 'event-generated'
                }
            ]
        )
        return True
    except Exception as e:
        logger.error('Exception: {}'.format(e))
        return False
