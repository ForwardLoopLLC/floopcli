import os

AWS_CONFIG = {
    'account_id' : os.environ['AWS_ACCOUNT_ID'], 
    'region' : os.environ['AWS_DEFAULT_REGION']
}

LAMBDA_CONFIG = {
    'function_name':'floop-cli_test',
    'src_dir':'./floop-cli_test/',
    'zip_archive':'./floop-cli_test.zip',
    'role':'floop-cli-test-role',
    'runtime':'python3.6',
    'handler':'test.lambda_handler',
    'expect_failure' : False 
}
