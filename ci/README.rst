floop Continuous Integration
============================

Overview
--------
floop tests run on a custom CI platform that allows testing of virtual hardware through existing Docker machines/floop cores. This repository uses Github webhooks to start test runs on EC2 instances on AWS. These tests automatically update the build badge and the build logs for the repo.

floop needs access to virtual hardware in order to test network creation, network deletion, and remote installation features. This is not currently possible with most commercial CI platforms because they use virtual environments for test runs. These virtual environments do not usually enable nested virtualization, so it is not possible to test virtual hardware in these environments.

How It Works
------------
The CI environment works as follows:

- Developer uses *git push* to push code a development branch
- Github webhook calls an AWS Lambda function to begin testing
- The AWS Lambda function does the following:
    - Starts an AWS EC2 server running Ubuntu
    - Installs operating system dependencies on the EC2 server
    - Uses *git pull* to pull the new code commit to the EC2 server
    - Starts two Docker Machines using the *--driver amazonec2* flag
    - Sets the **FLOOP_CLOUD_TEST** and **FLOOP_CLOUD_CORES** environment variables to tell the CI suite to run cloud tests, as opposed to local hardware tests
    - Runs *pytest* tests using the AWS EC2 Docker Machines as virtual hardware
    - If the tests succeed, pushes the new documentation to the documentation website
    - Updates the documentation website S3 bucket for the documentation so the build badge image corresponds to whether the tests are pending, failing, or passing

You can find more information about the AWS Lambda function in the **floop-cli_test** folder. Specifically, the *init-script* argument to start the AWS EC2 instance defines the build and run instructions for the AWS EC2 server and the two AWS EC2 Docker Machines. These build instructions are very similar to the type of build instructions you would specify in a Dockerfile. **The init-script is the most important part to understand in the CI pipeline. The rest of the code exists to enhance the convenience and security of running the init-script instructions.**

For convenience, there is a script that allows developers to push new AWS Lambda functions and aliases directly to the cloud. You can read more about this utility by checking *push.py* and its associated functions in the **test** folder.
