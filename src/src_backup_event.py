'''
Copyright 2019  Pinguin AG, Mattis Haase

Licensed under the Apache License, Version 2.0 (the "License").

Inspired by https://github.com/awslabs/rds-snapshot-tool
'''

# src_backup_event.py
# This lambda function looks at an RDS backup event. If the event is a completed
# Snapshot or Cluster snapshot, invoke step function

import json
import logging
import os
import re

import boto3

from common import *

LOGLEVEL          = os.getenv('LOGLEVEL', 'ERROR').strip()
REGION            = os.getenv('REGION').strip()
STATE_MACHINE_ARN = os.getenv('STATE_MACHINE_ARN').strip()
PATTERN           = os.getenv('PATTERN').strip()

logger = logging.getLogger()
logger.setLevel(LOGLEVEL.upper())

RDS = boto3.client('rds', region_name=REGION)
SNS = boto3.client('sns', region_name=REGION)
SFN = boto3.client('stepfunctions', region_name=REGION)

def lambda_handler(event, context):
    """Main method
    
    Arguments:
        event {dict} -- Lambda event object
        context {obj} -- Lambda context object
    """
    logger.debug('event: {}'.format(event))
    msg = json.loads(event['Records'][0]['Sns']['Message'])
    logger.info('Parsing message, type: {}'.format(msg['Event Source']))
    if msg['Event Source'] == 'db-snapshot' or msg['Event Source'] == 'db-cluster-snapshot':
      if msg['Event Message'] == 'Automated snapshot created':
        logger.info('New DB Snapshot created: {}'.format(msg['Source ID']))
        if re.search(PATTERN, msg['Source ID']):
            # Aurora cluster snapshots and RDS snapshots use two different sets
            # of API calls
            if 'cluster' in msg['Event Source']:
                try:
                    rds_response = RDS.describe_db_cluster_snapshots(
                        DBClusterSnapshotIdentifier = msg['Source ID']
                    )
                    arn = rds_response['DBClusterSnapshots'][0]['DBClusterSnapshotArn']
                except Exception as e:
                    log_message = 'Encountered Error: {}'.format(e)
                    logger.error(log_message)
                    raise SnapshotSharingException(log_message)
            else:
                try:
                    rds_response = RDS.describe_db_snapshots(
                        DBSnapshotIdentifier = msg['Source ID']
                    )
                    arn = rds_response['DBSnapshots'][0]['DBSnapshotArn']
                except Exception as e:
                    log_message = 'Encountered Error: {}'.format(e)
                    logger.error(log_message)
                    raise SnapshotSharingException(log_message)
            return_event = {
                'SourceIdentifier': msg['Source ID'],
                'SourceType'      : msg['Event Source'],
                'Message'         : msg['Event Message'],
                'SourceArn'       : arn
            }
            logger.info('Snapshot matches pattern. Trying to invoke Step Function {}.'.format(STATE_MACHINE_ARN))
            logger.debug('Step function to be invoked with input: {}'.format(return_event))
            try:
                response = SFN.start_execution(
                    stateMachineArn = STATE_MACHINE_ARN,
                    input           = json.dumps(return_event)
                )
                logger.info('Step Function response: {}'.format(response))
            except Exception as e:
                logger.error('Encountered Error: {}'.format(e))
