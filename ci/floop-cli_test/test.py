import os
import boto3
import json
import hmac
import hashlib

from base64 import b64decode
from random import choice
from string import ascii_uppercase
from time import time

'''
Note:
    AWS_DEFAULT_REGION, AWS_ACCESS_KEY, AWS_SECRET_KEY are protected by Lambda
    Add a trailing _ to define your own. Make sure these values are defined
    in the Lambda dashboard.
'''

def decrypt(key):
    return boto3.client('kms').decrypt(CiphertextBlob=b64decode(os.environ[key]))['Plaintext'].decode('utf-8')

def validate_secret(event):
    sha, sig = event['headers']['X-Hub-Signature'].split('=')
    if sha != 'sha1':
        return False
    digest = hmac.new(
        bytes(os.environ['FLOOP_CLI_GITHUB_WEBHOOK_SECRET'], 'utf-8'),
        msg=bytes(event['body'], 'utf-8'),
        digestmod=hashlib.sha1).hexdigest()
    valid = hmac.compare_digest(digest.encode('utf-8'), sig.encode('utf-8'))
    return valid

def get_client(service):
    return boto3.client(
        service_name = service,
        region_name = decrypt('AWS_DEFAULT_REGION_'), 
        aws_access_key_id = decrypt('AWS_ACCESS_KEY_'),
        aws_secret_access_key = decrypt('AWS_SECRET_KEY_')
    )

def docker_machine_name():
    return ''.join(choice(ascii_uppercase) for i in range(16)) + str(int(time()*10000))

def docker_machine_string(name):
    return '''docker-machine create \
--driver amazonec2 \
--amazonec2-instance-type=t2.nano \
--amazonec2-region={} \
--amazonec2-access-key={} \
--amazonec2-secret-key={} \
{}'''.format(
        decrypt('AWS_DEFAULT_REGION_'),
        decrypt('AWS_ACCESS_KEY_'),
        decrypt('AWS_SECRET_KEY_'),
        name)

def lambda_handler(event, context):
    '''
    AWS Lambda handler for floopcli integration testing
    '''
    if not validate_secret(event):
        return {
            'statusCode': 400,
            'body': json.dumps({'error' : 'Invalid Github secret'})
        }
    try:
        body = json.loads(event['body'])
    except (KeyError, json.decode.JSONDecodeError):
        return {
            'statusCode': 400,
            'body': json.dumps({'error' : 'No body'})
        }
    try:
        commit = body['after']
    except KeyError:
        return {
            'statusCode': 400,
            'body': json.dumps({'input': event, 'error' : 'No commit ID'})
        }
    try:
        branch = body['ref'].split('/')[-1]
    except KeyError:
        return {
            'statusCode': 400,
            'body': json.dumps({'input': event, 'error' : 'No branch?'})
        }

    ec2 = get_client('ec2')

    cores = [docker_machine_name(), docker_machine_name()]

    # this bash script runs as soon as the ec2 instance boots
    init_script = '''#!/bin/bash

# if any command fails, just clean up and exit
set -e

# force shutdown and terminate after a time limit, even if processes are running
shutdown -H 15 

# add SSH key for testing
mkdir -p /root/.ssh/
# the SSH_KEY env variable must contain slash-n newline characters
echo -e "{sshkey}" > /root/.ssh/id_rsa && chmod 700 /root/.ssh/id_rsa

echo "added key to root"

# don't run as root
su ubuntu

# push logs that Github badge can link to
log () {{
    # just returns an empty log if it doesn't make it to pytest
    touch /var/log/user-data.log
    # pipe test results into raw html
    echo "<pre>" > build-status.html
    date >> build-status.html
    echo "FOR MORE INFORMATION ABOUT THESE TESTS, VISIT THE ci/ FOLDER IN THIS BRANCH OF THE FLOOP REPO" >> build-status.html
    echo "Branch: {branch}" >> build-status.html
    echo "Commit: {commit}" >> build-status.html
    cat /var/log/user-data.log >> build-status.html
    echo "</pre>" >> build-status.html
    # push raw html to s3
    aws s3 cp build-status.html s3://docs.forward-loop.com/floopcli/{branch}/status/build-status.html --cache-control max-age=0,no-cache --metadata-directive REPLACE
}}

# clean up function to run at the end of testing
cleanup () {{
    log
    docker-machine rm -f {dm0} || true
    docker-machine rm -f {dm1} || true
    shutdown -H now
}}

error () {{
    # copy the failing build badge to the status URL
    aws s3 cp s3://docs.forward-loop.com/status/build-failing.png s3://docs.forward-loop.com/floopcli/{branch}/status/build-status.png || true
    cleanup
}}

success () {{
    # copy the passing build badge to the status URL
    aws s3 cp s3://docs.forward-loop.com/status/build-passing.png s3://docs.forward-loop.com/floopcli/{branch}/status/build-status.png || true
    cleanup
}}

# no matter what happens, call cleanup
# trap errors
trap error ERR INT TERM SIGINT SIGTERM SIGHUP

# install system dependencies
sudo apt-get update && sudo apt-get install -y curl git rsync python3-pip

# install awscli to use s3 sync
sudo pip3 install awscli

# configure aws with env variables
aws configure set aws_access_key_id {awskey} 
aws configure set aws_secret_access_key {awssecret} 
aws configure set default.region {awsregion} 

# copy the pending build badge to the status URL
aws s3 cp s3://docs.forward-loop.com/status/build-pending.png s3://docs.forward-loop.com/floopcli/{branch}/status/build-status.png

# copy pending build-status.html to badge link
echo "<pre>" > build-status.html
date >> build-status.html
echo "FOR MORE INFORMATION ABOUT THESE TESTS, VISIT THE ci/ FOLDER IN THIS BRANCH OF THE FLOOP REPO" >> build-status.html
echo "Branch: {branch}" >> build-status.html
echo "Commit: {commit}" >> build-status.html
echo "Build Pending" >> build-status.html
echo "</pre>" >> build-status.html
# push raw html to s3
aws s3 cp build-status.html s3://docs.forward-loop.com/floopcli/{branch}/status/build-status.html --cache-control max-age=0,no-cache --metadata-directive REPLACE

# clone floopcli repo
git clone https://github.com/ForwardLoopLLC/floopcli.git 

# checkout the commit that was just pushed
cd floopcli && git checkout {commit}

# local install floopcli and tests
sudo pip3 install -e .[test]

# build the docs and move to a named folder for s3
cd docs && make html && mkdir -p s3/floopcli/{branch}/ && \
        cp -r build/html/* s3/floopcli/{branch}/ && cd ..

# check static typing
mypy --config-file mypy.ini floopcli

# check python 2 compatibility
mypy --py2 --config-file mypy.ini floopcli

# install docker-machine
base=https://github.com/docker/machine/releases/download/v0.14.0 &&\
  curl -L $base/docker-machine-$(uname -s)-$(uname -m) >/tmp/docker-machine &&\
  sudo install /tmp/docker-machine /usr/local/bin/docker-machine

# start "target" ec2 instances as AWS Docker Machines, add ubuntu to docker group
{dmstr0} && docker-machine ssh {dm0} sudo usermod -aG docker ubuntu
{dmstr1} && docker-machine ssh {dm1} sudo usermod -aG docker ubuntu

# try to get ec2 to give any relevant information
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

# run pytest on floopcli, set cloud test env variable to true
FLOOP_CLOUD_TEST=true FLOOP_CLOUD_CORES={dm0}:{dm1} pytest --cov-report term-missing --cov=floopcli -v -s -x floopcli

# sync documentation to docs website
aws s3 sync docs/s3/ s3://docs.forward-loop.com

# trap success
trap success EXIT 
'''.format(
        dm0=cores[0],
        dm1=cores[1],
        commit=commit,
        awskey=decrypt('AWS_ACCESS_KEY_'),
        awssecret=decrypt('AWS_SECRET_KEY_'), 
        awsregion=decrypt('AWS_DEFAULT_REGION_'),
        sshkey=decrypt('SSH_KEY'),
        branch=branch,
        dmstr0=docker_machine_string(cores[0]),
        dmstr1=docker_machine_string(cores[1]),
    )

    # these logs go to cloudwatch, not user-data.log  or /var/sys/log
    print(init_script)

    instance = ec2.run_instances(
        # use env default or default AMI for ap-southeast-1
        ImageId=os.environ.get('DEFAULT_AMI') or 'ami-2378f540',
        # use env default or smallest ec2 instance
        InstanceType=os.environ.get('DEFAULT_INSTANCE_TYPE') or 't2.nano',
        MinCount=1,
        MaxCount=1,
        InstanceInitiatedShutdownBehavior='stop',
        UserData=init_script,
        KeyName='FLOOP_CLI_KEY'
    )

    instance_id = instance['Instances'][0]['InstanceId']
    print(instance_id)
    return {
            'statusCode': 200,
            'body': json.dumps({'instance_id' : instance_id})
        }
