.. _intro-hello:

===================
Hello, World! Guide
===================

Overview
========
**Estimated time to complete:**
    30 to 60 minutes

In this guide, you will try out all of the floop commands. In order to do so, you will:
    - develop a simple Hello, World! app and tests in one of several languages 
    - define simple test and production environments using `Dockerfiles <https://docs.docker.com/engine/reference/builder/>`_
    - **configure** floop with the app
    - **create** floop target cores that handle communication with your real hardware targets
    - **push** source code from your host core to target cores
    - **build** code on target cores
    - **test** code on target cores in a test operating system environment on the target
    - **run** code on target cores in a production operating system environment on the target
    - **monitor** running or testing environments on target cores
    - **log** all events to the host 
    - **destroy** floop cores and reclaim resources on all target cores

In the end, each target core should greet you with "Hello, World!"

If you have Linux-based target cores, you can use them for this guide. Otherwise, follow along to see how to use Docker Machines on your host to run and test floop using just your computer.

Prerequisites
==============
At least one of the following:

.. tabs::

    .. tab:: ARM Cores 

        This is the option for using floop with real cores.

        You can use one or more ARM cores running a Linux-based operating system with `kernel version 3.10+ <https://docs.docker.com/engine/faq/#how-far-do-docker-containers-scale>`_. For example, `Orange Pi Zero <http://www.orangepi.org/orangepizero/>`_ running `Armbian <https://www.armbian.com/orange-pi-zero/>`_ mainline kernel.
            If you use target hardware, please make sure the operating system on each core follows the :ref:`intro-os`. 

    .. tab:: Docker Machines 

        This is the option for testing or evaluating floop before you use it with real cores.

        You can use one or more Docker Machines running on your host. To see how to do this, check the `Docker Machine Tutorial <https://docs.docker.com/machine/get-started/>`_ for how to run local Docker Machines using Virtualbox. Once you install Docker Machine and local machine dependencies, you can typically start a new machine as follows: 

.. code-block:: bash

  #!/bin/bash
  docker-machine create \
  --driver virtualbox \
  --virtualbox-memory 1024 \
  core0

That creates a new Docker Machine called *core0* with 1GB of virtual memory.

When you are finished, you can clean up as follows:
::

  #!/bin/bash
  docker-machine rm -f core0

If you want to test floop with multiple local cores, you can use the procedure above to make new cores and name them whatever you want, removing them when you are finished.
      

1. Install Floop
================
Check out the :ref:`intro-install` here.

2. Develop a Simple App
=======================
To start, we will make a simple app to print "Hello, World!" to the console. We will also add a small test suite to make sure our code works.

.. tabs::

    .. tab:: C++ 

        Make a new **project** folder with a **src** folder inside:
        ::
            mkdir -p ./project/src/ && cd ./project/
       
        We need a function to print "Hello, World!" in order to test it
        outside of the main routine.
        
        Add the following code to a file called **src/hello.cpp**:

        .. literalinclude:: ../../../example/cpp/hello/src/hello.cpp
            :language: c++

        We need a header file in order to share the *hello* function 
        between the main routine and the test routine.

        Add the following code to a file called **src/hello.h**:
            
        .. literalinclude:: ../../../example/cpp/hello/src/hello.h
            :language: c++

        We need a test routine in order to test the *hello* function.
        We will use the `Google Test <https://github.com/google/googletest>`_ library to run our tests.

        Add the following code to a file called **src/hello_test.cpp**:

        .. literalinclude:: ../../../example/cpp/hello/src/hello_test.cpp
            :language: c++

        Finally, we need a main routine to run the *hello* function
        in production.

        Add the following code to a file called **src/main.cpp**:

        .. literalinclude:: ../../../example/cpp/hello/src/main.cpp
            :language: c++


    .. tab:: Python

        Make a new **project** folder:
        ::
            mkdir -p ./project/ && cd ./project/

        We need a function to print "Hello, World". This function
        will double as our main routine if the file containing
        the *hello* function is called as a Python script.

        Add the following code to a file called **hello.py**:

        .. literalinclude:: ../../../example/python/hello/hello.py
            :language: python

        We need a test suite to test our *hello* function.
        We will use the `pytest <https://docs.pytest.org/en/latest/>`_ library to run our tests. 

        Add the following code to a file called **hello_test.py**:

        .. literalinclude:: ../../../example/python/hello/hello_test.py
            :language: python

        In order for Python to consider our folder a package so that we can import code from **hello.py** into **hello_test.py**, add a blank file called **__init__.py**:
        ::
            touch ./__init__.py

        Test our code on the host:
        ::
            python ./hello.py

        You should see "Hello, World!" on the console.

    .. tab:: Go 

        Make a new **project** folder with a **src** folder inside with a **hello** folder and a **main** inside **src**:
        ::

            mkdir -p ./project/src/hello/ && \
            mkdir -p ./project/src/main/ && \
            cd ./project/

        We need a function to print "Hello, World!" in order to test it outside of the main routine.

        Add the following code to a file called **src/hello/hello.go**:

        .. literalinclude:: ../../../example/go/hello/src/hello/hello.go

        We need a test suite to test our *hello* function. We will use the native testing features in Go, so we have no external dependencies.

        Add the following code to a file called **src/hello/hello_test.go**:

        .. literalinclude:: ../../../example/go/hello/src/hello/hello_test.go

        Finally, we need a main routine to run the *hello* function in production.

        Add the following code to a file called **src/main/main.go**:

        .. literalinclude:: ../../../example/go/hello/src/main/main.go

We now have a simple app. In order to test and to run this app, we need to define test and run environments.

3. Define Test and Run Environments
==========================================
We need to define a test and a run environment so we can run our tests to make sure that the code will work during deployment and then run the production code. For this purpose, floop uses Docker to create runtime environments with all dependencies and code installed as needed.  

Both the test and run environments will run inside a virtual operating system on your target cores. This standardizes your test and production environments across cores, despite different underlying hardware and operating systems installed on that hardware.

Since testing often requires different dependencies and run behavior than a production environment, we will need one environment build file to test and another to run. 

.. tabs::

    .. tab:: C++ 

        First, define the test environment.
        
        We will start with a Debian Jessie operating system image, install a C++ compiler, install a testing library (Google Test), and set the default behavior of the environment to run the tests. 

        To accomplish these steps, add the following code to a file called **Dockerfile.test**:

        .. literalinclude:: ../../../example/cpp/hello/Dockerfile.test
           
        At the end of the **Dockerfile.test** environment, it calls a script called **test.sh**. This script should compile all the code that needs to be tested, then run that code inside of the test environment.

        Add the following code to a file called **test.sh**:

        .. literalinclude:: ../../../example/cpp/hello/test.sh

        Now when we run our floop tests, we will automatically re-compile all new code alongside our testing utilities, then run the tests.

        Next, define the run environment.

        As with the test environment, we will start with a Debian Jessie operating system image and install a C++ compiler. Unlike the test environment, we no longer need to install the testing library. We will also need to set the default behavior of the environment to run the code.

        To accomplish these steps, add the following code to a file called **Dockerfile**:

        .. literalinclude:: ../../../example/cpp/hello/Dockerfile

        At the end of the **Dockerfile** environment, it calls a script called **run.sh**. This script should compile all the code that needs to be run then run that code inside of the run environment.

        Add the following code to a file called **run.sh**:

        .. literalinclude:: ../../../example/cpp/hello/run.sh

        Now when we run our code, we will automatically re-compile all new code alongside our production utilities, then run the final binary.
        
        :subscript:`(Note: in a real production environment, you are usually better off using a runtime environment with minimal dependencies and running a pre-built executable. However, this is beyond the scope of Hello, World!)`

        The **test.sh** and **run.sh** scripts need to be executable, so give them execute permissions:
        ::
          chmod +x *.sh

    .. tab:: Python 

        First, define the test environment.

        We will start with a Debian Jessie operating system with Python 3.6 already installed, then install a testing library (pytest), and set the default behavior of the environment to run tests.

        To accomplish these steps, add the following code to a file called **Dockerfile.test**:

        .. literalinclude:: ../../../example/python/hello/Dockerfile.test

        At the end of the **Dockerfile.test** environment, it calls Python to run pytest on our project.

        Next, define the run environment.

        As with the test environment, we will start with a Debian Jessie operating system with Python 3.6 already installed. In this case, we have no external dependencies, so set the default behavior of the run environment to run Python on our **hello.py** entrypoint.

        To accomplish these steps, add the following code to a file called **Dockerfile**:

        .. literalinclude:: ../../../example/python/hello/Dockerfile

    .. tab:: Go

        First, define the test environment. 

        We will start with a Debian Jessie operating system with Go already installed, then set the working directory and *GOPATH* environment variable to **/floop**, which is where our source code will be stored inside the Docker container on the target device, and finally set the default behavior of the environment to run the tests.

        To accomplish these steps, add the following to a file called **Dockerfile.test**:

        .. literalinclude:: ../../../example/go/hello/Dockerfile.test

        Next, define the run environment.

        As with the test environment, we will start with a Debian Jessie operating system image with Go already installed. We will set the working directory and *GOPATH* then set the default behavior of the environment to run the *main* routine.

        To accomplish these steps, add the following to a file called **Dockerfile**:

        .. literalinclude:: ../../../example/go/hello/Dockerfile


    Now we are ready to build, test, and run our app with floop.

4. Configure the App with Floop
===============================
floop reads all project configuration from a single JSON configuration file. This configuration defines the details of source code, core network addresses, and initial authentication details.

We will use floop in order to generate a default configuration template and then modify that template to match our core and network configuration.

From within the **project** folder, run:
::
    floop config

This will generate a default configuration called **floop.json**.

This configuration is based on the following default values (this is a Python dictionary that gets written to JSON):

.. literalinclude:: ../../../floopcli/config.py
    :lines: 10-39

:subscript:`(Note: The calls to the *which* function automatically set the path of docker-machine and rsync as they are installed on your system. If needed, you can edit floop.json to set the paths to each binary dependency. This may be useful if you need to use a different version of docker-machine or rsync than the default version for your system.)`

From this we can describe the default configuration in plain language. 

All groups use the same rsync and docker-machine binaries. We define one group called *group0*. All cores in *group0* look to the *host_source* directory as their source code directory on the host. Within *group0* there is one core called *core0* that we can reach at its *address* using SSH access via the *user* and *host_key* on the host. When using floop, the *host_source* for *group0* will be pushed to *target_source* on *core0*. When floop builds the the build and run environment on the target, it uses the *build_file* in the *host_source* folder, which appears as the *build_file* for the *target_source* on the target. The same is true for the *test_file* when floop builds the test environment. Both *build_file* and *test_file* are relative file names inside the *host_source* and the *target_source*.

The *privileged*, *host_network*, *hardware_devices* and *docker_socket* key-values are advanced options. **For the sake of this tutorial, you can leave the default configuration for these options.**

In case you are interested, these key-values configure how floop works with Docker on the target operating system. 

The *privileged* option is equivalent to the **--privileged** flag for Docker. The *privileged* option needs to be enabled in order for *host_network*, *hardware_devices* and/or *docker_socket* to have any effect. 

The *host_network* option is equivalent to the **--net=host** option for Docker. This option allows floop to control target operating system networking through Docker. 

The *hardware_devices* key-values takes a list of file paths to Linux **/dev/** entries for valid hardware peripherals attached to the target device. For each hardware device in the list, floop adds the **--device** flag when running Docker. This allows floop to access hardware peripherals like I2C and GPIO sensors from within Docker. By default, floop expects no hardware devices. 

The *docker_socket* is the path to the target operating system Docker socket. If *docker_socket* is an empty string, then the value is ignored. If *docker_socket* is not an empty string, then floop tries to share *docker_socket* into the container running on each target device. This allows floop to call Docker (and Docker Compose, if installed inside a container) from inside of a container.

For all configurations, floop uses a compact configuration format that defines *default* key-values for groups and cores. A **group** is a collection of **cores**. A **core** runs an operating system. floop automatically flattens the configuration file as follows:
    - *default* key-values for **groups** become key-values for all groups
    - *default* key-values for **cores** become key-values for all cores in a group
    - key-values for specific cores overwrite key-values defined as *default* (for example, if you define *host_source* within *core0* then that will overwrite the *host_source* defined in *default*)

You must always define *default* for groups and cores, even if these objects are empty. Each group must have one or more cores.

Applying the flattening procedure to the default configuration reveals that it defines a single core called *core0* that belongs to the group *group0*. The flattened configuration is:
::
    [
        {
            'host_source': './', 
            'build_file' : 'Dockerfile',
            'test_file' : 'Dockerfile.test',
            'core': 'core0', 
            'address': '192.168.1.100', 
            'host_docker_machine_bin': '/usr/local/bin/docker-machine', 
            'host_key': '~/.ssh/id_rsa', 
            'group': 'group0', 
            'target_source': '/home/floop/floop/', 
            'host_rsync_bin': '/usr/bin/rsync', 
            'user': 'floop',
            'privileged' : False,
            'host_network' : False,
            'docker_socket' : '/var/run/docker.sock',
            'hardware_devices' : []
        }
    ]

The flattened configuration will be a list with as many items as cores. You can add more cores by modifying the configuration file.

When you run floop, it will automatically copy code from *host_source* to *target_source* on each target. For this guide, you should change *target_source* depending on whether you are using Docker Machines on your host or hardware ARM cores.

.. tabs::

    .. tab:: ARM Cores 

        This is the option for using floop with real cores.

        For ARM cores, you need to update each entry in *cores*. For example, if you have a target core that you want to call *core0* that can be reached at IP address **192.168.188** and that core runs an operating system that has a user called *floop* (with corresponding user directory **/home/floop/**) who uses **~/.ssh/floop.key** to SSH into your core, then you would configure floop as follows:
        ::
          ... # only showing core0 
          "core0" : {
              "target_source' : '/home/floop/floop/",
              "address' : '192.168.1.188", 
              "user' : 'floop",             
              "host_key' : '~/.ssh/floop.key", 
          } 

        If you have more than one ARM core, then make sure to add entries to the *cores* list, changing the values to match your specific core.

    .. tab:: Docker Machines 

        This is the option for testing or evaluating floop before you use it with real cores.

        For Docker Machines on the host, if you have one existing Docker Machine called *core0* then the default configuration should work for you. If you have more than one Docker Machine, then you should add more cores to the configuration, changing the name to match the name you used when you created the cores using Docker Machine. To see existing Docker Machines on your host, use docker-machine directly to list them:
        ::

          docker-machine ls

Note that all core names and addresses must be unique. 

You are now ready to start communicating with target devices. Make sure that you run the following floop commands from the **project** folder you made for this guide.

5. Create Floop Target Cores
==============================

Once you have a configuration file that defines your cores, you can create new floop cores by running:
::

  floop create

Optionally, you can add the *-v* flag to see what floop is doing under the hood to establish communication with your remote cores and handle encrypted authentication.

If you see any errors, follow the help messages that floop provides. Make sure that you have defined valid cores and that you have network access to those cores.

6. Push Code from Host to Targets
=================================
Once you have successfully created one or more floop cores, you can push code from your configured *host_source* to *target_source* by running:
::

  floop push

:subscript:`(Note: communication between the host and targets runs in parallel so floop works on all targets at the same time)`

Optionally, you can add the *-v* flag to see how floop uses rsync to synchronize the code between the host and all targets to ensure that the source and target are the same.

Your code is now on all of your targets so we can build, run, or test it.

7. Build Code on Targets
========================
In order to build your code on all of your targets, you can run:
::

  floop build

:subscript:`(Note: build uses Docker under the hood, so all builds are cached. This means that first build usually takes much longer than subsequent builds.)``

Optionally, you can add the *-v* flag to see that floop always pushes before a build then builds your run environment using the *build_file* in the *target_source* for each core that builds your app. 

8. Test Code on Targets
=======================
You can run your test environment for your app by running:
::

  floop test

Optionally, you can add the *-v* flag to see that floop always pushes and always builds and runs the test environment using the *test_file* in the *target_source* for each core that tests your app your app.  

You should see your tests run on all targets.

9. Run Code on Targets
======================
You can run your run environment for your app by running:
::

  floop run 

Optionally, you can add the *-v* flag to see that floop always pushes and always builds and runs the run environment using the *build_file* in the *target_source* for each core that builds your app.

You should see all targets greet you with "Hello, World!"

10. Monitor Running or Testing Code on Targets
==============================================
If you have long-running tests or scripts that run indefinitely, you can check on all testing or running code on all targets by running:
::
 
  floop ps

Optionally, you can add the *-v* flag to see that floop calls Docker on all targets to determine which tests or runs are still running.

11. Log All Floop Events
========================
Once you push, build, test, and/or run code on your targets, you can see the logs from all targets directly on your host by running:
::

  floop logs

:subscript:`(Note: floop stores logs for each project in a file called floop.log in the root project folder. The logs contain sucessful commands as well as all errors messages.)`

Optionally, you can add the *-m* flag followed by a *match-term* to show only the lines of the log that contain *match-term*. 

For example, to show all lines that contain the term **TEST PASSED** you can run:
::

  floop logs -m "TEST PASSED"

12. Destroy Floop Target Cores
================================
When you are finished with this guide, you can destroy all the floop cores defined in your configuration file by running:
::

  floop destroy

:subscript:`(Note: floop destroy cores. It does NOT remove your project from your host.)`

Optionally, you can add the *-v* flag to see that floop destroys cores by removing Docker Machines from the host. This leaves the *target_source* directory on the target device. This also leaves Docker installed on the target device.

If you followed this guide using more than one ARM core or Docker Machine, you may only want to destroy some of the floop cores you created before. In order to do this, you can remove all of the cores you want to destroy from your **floop.json** and add them to a new configuration file called **floop-destroy.json**. You can then destroy those cores using the *-c* flag for the floop command by running:
::

  floop -c floop-destroy.json destroy

This will destroy the cores defined in **floop-destroy.json** while leaving the remaining cores in **floop.json** untouched.

For more information about how to use floop, check the :doc:`best`.
