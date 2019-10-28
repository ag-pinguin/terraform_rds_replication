'''
Copyright 2019  Pinguin AG, Mattis Haase

Licensed under the Apache License, Version 2.0 (the "License").

Inspired by https://github.com/awslabs/rds-snapshot-tool
'''

# dst_copy_snapshot.py
# This lambda function copies the shared snapshot to the destination account

import os
import logging

import boto3

from common import *

DST_ARN     = os.getenv('DST_ARN').strip()
DST_REGION  = os.getenv('DST_REGION').strip()
LOGLEVEL    = os.getenv('LOGLEVEL', 'ERROR').strip()
SRC_ACCOUNT = os.getenv('SRC_ACCOUNT').strip()

logger = logging.getLogger()
logger.setLevel(LOGLEVEL.upper())

# This function is executed on a different account so we have to get the credentials
STS = boto3.client('sts')
awsaccount = STS.assume_role(
        RoleArn         = DST_ARN,
        RoleSessionName ='awsaccount_session'
)

ACCESS_KEY    = awsaccount['Credentials']['AccessKeyId']
SECRET_KEY    = awsaccount['Credentials']['SecretAccessKey']
SESSION_TOKEN = awsaccount['Credentials']['SessionToken']

RDS = boto3.client('rds', region_name=DST_REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY, aws_session_token=SESSION_TOKEN)

def lambda_handler(event, context):
    """Copy shared snapshot
    
    Arguments:
        event {dict} -- Lambda event object
        context {obj} -- Lambda context object
    
    Returns:
        dict -- as event
    """
    cluster = False
    if 'cluster' in event['SourceType']:
        cluster = True
    logger.debug('event: {}'.format(event))

    # Get the ARN of the shared snapshot to copy
    if cluster:
        shared_snapshot_arn = 'arn:aws:rds:{}:{}:cluster-snapshot:{}'
    else:
        shared_snapshot_arn = 'arn:aws:rds:{}:{}:snapshot:{}'

    shared_snapshot_arn = shared_snapshot_arn.format(
        DST_REGION,
        SRC_ACCOUNT,
        event['local_copy_snapshot_identifier']
    )
    logger.debug('arn: {}'.format(shared_snapshot_arn))

    # Generating name for our local snapshot copy
    local_copy_name = 'replication-{}-{}'.format(SRC_ACCOUNT, event['SourceIdentifier'].replace(':', '-'))
    logger.info('Copying snapshot {} from account {} to {}'.format(shared_snapshot_arn, SRC_ACCOUNT, local_copy_name))

    try:
        if cluster:
            response = RDS.copy_db_cluster_snapshot(
                SourceDBClusterSnapshotIdentifier = shared_snapshot_arn,
                TargetDBClusterSnapshotIdentifier = local_copy_name,
            )
        else:
            response = RDS.copy_db_snapshot(
                SourceDBSnapshotIdentifier = shared_snapshot_arn,
                TargetDBSnapshotIdentifier = local_copy_name,
            )
        logger.info('Response: {}'.format(response))
    except Exception as e:
        log_message = 'Exeption: {}'.format(e)
        logger.error(log_message)
        raise SnapshotSharingException(log_message)
    event['dst_snapshot_identifier'] = local_copy_name
    return event
