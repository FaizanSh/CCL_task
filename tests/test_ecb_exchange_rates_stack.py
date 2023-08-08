'''
Description: This code file is a part of application that fetches the data from European Central Bank and provide its exchange rates as json in the form of an API
Creator:     Faizan Ullah
Date:        8/8/23
Email:       faizan.ushahid@gmail.com


Code Functionality:
This is a unit test file created to validate cdk stack for essential resources. 
'''
import aws_cdk as core
import aws_cdk.assertions as assertions
from app import ECBExchangeRatesStack

def create_stack():
    '''
    Stack Creation.
    '''
    app = core.App()
    return ECBExchangeRatesStack(app, 'ecb-exchange-rates')

def test_dynamodb_table_created():
    '''
    DynamoDB table.
    '''
    stack = create_stack()
    template = assertions.Template.from_stack(stack)
    dynamodb_table_properties(template)
    dynamodb_table_deletion_policy(template)

def dynamodb_table_properties(template):
    template.has_resource_properties('AWS::DynamoDB::Table', {
        'KeySchema': [{'AttributeName': 'id', 'KeyType': 'HASH'}],
        'AttributeDefinitions': [{'AttributeName': 'id', 'AttributeType': 'S'}]
    })

def dynamodb_table_deletion_policy(template):
    template.has_resource('AWS::DynamoDB::Table', {'DeletionPolicy': 'Delete'})

def test_update_lambda_created():
    '''
    ECB updating data Lambda Function.
    '''
    stack = create_stack()
    template = assertions.Template.from_stack(stack)
    lambda_properties(template, 'update_ecb_exchange_rates.handler', 360)

def test_read_lambda_created():
    '''
    ECB get data lambda Function.
    '''
    stack = create_stack()
    template = assertions.Template.from_stack(stack)
    lambda_properties(template, 'get_ecb_exchange_rates.handler', 60)

def lambda_properties(template, handler, timeout):
    template.has_resource_properties('AWS::Lambda::Function', {
        'Handler': handler,
        'Runtime': 'python3.8',
        'Timeout': timeout,
        'Environment': {'Variables': {'DYNAMO_TABLE_NAME': {}}}
    })

def test_rest_api_created():
    '''
    REST API.
    '''
    stack = create_stack()
    template = assertions.Template.from_stack(stack)
    rest_api_properties(template)

def rest_api_properties(template):
    template.has_resource_properties('AWS::ApiGateway::RestApi', {'Name': 'api-ecb-exchange-rates'})
    template.has_resource_properties('AWS::ApiGateway::Resource', {'PathPart': 'ecbexchangerates'})
    template.has_resource_properties('AWS::ApiGateway::Method', {'HttpMethod': 'GET'})

