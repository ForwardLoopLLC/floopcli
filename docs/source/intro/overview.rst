.. _intro-overview:

========
Overview
========
floop is a tool for standardizing code development between a host device and one or more target test devices. floop lets developers write code on one machine and test that same code on many devices at once. This has many applications, including prototyping, developing, and testing sensors and IoT devices.

See floop in action here:

.. image:: https://img.youtube.com/vi/rT3D8THxBn4/0.jpg
   :target: https://www.youtube.com/watch?v=rT3D8THxBn4

When to Use Floop
=================
floop is designed to work with target devices that run an operating system such as Ubuntu, Debian, Raspbian, or Armbian. The tool is mainly for developers who want to develop code using their normal workflow and then test that same code on a wide range of devices all at the same time. 

Currently, floop does not support firmware-based devices. floop looks to support the next generation of OS-based edge computing devices, such as Orange Pi, Raspberry Pi, BeagleBone Black, and NanoPi NEO. Over time we may start to add support for common firmware-based devices such as ESP8266 and STM32. 

How to Use Floop
================
floop is intended for development and testing. In the future, we may offer support for deployment on existing infrastructure, such as AWS, Azure, Google Cloud, Alicloud, and IBM Cloud.

floop aims to be a lightweight, project-specific build and test tool. Each new project has its own floop.json configuration, a Dockerfile for building and running code, and a Dockerfile.test for building and testing code. Additionally, all logging is project-specific, meaning that all floop logs are stored alongside your source code. This makes debugging and reproducing errors faster and easier so they can be fixed in less time.

Why Use Floop
================
floop automates and standardizes network communication, authentication, source code synchronization, and build, run, and test logs all in one place. It gives developers the ability to write code in one place and test it on many different target devices simultaneously.

floop uses Docker on all target devices to standardize build and testing environments. This lets developers spend less time configuring hardware and operating system settings for individual devices and more time developing and testing applications.
