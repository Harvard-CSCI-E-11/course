Changes from 2025 to 2026
=========================
* We migrated from Ubuntu 24.04 to Ubuntu 26.04 LTS
* We migrated from Python 3.13 to Python 3.14.
* We migrated from `poetry` to `uv` as our package manager.
* [lab7](Lab_7.md) and [lab8](Lab_8.md) were rewritten to use a Raspberry PI to address continuing device availability problems with the Adafruit MEMENTO.
* [lab7](Lab_7.md) and [lab8](Lab_8.md) now use Python3.14 no longer use Circuit Python.

Changes from 2024-2025
======================
* We moved from AWS Linux to Ubuntu 24.04 Linux. We did this because there are more online tutorials for Ubuntu Linux than for AWS Linux, and because Ubuntu Linux is available on more platforms (e.g. Raspberry PI or [MacOS](https://dev.to/ryfazrin/how-to-run-ubuntu-on-macos-like-wsl-wsl-style-experience-4cd4)).
* We have a script [etc/install-e11](../etc/install-e11) that configures for the class
* We created a new command, `e11`, for course VM management.
* We now use [`pipx`](https://pipx.pypa.io/latest/) to manage python commands in the CLI (including e11)
* The old lab2 (a library-based assigment) was removed.
* The old [lab3](https://github.com/Harvard-CSCI-E-11/spring25/tree/main/lab3) which involved standing up a database-driven website with a SQL injection vulnerability was changed into two labs:
  - [lab2](Lab_2.md) [A web server with password-based access control](https://docs.google.com/document/d/1-3Wrh1coGqYvgfIbGvei8lw3XJQod85zzuvfdMStsvs/edit?tab=t.0)
  - [lab3](Lab_3.md) [A simple database-driven web app written in python](https://docs.google.com/document/d/1pOeS03gJRGaUTezjs4-K6loY3SoVx4xRYk6Prj7WClU/edit?tab=t.0)
* The old [lab5](https://github.com/Harvard-CSCI-E-11/spring25/tree/main/lab5) which involved creating a system that allowed uploading images and then feeding them through Amazon Rekognition has been split into two labs:
  - [lab5](Lab_5.md) [Add images to your message board](https://docs.google.com/document/d/1CW48xvpbEE9xPs_6_2cQjOQ4A7xvWgoWCEMgkPjNDuc/edit?usp=drive_web&ouid=114142951656037982317)
  - [lab6](Lab_6.md) [AI image analysis with AWS Rekognition](https://docs.google.com/document/d/1aRFFRaWmMrmgn3ONQDGhYghC-823GbGzAP-7qdt5E0U/edit?tab=t.0)
* Because the labs are now graded asynchronously, the results are stored in a database, and the VMs are configured to re-reigster themselves on boot and get new DNS names for their new IP addresses, there is no need for students to leave the VMs running all the time.
