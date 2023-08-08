#!/usr/bin/env python3

import aws_cdk as cdk
from constructs import Construct
from aws_cdk import (
    Stack,
    Duration,
    triggers,
    RemovalPolicy,
    aws_logs as logs,
    aws_lambda as lambda_,
    aws_dynamodb as dynamodb,
    aws_apigateway as apigateway,
    aws_events as events,
    aws_events_targets as events_targets
)


# Exchange Rates Tracking Stack Class
class ECBExchangeRatesStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # DynamoDB Table
        exchange_rates_table = self.create_dynamodb_table()

        # Lambda Functions
        update_lambda = self.create_lambda_function('update-ecb-exchange-rates', 'update_ecb_exchange_rates.handler', 6,'./updatelambda')
        read_lambda = self.create_lambda_function('get-ecb-exchange-rates', 'get_ecb_exchange_rates.handler', 1,'./getlambda')

        #add variable
        update_lambda.add_environment('DYNAMO_TABLE_NAME', exchange_rates_table.table_name)
        read_lambda.add_environment('DYNAMO_TABLE_NAME', exchange_rates_table.table_name)

        # Grant Permissions
        exchange_rates_table.grant_read_write_data(update_lambda)
        exchange_rates_table.grant_read_data(read_lambda)

        # Schedule Lambda Execution
        self.schedule_lambda_execution(update_lambda)

        # REST API
        self.create_rest_api(read_lambda)

        # Trigger for Initial Data Population
        self.create_initial_data_trigger(exchange_rates_table, update_lambda)

    def create_dynamodb_table(self):
        return dynamodb.Table(self, 'table-ecb-exchange-rates',
                              partition_key=dynamodb.Attribute(name='id', type=dynamodb.AttributeType.STRING),
                              removal_policy=RemovalPolicy.DESTROY)

    def create_lambda_function(self, id, handler, timeout_minutes, codepath):
        return lambda_.Function(self, id,
                                runtime=lambda_.Runtime.PYTHON_3_8,
                                code=lambda_.Code.from_asset(codepath),
                                handler=handler,
                                timeout=Duration.minutes(timeout_minutes),
                                log_retention=logs.RetentionDays.ONE_DAY)
        

    def schedule_lambda_execution(self, lambda_function):
        update_schedule = events.Schedule.cron(hour='17', minute='0')
        update_target = events_targets.LambdaFunction(handler=lambda_function)
        events.Rule(self, "ecb-exchange-rates-update-scheduler",
                    description="SNeed to update the database after exchange rates update on the website",
                    enabled=True,
                    schedule=update_schedule,
                    targets=[update_target])

    def create_rest_api(self, lambda_function):
        api = apigateway.LambdaRestApi(self, 'api-ecb-exchange-rates',
                                       handler=lambda_function,
                                       proxy=False)
        api.root.add_resource('ecbexchangerates').add_method('GET')

    def create_initial_data_trigger(self, exchange_rates_table, update_lambda):
        init_trigger = triggers.TriggerFunction(self, 'init-ecb-echange-rates',
                                                execute_after=[exchange_rates_table, update_lambda],
                                                runtime=lambda_.Runtime.PYTHON_3_8,
                                                code=lambda_.Code.from_asset('./updatelambda'),
                                                handler='update_ecb_exchange_rates.handler',
                                                timeout=Duration.minutes(5),
                                                log_retention=logs.RetentionDays.ONE_DAY,
                                                execute_on_handler_change=False)
        init_trigger.add_environment('DYNAMO_TABLE_NAME', exchange_rates_table.table_name)
        exchange_rates_table.grant_read_write_data(init_trigger)

# Main Application
APP = cdk.App()
ECBExchangeRatesStack(APP, 'ecb-exchange-rates')
APP.synth()

