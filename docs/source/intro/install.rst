.. _intro-install:

==================
Installation Guide
==================

Overview
========
floop is a command-line interface built in Python. The tool uses Docker, Docker Machine, and rsync to manage all host-target communication.

Supported Operating Systems
===========================

Check out the :doc:`os` to learn more about how to configure the operating systems on your target devices to enable floop.

floop currently supports operating systems that have a bash shell and support virtualization.

Install Prerequisites
=====================
Install `Docker Machine <https://docs.docker.com/machine/install-machine/>`_
    Docker Machine builds virtual operating system environments on remote servers. floop uses Docker Machine to establish network communication between the host and your targets. During build, run, and test phases for development, Docker Machine handles all SSH authentication and in-transit encryption between host and targets.
Install `rsync <https://git.samba.org/rsync.git>`_
    rsync synchronizes folders and files between networked devices. floop uses rsync to ensure that host source code and target source code are the same. When using floop, all rsync communication is one-way from the host to the targets. This means that manually changing code on the targets will not affect code on the host.
    
    rsync is probably known to your package manager, e.g.:
.. code-block:: bash 

    sudo apt-get update && sudo apt-get install rsync # Debian/Ubuntu
    sudo yum install rsync                            # CentOS
    brew install rsync                                # macOS/OSX

Install floop
=============
floop can be installed via `pip <https://pip.pypa.io/en/stable/installing/>`_, where it is known as `floopcli <https://pypi.org/project/floopcli>`_:
::    
    pip install floopcli

This will install a floop executable binary on your host system.

Test that floop installation succeeded:
::
    floop --version

If you see no error messages, you successfully installed floop.
