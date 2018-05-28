.. _intro-best:

===================
Best Practice Guide
===================

Overview
========
This guide introduces best practice guidelines for using floop to maximize developer efficiency and code portability while minimizing hardware dependence and cross-platform bugs.

Use floop for dev, not prod
---------------------------
floop is currently meant for prototyping, developing, and testing applications quickly. When it comes to deploying target devices, you will want a production environment with more infrastructure. Stay tuned for more information about integrating floop with cloud IoT platforms.

Add a Dedicated floop User to Target Device Operating Systems
-------------------------------------------------------------
Each target device operating system you use should have a user with SSH access and passwordless sudo. To reduce security concerns and to improve transparency of logging, you should only use this user for floop-related communication. We recommend naming the user *floop* and associating *floop* with an SSH key that only the *floop* user will use. 

Use *library* Docker Images
---------------------------
When working with ARM targets, you should always base your **Dockerfile.test** and **Dockerfile** environments on images from the `Docker Hub Library <https://hub.docker.com/u/library/>`_. These images `work across platforms <https://blog.docker.com/2017/09/docker-official-images-now-multi-platform/>`_, including x86 and ARM. It is not guaranteed that other base images will build correctly on ARM hardware. In practice, this means that all Dockerfiles should start with:
::
    FROM library/...

If you need a language or environment that is not provided as a *library* image, you can often build one yourself by installing on a base image such as **library/debian**.
