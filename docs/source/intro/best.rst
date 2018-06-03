.. _intro-best:

===================
Best Practice Guide
===================

Overview
========
This guide introduces best practice guidelines for using floop to maximize developer efficiency and code portability while minimizing hardware dependence and cross-platform bugs.

General
=======

Use floop for dev, not prod
---------------------------
floop is currently meant for prototyping, developing, and testing applications quickly. When it comes to deploying target devices, you will want a production environment with more infrastructure. Stay tuned for more information about integrating floop with cloud IoT platforms.

Target Operating System
=======================

Add a Dedicated floop User to Target Device Operating Systems
-------------------------------------------------------------
Each target device operating system you use should have a user with SSH access and passwordless sudo. To reduce security concerns and to improve transparency of logging, you should only use this user for floop-related communication. We recommend naming the user *floop* and associating *floop* with an SSH key that only the *floop* user will use. 


Give Target Operating Systems a Unique Identifier on First Boot
---------------------------------------------------------------
If you work with many target devices, it can be useful to have a unique identifier for each device. You can specify an identifier at the operating system level for your base image by removing the operating system *machine-id* and telling the operating system to generate a new *machine-id* on first boot. You can do this by running the following on your **target**:
::

  sudo rm -f /etc/machine-id && \
  sudo rm -f /var/lib/dbus/machine-id

Then change the file **/etc/rc.local** on the target so it ends with the following:
::

  if [ ! -f /etc/machine-id ]; then
      dbus-uuidgen --ensure
      systemd-machine-id-setup
  fi
  exit 0


Now you can unplug power to your target device, copy the target operating system to your host device, and burn that operating system to multiple SD cards for multiple targets. When each target boots up the first time, it will automatically generate a new, unique *machine-id* in **/etc/machine-id**.

Applications and Dockerfiles
============================

Use Docker Images for Your Version of ARM
-----------------------------------------
When working with ARM targets, you should always base your **Dockerfile.test** and **Dockerfile** environments on images that match the ARM version of your target hardware operating system. 

.. tabs::

  .. tab:: ARMv7

    This works for Armbian on Orange Pi.

    For ARMv7, you should use images from the `Docker Hub Library <https://hub.docker.com/u/library/>`_. These images `work across platforms <https://blog.docker.com/2017/09/docker-official-images-now-multi-platform/>`_, including x86 and ARMv7. It is not guaranteed that other base images will build correctly on ARMv7 hardware. In practice, this means that all Dockerfiles for all ARMv7 devices should start with:
    ::
        FROM library/...

    If you need a language or environment that is not provided as a *library* image, you can often build one yourself by installing on a base image such as **library/debian**.

  .. tab:: ARMv6

    This works for Raspbian on Raspberry Pi.

    For ARMv6 images, you should use images from the `arm32v6 Library <https://hub.docker.com/u/arm32v6/>`_. These images only work for ARMv6 devices. In practice, this means that all Dockerfiles for all ARMv7 devices should start with:
    ::
        FROM arm32v6/...
