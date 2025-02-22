from __future__ import print_function
from aws_kinesis_agg.deaggregator import iter_deaggregate_records
import base64
import json
import boto3
import os

# OS input variables:
cloudwatch_namespace = os.environ['cloudwatch_namespace']
cloudwatch_metric = os.environ['cloudwatch_metric']

# AWS Services
cloudwatch = boto3.client('cloudwatch', region_name='eu-west-1')


def lambda_handler(event, context):
    raw_kinesis_records = event['Records']
    record_count = 0

    # Deaggregate all records using a generator function
    for record in iter_deaggregate_records(raw_kinesis_records):

        try:
            # Kinesis data in Python Lambdas is base64 encoded
            payload = base64.b64decode(record['kinesis']['data'])
            json_document = json.loads(payload.decode('utf-8'))

            # Extract data from payload, to publish in CloudWatch.
            # - Note: this can be dynamically built or fetched from properties file,
            #         without hard-coding KEY-VALUE pairs.
            dimension_name_1 = 'severity_accident'
            dimension_value_1 = str(json_document['Severity'])
            dimension_name_2 = 'city_accident'
            dimension_value_2 = json_document['City']
            dimension_name_3 = 'county_accident'
            dimension_value_3 = json_document['County']

            # Push metrics to CloudWatch
            cloudwatch_response = cloudwatch.put_metric_data(
                MetricData=[
                    {
                        'MetricName': cloudwatch_metric,
                        'Dimensions': [
                            {
                                'Name': dimension_name_1,
                                'Value': dimension_value_1
                            },
                            {
                                'Name': dimension_name_2,
                                'Value': dimension_value_2
                            },
                            {
                                'Name': dimension_name_3,
                                'Value': dimension_value_3
                            },
                        ],
                        'Unit': 'Count',
                        'Value': 1,
                        'StorageResolution': 1
                    },
                ],
                Namespace=cloudwatch_namespace
            )

            # Print Cloudwatch response:
            print(cloudwatch_response)

        except Exception as e:
            print('Error when processing stream:')
            print(e)

        # Print response and increment counter
        record_count += 1

    return 'Successfully processed {} records.'.format(record_count)
