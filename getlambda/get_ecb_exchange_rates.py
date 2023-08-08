'''
Description: This code file is a part of application that fetches the data from European Central Bank and provide its exchange rates as json in the form of an API
Creator:     Faizan Ullah
Date:        8/8/23
Email:       faizan.ushahid@gmail.com


Code Functionality:
This code file reads data from dynamodb and creates response in json format. 
'''

import os
import json
import logging
import boto3

# Logger Configuration
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

# DynamoDB Table Configuration
TABLE_NAME = os.environ['DYNAMO_TABLE_NAME']
ENDPOINT_URL = f'http://{os.environ["LOCALSTACK_HOSTNAME"]}:4566' if 'LOCALSTACK_HOSTNAME' in os.environ else None

# Main Handler Function
def handler(event, context):
    LOGGER.info('Reading exchange rates from database')
    exchange_rates = fetch_exchange_rates_from_db()
    
    if not exchange_rates:
        LOGGER.info('No data available')
        return response_with_error("No data available, please try later")
    
    response_data = construct_response(exchange_rates)
    return response_with_success(response_data)

# Function to Read Exchange Rates from Database
def fetch_exchange_rates_from_db():
    dynamodb = boto3.resource('dynamodb', endpoint_url=ENDPOINT_URL)
    table = dynamodb.Table(TABLE_NAME)
    tblscan = table.scan()
    items = tblscan.get('Items', [])
    
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response['Items'])
    
    return items

# Function to Construct Response
def construct_response(items):
    response = {'update_date': 'N/A', 'publish_date': 'N/A', 'base_currency': 'EUR', 'exchange_rates': []}
    
    for item in items:
        if item['id'] in ('update_date', 'publish_date'):
            response[item['id']] = item['value']
        else:
            currency_data = {
                'currency':          item['id'],
                'rate':              item['value'],
                'change':            item['diff'],
                'change_percentage': item['diff_percent']
            }
            response['exchange_rates'].append(currency_data)
    
    response['exchange_rates'] = sorted(response['exchange_rates'], key=lambda x: x['currency'])
    return response

# Function to Return Success Response
def response_with_success(data):
    return {'statusCode': 200, 'body': json.dumps(data, indent=4)}

# Function to Return Error Response
def response_with_error(error_message):
    return {'statusCode': 200, 'body': json.dumps({'error': error_message}, indent=4)}
