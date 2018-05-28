.. _intro-os:

====================================
Target Device Operating System Guide
====================================

Overview
========
floop works with target devices that run a large variety of operating systems. In this guide, you will:
 - learn the minimum requirements for a target OS to work with floop
 - learn how to configure an existing target OS for use with floop
 - reuse the configured target OS for other devices

Minimum Requirements to Use floop
====================================
Target operating systems must meet the following requirements:
 - Linux kernel version 3.10 or higher (to install and run Docker)
 - Non-root user with passwordless sudo (to install Docker)
 - SSH access for the above non-root user (to create Docker Machine)

Configuring a Target Operating System to Meet Minimum Requirements
=====================================================================
You should only need to do the following for each base operating system one time.


Here we show how to configure a Debian or Ubuntu-like target operating system for use with floop. This has been tested on `Armbian Mainline Kernel for Orange Pi Zero <https://www.armbian.com/orange-pi-zero/>`_.

First, boot your operating system on your target then get access to a terminal on the device either via serial connection or SSH. This will depend on your actual hardware and base operating system image. Here we assume your operating system starts you as the root user.

Once you have access to a terminal, check your kernel version on the **target** by running:
::

 uname -r

You should see a version number that looks something like 4.13.0. If this version number is above 3.10, then your operating system should support the proper virtualization.

Next, you should install sudo and an SSH server on the **target**:
::

  apt-get update && apt-get install -y sudo openssh-server

Next, you should make a new user that floop can use with sudo permissions. We recommend you create a user called floop. You can do this on the **target** by running:
::

  adduser floop sudo 

Next, create a docker group and add the floop user to group so floop can call Docker;
::

  groupadd docker && usermod -aG docker floop

Next, you should give your user permission to run sudo without a password. You can do this by adding a line in **/etc/sudoers** on the **target** by running:
::
 
  sudo echo "floop  ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

If you have a base operating system where you do not start as the root user, you may need to prepend *sudo* to some of the commands above and supply a password. 

Next, make sure that your floop user has passwordless SSH access from your **host**. Do this on the **target** by running:
::

  sed -ri 's/^PermitRootLogin\s+.*/PermitRootLogin no/' /etc/ssh/sshd_config && \
  sed -ri 's/^AuthorizedKeysFile\s+.*/AuthorizedKeysFile %\/.ssh\/authorized_keys/' /etc/ssh/sshd_config && \
  sed -ri 's/^#PasswordAuthentication\s+.*/PasswordAuthentication no/' /etc/ssh/sshd_config && \
  sed -ri 's/^#UsePAM\s+.*/UsePAM yes/' /etc/ssh/sshd_config

On your **host**, if you do not already have an SSH key, then generate a new one by running:
::
 
  ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa

Copy and paste the contents of the host file **~/.ssh/id_rsa.pub** to the target file **/home/floop/.ssh/authorized_keys**.

You can test that your sudo and SSH configuration changes succeeded by running the following from the **host**:
::

  ssh -i ~/.ssh/id_rsa \
  floop@your.device.ip.address \
  sudo tail -1 /etc/sudoers

You should change *your.device.ip.address* to the IP address of your target device on a network that your host can access.

If you see the line you added above to permit passwordless sudo, then your sudo configuration succeeded.

If you are working with `Raspbian <https://www.raspbian.org/>`_, then you may need to perform the following additional step. You need to change the distribution ID from *raspbian* to *debian* so docker-machine recognizes that you are running a Debian-based operating system. You can do this by running the following command from your **host**:
::
  
  ssh -i ~/.ssh/id_rsa \
  floop@your.device.ip.address \
  sed -ri 's/ID=raspbian/ID=debian/g' /etc/os-release

Your operating system is now configured so that it can be used with floop. From your host, you can make a disk image of the configured operating system and copy that image and run it on other devices.

For more options (not requirements) for configuring your target operating system, check the :doc:`best`
