# -*- coding: utf-8 -*-
import os
import boto3
from datetime import datetime
from .config import AWS_CONFIG, LAMBDA_CONFIG
from .termcolor import termcolor, cprint
from botocore.exceptions import ClientError
from shutil import make_archive
from uuid import getnode as get_mac

def get_client(service):
    '''
    Convenient wrapper for boto3 AWS service client

    Args:
        service (str):
            name of AWS service for which to get client
    Returns:
        (boto3.client):
            authenticated client for service
    '''
    return boto3.client(
        service_name = service,
        region_name = os.environ['AWS_DEFAULT_REGION'], 
        aws_access_key_id = os.environ['AWS_ACCESS_KEY'],
        aws_secret_access_key = os.environ['AWS_SECRET_KEY']
    )

class LambdaUnknownException(Exception):
    '''
    Catch-all error for Lambda function create, update, and/or code upload
    '''
    pass

class Lambda(object):
    '''
    Handles creating, updating, and pushing code to an AWS Lambda function

    Args:
        AWS_CONFIG (dict):
            configuration for AWS as a whole. Expects the following keys:
                account_id:
                    AWS account id
                region:
                    AWS region for the Lambda function
        LAMBDA_CONFIG (dict):
            configuration for Lambda function itself. Expects the following keys:
                function_name:
                    name of the function to create or update
                src_dir:
                    path of directory that contains Lambda function
                zip_archive:
                    path/name of zip archive to produce for code in src_dir
                role:
                    name of AWS role with permission to create/update/upload
                    code to the Lambda function
                runtime:
                    name of Lamba runtime (usually 'python3.6')
                handler:
                    name of function in src_dir code to run as main
                expect_failure:
                    for testing, can set expect_failure to True to suppress
                    some errors and test downstream errors more easily
    '''
    def __init__(self, AWS_CONFIG=AWS_CONFIG, LAMBDA_CONFIG=LAMBDA_CONFIG):
        self.client = get_client('lambda')
        self.AWS_CONFIG = AWS_CONFIG
        self.LAMBDA_CONFIG = LAMBDA_CONFIG

    def cprint(self, string, color, time=True, tag='lambda'):
        cprint(string, color, time, tag)

    def make_zip_archive(self, verbose=True):
        make_archive(
            base_name = self.LAMBDA_CONFIG['zip_archive'].replace('.zip',''),
            format = 'zip',
            root_dir = self.LAMBDA_CONFIG['src_dir'],
            base_dir = None
        )
        if verbose:
            self.cprint('Made zip archive {} from files in directory {}'.format(
                    self.LAMBDA_CONFIG['zip_archive'], self.LAMBDA_CONFIG['src_dir']
                ), termcolor.GREEN
            )
        return self

    def create_or_update_function(self, verbose=True):
        lambda_zip_bytes = open(self.LAMBDA_CONFIG['zip_archive'], 'rb').read()
        lambda_role = 'arn:aws:iam::{}:role/{}'.format(self.AWS_CONFIG['account_id'], self.LAMBDA_CONFIG['role'])
        try:
            lambda_create_response = self.client.create_function(
                FunctionName = self.LAMBDA_CONFIG['function_name'],
                Runtime = self.LAMBDA_CONFIG['runtime'],
                Role = lambda_role, 
                Handler = self.LAMBDA_CONFIG['handler'],
                Code = {'ZipFile' : lambda_zip_bytes},
                Description = '[{}]'.format(str(datetime.now())) 
            )
            self.cprint('Created λ function: {}'.format(self.LAMBDA_CONFIG['function_name']),
                    termcolor.GREEN)
            if verbose:
                self.cprint('New λ function configuration: {}'.format(lambda_create_response),
                        termcolor.DEFAULT)
            response = lambda_create_response
        except ClientError as err:
            if err.response['Error']['Code'] == 'ResourceConflictException':
                self.cprint('λ function already exists: {}'.format(
                    self.LAMBDA_CONFIG['function_name']),termcolor.DEFAULT)
            else:
                raise LambdaUnknownException(err)
            lambda_update_response = self.client.update_function_code(
                FunctionName = self.LAMBDA_CONFIG['function_name'],
                ZipFile = lambda_zip_bytes,
                Publish=True
            )
            self.cprint('Updated λ function {} from zip source {}'.format(
                self.LAMBDA_CONFIG['function_name'], self.LAMBDA_CONFIG['zip_archive']),
                termcolor.GREEN)
            if verbose:
                self.cprint('Current λ function configuration: {}'.format(lambda_update_response),
                        termcolor.DEFAULT)
            response = lambda_update_response
        self.create_or_update_response = response
        return self 

    def publish_function_version(self, verbose=True): 
        local_mac_address = str(hex(get_mac()))
        publish_version_response = self.client.publish_version(
            FunctionName = self.LAMBDA_CONFIG['function_name'],
            CodeSha256 = self.create_or_update_response['CodeSha256'],
            Description = '[{}] Version from MAC {}'.format(
                str(datetime.now()), local_mac_address
                )
        )
        self.cprint('Published new λ function version: {}'.format(
            publish_version_response['Version']), termcolor.GREEN)
        if verbose:
            self.cprint('New λ version configuration: {}'.format(publish_version_response),
                    termcolor.DEFAULT)
        self.publish_version_response = publish_version_response
        return self

    def create_alias(self, verbose=True):
        local_mac_address = str(hex(get_mac()))
        function_version = self.publish_version_response['Version']
        function_alias = 'A{}'.format(function_version)
        try:
            create_alias_response = self.client.create_alias(
                FunctionName = self.LAMBDA_CONFIG['function_name'],
                Name = function_alias, 
                FunctionVersion = function_version,
                Description = '[{}] Alias from MAC {}'.format(
                    str(datetime.now()), local_mac_address
                    )
            )
            function_alias_arn = create_alias_response['AliasArn']
            self.create_alias_response = create_alias_response
            self.cprint('Created alias for λ function {}'.format(
                self.LAMBDA_CONFIG['function_name']), termcolor.GREEN)
            if verbose:
                self.cprint('New λ alias configuration: {}'.format(create_alias_response),
                        termcolor.DEFAULT)
        except ClientError as err:
            if err.response['Error']['Code'] == 'ResourceConflictException':
                self.cprint('Alias for λ function already exists', termcolor.DEFAULT)
                get_alias_response = self.client.get_alias(
                    FunctionName=self.LAMBDA_CONFIG['function_name'],
                    Name=function_alias
                )
                function_alias_arn = get_alias_response['AliasArn']
            else:
                self.cprint(
                        '[FAILURE] Could not create or update Alias for λ function: {}'.format(
                        self.LAMBDA_CONFIG['function_name']),
                        termcolor.RED)
                raise LambdaUnknownException(err)
        self.function_alias_arn = function_alias_arn 
        return self

    def test_on_cloud(self, verbose=True):
        function_version = self.publish_version_response['Version']
        function_alias = 'A{}'.format(function_version)
        invoke_response = self.client.invoke(
            FunctionName = self.LAMBDA_CONFIG['function_name'],
            InvocationType = 'RequestResponse',
            LogType = 'Tail',
            Payload = b'{}',
            Qualifier = function_alias 
        )
        function_error = False 
        if 'FunctionError' in invoke_response:
            function_error = invoke_response['FunctionError'] == 'Unhandled'
        if (function_error and self.LAMBDA_CONFIG['expect_failure']) or not function_error:
            self.cprint('[SUCCESS] Tested λ function (alias): {} ({})'.format(
                self.LAMBDA_CONFIG['function_name'], function_alias), termcolor.GREEN)
            if verbose:
                self.cprint('Test λ alias configuration: {}'.format(invoke_response),
                        termcolor.DEFAULT)
                function_output = invoke_response['Payload'].read()
                self.cprint('Test λ alias output: {}'.format(
                    function_output), termcolor.DEFAULT
                )
        else:
            self.cprint('[FAILURE] Tested λ function (alias): {} ({})'.format(
                self.LAMBDA_CONFIG['function_name'], function_alias), termcolor.RED)
            if verbose:
                self.cprint('Test λ alias configuration: {}'.format(invoke_response),
                        termcolor.RED)
                function_output = invoke_response['Payload'].read()
                self.cprint('Test λ alias output: {}'.format(
                    function_output), termcolor.RED
                )
        self.cprint('Expected failure? {}'.format(
            self.LAMBDA_CONFIG['expect_failure']), termcolor.DEFAULT)
        return self
