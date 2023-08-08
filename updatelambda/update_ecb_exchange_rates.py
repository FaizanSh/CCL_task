'''
Description: This code file is a part of application that fetches the data from European Central Bank and provide its exchange rates as json in the form of an API
Creator:     Faizan Ullah
Date:        8/8/23
Email:       faizan.ushahid@gmail.com


Code Functionality:
This code file updates the dynamo db table with difference of exchange rates
'''

import os
import sys
import logging
import urllib.error
import urllib.request
from datetime import datetime
import xml.etree.ElementTree as ET
import boto3

# Constants
DOWNLOAD_URL = 'https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist-90d.xml'
TABLE_NAME = os.environ['DYNAMO_TABLE_NAME']
ENDPOINT_URL = f'http://{os.environ["LOCALSTACK_HOSTNAME"]}:4566' if 'LOCALSTACK_HOSTNAME' in os.environ else None

# Logger Configuration
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

# Main Handler Function
def handler(event, context):
    LOGGER.info('Getting exchange rates data from European Central Bank')
    date, exchange_rates = fetch_exchange_rates_from_ecb()
    LOGGER.info('Updating exchange rates in database')
    update_exchange_rates_in_db(date, exchange_rates)
    LOGGER.info('Job completed')

# Function to Fetch Exchange Rates from European Central Bank
def fetch_exchange_rates_from_ecb():
    try:
        response = urllib.request.urlopen(DOWNLOAD_URL, timeout=30)
        xml_data = response.read()
        doc = ET.fromstring(xml_data)
        data = parse_exchange_rates_from_xml(doc)
        return calculate_exchange_rate_differences(data)
    except urllib.error.URLError as err:
        LOGGER.critical('Failed to download exchange rates data from %s', DOWNLOAD_URL)
        LOGGER.critical(err)
        sys.exit(1)

# Function to Parse Exchange Rates from XML
def parse_exchange_rates_from_xml(doc):
    data = []
    for i, x in enumerate(doc.find('{http://www.ecb.int/vocabulary/2002-08-01/eurofxref}Cube')):
        daily_data = {
            'date': x.attrib['time'].strip(),
            'rates': {y.attrib['currency'].strip(): y.attrib['rate'].strip() for y in x}
        }
        data.append(daily_data)
        if i == 1:
            break
    return data

# Function to Calculate Exchange Rate Differences
def calculate_exchange_rate_differences(data):
    date = data[0]['date']
    latest_rates = data[0]['rates']
    previous_rates = data[1]['rates']
    exchange_rates = {}
    for currency, rate in latest_rates.items():
        if currency not in previous_rates:
            continue
        p_rate = float(previous_rates[currency])
        diff = round(float(rate) - p_rate, 4) or 0.0
        diff_percent = round((diff / p_rate) * 100, 4) or 0.0
        diff = f'+{diff}' if diff > 0 else f'{diff}'
        diff_percent = f'+{diff_percent} %' if diff_percent > 0 else f'{diff_percent} %'
        exchange_rates[currency] = {'value': rate, 'diff': diff, 'diff_percent': diff_percent}
    return date, exchange_rates

# Function to Update Exchange Rates in Database
def update_exchange_rates_in_db(date, exchange_rates):
    dynamodb = boto3.resource('dynamodb', endpoint_url=ENDPOINT_URL)
    table = dynamodb.Table(TABLE_NAME)
    with table.batch_writer() as writer:
        for currency, data in exchange_rates.items():
            data['id'] = currency
            writer.put_item(Item=data)
        writer.put_item(Item={'id': 'publish_date', 'value': date})
        writer.put_item(Item={'id': 'update_date', 'value': datetime.utcnow().strftime('%Y-%m-%d')})
