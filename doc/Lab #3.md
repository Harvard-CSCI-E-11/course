# **![][image1]**

# **CSCI E-11: Artificial Intelligence, the Internet-of-Things, and Cybersecurity** **Harvard Extension School** **Spring 2027**

# **Lab \#3 \- Lookup Grades — A simple database-driven web app written in python**

[Introduction and Lab Objectives](#introduction-and-lab-objectives)

[Building on Lab 2](#building-on-lab-2)

[Getting Started — First Read The Docs\!](#getting-started-—-first-read-the-docs!)

[Add Another Name to Your TLS certificate](#add-another-name-to-your-tls-certificate)

[Expanding your certificate](#expanding-your-certificate)

[Poetry: A modern Python package manager](#poetry:-a-modern-python-package-manager)

[Making Poetry work with lab 3](#making-poetry-work-with-lab-3)

[Running a simple Flask application from the command line](#running-a-simple-flask-application-from-the-command-line)

[Running a flask application from gunicorn](#running-a-flask-application-from-gunicorn)

[Understanding the difference between “start” and “enable”](#understanding-the-difference-between-“start”-and-“enable”)

[Setting up the nginx reverse proxy](#setting-up-the-nginx-reverse-proxy)

[Creating a Student Database and Installing the Vulnerable Database Application](#creating-a-student-database-and-installing-the-vulnerable-database-application)

[The Right Starting Place](#the-right-starting-place)

[Creating the student database](#creating-the-student-database)

[Installing the vulnerable app](#installing-the-vulnerable-app)

[Test your web application](#test-your-web-application)

[Test with normal code](#test-with-normal-code)

[Demonstrate the vulnerability](#demonstrate-the-vulnerability)

[Debugging](#debugging)

[Learn about Prepared Statements](#learn-about-prepared-statements)

[Get an A: Fix your app](#get-an-a:-fix-your-app)

[Using the e11 command](#using-the-e11-command)

[Going Further](#going-further)

# **Introduction and Lab Objectives** {#introduction-and-lab-objectives}

Welcome to the third lab\! We will continue to use Amazon Web Services for our labs.

Objectives for this lab:

* Add a second website to your web server.
* Certificate \- Expand your Let’s Encrypt certificate to include a second website.
* Poetry \- Install the Poetry python environment
* Flask \- Install Flask to allow for applications to run on your web server.
* Add a Reverse Proxy to allow your one server to host multiple websites
* Deploy a simple application that performs a simple database lookup. **NOTE:** The code we give you contains an SQL injection vulnerability\! (You have to fix it.)

What will be graded by e11:

* The second website running on port 443
* The TLS certificate properly expanded
* The database-driven application running
* The SQL injection vulnerability corrected

# **Building on Lab 2** {#building-on-lab-2}

This assignment builds on the instance created in Lab 1 and 2\. If you stopped it, now is a good time to restart it. If you terminated the instance please create a new one and re-run the installer and re-register the server with the E11 course management system.

In Lab 2 we created a TLS certificate for *smashedemail.csci-e-11.org* and added support for that certificate to the nginx web server.

Lab 3 builds upon Lab 2, but you will find new files in the [lab3 folder of the git repo](https://github.com/Harvard-CSCI-E-11/spring27/tree/main/lab3/):

	lab3/Makefile — a Makefile with new targets

	lab3/README.md — describes some of what’s different

	lab3/lab3.service-simple\_flask\_application — A Linux service for your first flask application that serves the application on port 8003\.

	lab3/lab3.service-student\_server — A Linux service for your second flask application that also serves the application on port 8003\. You can only run one server at a time\!

	lab3/lab3-nginx-patch — The changes you will make to the nginx configuration file to pass through requests to the gunicorn server running on port 8003

	lab3/simple\_flask\_application.py — The simple flask application

	lab3/student\_server.py —The student server

# **Getting Started — First Read The Docs\!** {#getting-started-—-first-read-the-docs!}

This assignment assumes some familiarity with HTTP, TLS, SQL and Python. We are providing you with these resources that you might want to read first:

Python Poetry and Flask:

* [Introduction | Documentation | Poetry \- Python dependency management and packaging made easy](https://python-poetry.org/docs/)
* [Flask](https://flask.palletsprojects.com/en/stable/)

Using nginx and gunicorn to serve a python application over HTTP:

* [NGINX Reverse Proxy | NGINX Documentation](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/)
* [Deploying Gunicorn \- Nginx Configuration](https://docs.gunicorn.org/en/latest/deploy.html)

Docs about SQL Injection:

* [xkcd: Exploits of a Mom](https://xkcd.com/327/)
* [327: Exploits of a Mom \- explain xkcd](https://www.explainxkcd.com/wiki/index.php/327:_Exploits_of_a_Mom)
* [SQL injection \- Wikipedia](https://en.wikipedia.org/wiki/SQL_injection)

Try out SQL injection attacks here: [SQL Injection (W3Cshools)](https://www.w3schools.com/sql/sql_injection.asp)

# **Add Another Name to Your TLS certificate** {#add-another-name-to-your-tls-certificate}

In Lab 2 you set the hostname of your instance to be *smashedemail*.csci-e-11.org*,* where  *smashedemail* is somehow related to your email address.

However, when we created that DNS name for you in the csci-e-11.org domain, for you, we actually created several other DNSs, all pointing to the same IP address:

*smashedemail*.csci-e-11.org

*smashedemail*\-lab1.csci-e-11.org

*smashedemail*\-lab2.csci-e-11.org

*smashedemail*\-lab3.csci-e-11.org

*smashedemail*\-lab4.csci-e-11.org

*smashedemail*\-lab5.csci-e-11.org

*smashedemail*\-lab6.csci-e-11.org

Each of these DNS entries have the same IP address. You will now configure your web server so that it serves different pages for each domain name. These domain names are sometimes called “virtual hosts” because they are not all different physical hosts. We will now configure the webserver so support these four additional virtual hosts, and then tell the Let’s Encrypt certbot to give each one its own public key server certificate.

Start off by going to your first home page:

https://*smashedemail*.csci-e-11.org

This page should still work. If it doesn’t, check your nginx configuration file. If necessary, restore your backup.

Now look at this page:

https://*smashedemail-lab3*.csci-e-11.org

You should see a certificate error:

![][image2]

That’s because the original certificate was just fo*r [https://smashedemail.csci-e-11.org](https://smashedemail.csci-e-11.org)* and not for [*https://smashedemail-lab3.csci-e-11.org*](https://smashedemail-lab3.csci-e-11.org). If you override the warning (via the *Advanced* button) you’ll see your original default page for the first domain:

![][image3]

The first thing you need to do now is to extend the certificate to include the new domain name. Then you need to extend the web server.

You will find some files to help you get started installed at /home/ubuntu/course/lab3/.

## **Expanding your certificate** {#expanding-your-certificate}

The openssl command allows you to perform many cryptographic operations from the command line.

Below, we use the command to examine the server certificate. Try this example with your server certificate host and server certificate by changing **sgarfinkelfas** to your **smashedmail**.

$ **openssl s\_client \-host sgarfinkelfas.csci-e-11.org \-port 443 \</dev/null | openssl x509 \-noout \-text**

You will see output similar to the following. Your certificate will have slightly different values, of course\!

depth=2 C \= US, O \= Internet Security Research Group, CN \= ISRG Root X1
verify return:1
depth=1 C \= US, O \= Let's Encrypt, CN \= E5
verify return:1
depth=0 CN \= sgarfinkelfas.csci-e-11.org
verify return:1
DONE
Certificate:
    Data:
        Version: 3 (0x2)
        Serial Number:
            05:da:0c:fc:df:f1:48:4d:c2:11:76:24:75:0d:54:55:8d:01
        Signature Algorithm: ecdsa-with-SHA384
        Issuer: C \= US, O \= Let's Encrypt, CN \= E5
        Validity
            Not Before: Aug 14 13:06:36 2025 GMT
            Not After : Nov 12 13:06:35 2025 GMT
        Subject: CN \= sgarfinkelfas.csci-e-11.org
        Subject Public Key Info:
            Public Key Algorithm: id-ecPublicKey
                Public-Key: (256 bit)
                pub:
                    04:40:ab:0c:a6:e1:34:4a:d7:08:b6:2f:f0:dc:47:
                    8d:54:d9:50:e6:46:db:3e:b5:63:ce:4c:ec:24:9f:
                    96:ce:e4:4f:e4:fb:e6:99:64:fc:59:55:95:e0:96:
                    f4:a5:49:38:22:6d:26:35:ca:c5:71:2f:2c:0c:72:
                    ae:e7:a6:08:82
                ASN1 OID: prime256v1
                NIST CURVE: P-256
        X509v3 extensions:
            X509v3 Key Usage: critical
                Digital Signature
            X509v3 Extended Key Usage:
                TLS Web Server Authentication, TLS Web Client Authentication
            X509v3 Basic Constraints: critical
                CA:FALSE
            X509v3 Subject Key Identifier:
                F5:E6:EC:3D:D6:30:96:B6:7C:37:F3:C3:33:88:99:A4:B7:DF:15:C0
            X509v3 Authority Key Identifier:
                9F:2B:5F:CF:3C:21:4F:9D:04:B7:ED:2B:2C:C4:C6:70:8B:D2:D7:0D
            Authority Information Access:
                CA Issuers \- URI:http://e5.i.lencr.org/
            X509v3 Subject Alternative Name:
                DNS:sgarfinkelfas.csci-e-11.org
            X509v3 Certificate Policies:
                Policy: 2.23.140.1.2.1
            X509v3 CRL Distribution Points:
                Full Name:
                  URI:http://e5.c.lencr.org/2.crl
            CT Precertificate SCTs:
                Signed Certificate Timestamp:
                    Version   : v1 (0x0)
                    Log ID    : ED:3C:4B:D6:E8:06:C2:A4:A2:00:57:DB:CB:24:E2:38:
                                01:DF:51:2F:ED:C4:86:C5:70:0F:20:DD:B7:3E:3F:E0
                    Timestamp : Aug 14 14:05:06.681 2025 GMT
                    Extensions: none
                    Signature : ecdsa-with-SHA256
                                30:44:02:20:51:97:90:F6:19:10:99:9D:38:A8:B7:FA:
                                FA:6D:2A:00:65:6C:17:EB:60:DA:4A:16:2A:B8:B2:ED:
                                CF:09:5A:ED:02:20:2E:E1:E4:84:F2:74:2D:EC:C1:76:
                                9B:F6:E1:10:3C:1D:F6:27:93:D4:98:CE:14:24:2D:28:
                                C1:6D:89:BE:7A:AA
                Signed Certificate Timestamp:
                    Version   : v1 (0x0)
                    Log ID    : 0D:E1:F2:30:2B:D3:0D:C1:40:62:12:09:EA:55:2E:FC:
                                47:74:7C:B1:D7:E9:30:EF:0E:42:1E:B4:7E:4E:AA:34
                    Timestamp : Aug 14 14:05:06.674 2025 GMT
                    Extensions: none
                    Signature : ecdsa-with-SHA256
                                30:44:02:20:68:F9:88:DC:0F:78:B3:64:EE:CA:1D:0B:
                                CE:1B:4F:A0:07:19:E8:C1:52:67:02:AC:8D:B9:AA:D0:
                                07:C1:91:68:02:20:07:94:41:78:F2:A7:EA:DF:FA:88:
                                21:78:22:E7:5F:78:97:99:26:1F:61:D3:ED:9E:51:3D:
                                18:0E:A3:84:94:33
    Signature Algorithm: ecdsa-with-SHA384
    Signature Value:
        30:64:02:30:66:f2:50:0c:27:29:2b:14:86:79:5c:68:d2:d4:
        6a:6e:64:a3:f1:cf:d4:58:34:a6:14:b8:7c:12:b2:72:f3:89:
        4e:9a:49:ac:3d:33:11:52:d9:fd:0d:70:30:6e:f3:47:02:30:
        37:5c:4c:ad:dc:33:6f:a1:fd:fa:9e:bf:bc:e4:29:59:5d:52:
        39:9e:7e:a2:5c:a1:4c:d8:1f:f2:b5:06:41:3d:0c:22:78:4c:
        60:6d:3a:e6:bc:ab:70:ba:b3:87:10:a2

Now look at the options that the certbot command gives you:

$ **certbot \-h**

You will see that you want to use the certbot \-d command to specify both the old and the new domain names:

$ **sudo certbot \-d [smashedemail.csci-e-11.org](http://smashedemail.csci-e-11.org) \-d smashedemail-lab3.csci-e-11.org**

You should see output that looks like this:

$ **sudo certbot \-d [sgarfinkelfas.csci-e-11.org](http://sgarfinkelfas.csci-e-11.org) \-d sgarfinkelfas-lab3.csci-e-11.org**
Saving debug log to /var/log/letsencrypt/letsencrypt.log

\- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \-
You have an existing certificate that contains a portion of the domains you
requested (ref: /etc/letsencrypt/renewal/sgarfinkelfas.csci-e-11.org.conf)

It contains these names: sgarfinkelfas.csci-e-11.org

You requested these names for the new certificate: sgarfinkelfas.csci-e-11.org,
sgarfinkelfas-lab3.csci-e-11.org.

Do you want to expand and replace this existing certificate with the new
certificate?
\- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \-
(E)xpand/(C)ancel: **E**
Renewing an existing certificate for sgarfinkelfas.csci-e-11.org and sgarfinkelfas-lab3.csci-e-11.org

Successfully received certificate.
Certificate is saved at: /etc/letsencrypt/live/sgarfinkelfas.csci-e-11.org/fullchain.pem
Key is saved at:         /etc/letsencrypt/live/sgarfinkelfas.csci-e-11.org/privkey.pem
This certificate expires on 2025-11-12.
These files will be updated when the certificate renews.
Certbot has set up a scheduled task to automatically renew this certificate in the background.

Deploying certificate
Successfully deployed certificate for sgarfinkelfas.csci-e-11.org to /etc/nginx/sites-enabled/default
Successfully deployed certificate for sgarfinkelfas-lab3.csci-e-11.org to /etc/nginx/sites-enabled/default
Your existing certificate has been successfully renewed, and the new certificate has been installed.

\- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \-
If you like Certbot, please consider supporting our work by:
 \* Donating to ISRG / Let's Encrypt:   https://letsencrypt.org/donate
 \* Donating to EFF:                    https://eff.org/donate-le
\- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \- \-
$

Notice:

* There are now two names on the certificate.
* Both sites have been deployed to the file /etc/nginx/sites-enabled/default (which itself is a symbolic link to /etc/nginx/sites-available/default).

Now look at the default file:

$ **more /etc/nginx/sites-enabled/default**

You will see that there are five blocks that begin with this line:

server {

Each of these blocks is a server control block:

* The first creates the default server that listens on port 80\.
* The second creates the TLS server on port 443 with the name [smashedemail.csci-e-11.org](http://sgarfinkelfas.csci-e-11.org).
* The third creates a server on port 80 for the name [smashedemail.csci-e-11.org](http://sgarfinkelfas.csci-e-11.org) that redirects to [https://smashedemail.csci-e-11.org/](https://sgarfinkelfas.csci-e-11.org/)
* The fourth creates a TLS server on port 443 with the name [smashedemail-lab3.csci-e-11.org](http://sgarfinkelfas-lab3.csci-e-11.org).
* The fifth creates a server on port 80 for the name [smashedemail-lab3.csci-e-11.org](http://sgarfinkelfas.csci-e-11.org) that redirects to [https://smashedemail-lab3.csci-e-11.org/](https://sgarfinkelfas.csci-e-11.org/)

Restart the nginx webserver and test your certificate:

$ **sudo systemctl daemon-reload**

$ **sudo systemctl restart nginx.service**

Now use **openssl** to look at the certificate again and you will see that there are two names:

            X509v3 Subject Alternative Name:
                DNS:smashedemail-lab3.csci-e-11.org, DNS:smashedemail.csci-e-11.org

Restart your web browser and go to the website. You should see the same web page, but the certificate error should be gone. (If you had previously “clicked through” the security warning via the *Advanced* button, subsequent accesses might not repeat the full-page warning, but rather display a small *Not secure* or similar tag near the URL. You should not be seeing that now, either.)l

#

# **Poetry: A modern Python package manager** {#poetry:-a-modern-python-package-manager}

In this class we will be using the Poetry package manager to manage a different Python virtual environment for each lab. Poetry combines aspects of the [venv](https://docs.python.org/3/library/venv.html) module and [pip](https://pypi.org/project/pip/) installer, but is significantly faster and more powerful than both.

The e11 installer install-e11 installed poetry and configured it so that python virtual environments would be stored in a directory called .venv within each project directory. The leading “.” makes the directory invisible when you type ls \-l; to see it you need to type ls \-la (the ‘a’ is for “all”).

## **Making Poetry work with lab 3** {#making-poetry-work-with-lab-3}

The Poetry projects for this class are all set up, but you do need to activate the environments. To get started with lab 3, type these commands. (At the end of the second and third lines are comments, introduced by the comment character \#. These are present for your benefit; you do not need to type them.)

$ **cd \~/course/lab3**
$ **poetry install**		   \# install the dependencies
$ **source .venv/bin/activate** \# activate the virtual environment, setting PATH and prompt

# **Running a simple Flask application from the command line** {#running-a-simple-flask-application-from-the-command-line}

Flask is a framework for creating Python web applications. It is widely used. You can learn about it here: [Flask](https://flask.palletsprojects.com/en/stable/)

In the lab3 directory we have given you two simple flask applications:

* simple\_flask\_application.py — prints **Hello from Flask\!** in the web browser
* student\_database.py — A simple web-based application for searching a student database in a local SQLite web server.

Here are the contents of the simple flask application:

\# simple\_flask\_application.py
\#
from flask import Flask

app \= Flask(\_\_name\_\_)

@app.route('/')
def index():
    return "\<h1\>Hello from Flask\!\</h1\>\\n"

if \_\_name\_\_ \== '\_\_main\_\_':
    app.run(host='127.0.0.1', port=5000)

\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#

That’s pretty simple\! The @app.route('/') statement routes a single web page (called “/”) and makes it display the HTML snippet.

We can run this application from the Linux command line using this command:

$ **flask \--app simple\_flask\_application:app run \--reload \--port=8003**

Now, in another window (which you can open by doing another *Connect* from AWS), you can test the application with the curl command, which fetches a URL and displays the results:

$ **curl http://localhost:8003/**
\<h1\>Hello from Flask\!\</h1\>
$

One of the main uses of curl is for debugging. For example, we can view the full HTTP headers by adding the \-D \- option.:

$ **curl \-D \- http://localhost:8003/**
HTTP/1.1 200 OK
Server: Werkzeug/3.1.3 Python/3.12.3
Date: Thu, 14 Aug 2025 23:23:21 GMT
Content-Type: text/html; charset=utf-8
Content-Length: 27
Connection: close

\<h1\>Hello from Flask\!\</h1\>
$

Note the line that states Server: Werkzeug/3.1.3 Python/3.12.3.

* Werkzeug is German for “tool.” The Werkzeug Python package provides core services for Flask. You can find more information about it on the [PyPI Werkzeug page](https://pypi.org/project/Werkzeug/).
* Werkzeug/3.1.3 here means that we are using Werkzeug version 3.1.3.
* Python/3.14.x here means that we are running under Python 3.14

As both a security and a software professional (and nowadays you can’t be one without being the other as well), you should get in the habit of looking at version numbers like this and asking yourself questions like:

* Is this the most recent version of the software package?
* Does this version have any vulnerabilities?
* Is it possible to upgrade the version without any other software changes?
* Where did the software come from? How do I *know* that I am actually running the stated version?

So now we have an HTTP application running. It doesn’t do much, but it is a real application. It’s got some problems:

* The application is running on port 8003, but this port is blocked by the AWS firewall.
* The application is running without encryption, which means that anyone on the Internet could view its contents and potentially corrupt the data as it is transferred.The content could also be corrupted by chance, since TCP does not strongly protect against corruption.
* We need to have a window open with the flask command running. If we close the window, the web server stops.
* Flask’s built-in web server is not a production web server (i.e. it can be used for demonstration, but cannot handle real-world traffic levels).

Now we need to set up the gunicorn server:

* The server will listed on port 8003 (as specified above)
* The server will be started by the Linux services system.
* The server’s configuration will be specified in the file /etc/systemd/system/lab3.service
* The server will run out of the folder /home/ec2-user/app
* The server will use a Python virtual environment specified in the folder /home/ec2-user/venv

Before you go on, type ^C  (control-C) in the window where Flask is running so that the program exits:

$ **flask \--debug \--app simple\_flask\_application:app run \--reload \--port=8003**
 \* Serving Flask app 'simple\_flask\_application:app'
 \* Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 \* Running on http://127.0.0.1:8004
Press CTRL+C to quit
 \* Restarting with stat
 \* Debugger is active\!
 \* Debugger PIN: 130-083-806
**^C**$

# **Running a flask application from gunicorn** {#running-a-flask-application-from-gunicorn}

Gunicorn (which apparently stands for “[green unicorn](https://en.wikipedia.org/wiki/Gunicorn)”) is an application server for Python applications. It is a production server, meaning that it can handle a heavy load. In this section, you will create a new service on your Linux instance that will run the lab3 server with gunicorn in the background whenever your server is running.

Let’s set it up.

In this section we will be using the following files in the lab3 folder:

\-rw-rw-r-- 1 ubuntu ubuntu   456 Aug 14 23:55 lab3.service-simple\_flask\_application
\-rw-rw-r-- 1 ubuntu ubuntu   456 Aug 14 23:55 lab3.service-student\_server
\-rw-rw-r-- 1 ubuntu ubuntu   239 Aug 14 23:19 simple\_flask\_application.py
\-rw-rw-r-- 1 ubuntu ubuntu  1429 Aug 15 23:22 student\_data.py
\-rw-rw-r-- 1 ubuntu ubuntu  2792 Aug 16 01:17 student\_server.py

There are other files as well in this directory, but you can ignore them for now. (If you are interested, you can look inside the Makefile to see how the Python environment is set up and run.)

We have given you two files whose names start with lab3.service:

lab3.service-simple\_flask\_application — This file contains the gunicorn command line for serving the application out of the file simple\_flask\_application.py.You will use this file first.

lab3.service-student\_server — This file contains the gunicorn command line for serving the application out of the file student\_server.py. You will use this file second.

In order for Ubuntu 26.04 to run your server as a service (as opposed to from the command line), you need to copy the appropriate file to the location /etc/systemd/system/lab3.service and then start the service. We gave you two versions of this file so that you will not need to edit it.

Here are the contents of the file lab3.service-simple\_fask\_application:

\#\#\# install in /etc/systemd/system/lab3.service
\#\#\# then run:
\#\#\#  sudo systemctl daemon-reload
\#\#\#  sudo systemctl start lab3.service

\[Unit\]
Description=Gunicorn instance to serve Flask application for Lab 3
After=network.target

\[Service\]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/course/lab3
Environment="PATH=/home/ubuntu/course/lab3/.venv/bin"
ExecStart=/home/ubuntu/course/lab3/.venv/bin/gunicorn \-w 2 \-b 127.0.0.1:8003 \--reload simple\_flask\_application:app
Restart=always
RestartSec=1

\[Install\]
WantedBy=multi-user.target

Once installed, this service will:

* Run gunicorn, have it bind to port 8003, run the server at the app entry point, and reload the application whenever any of its source files are changed.
* Restart gunicorn every second if it crashes (useful if you have a typo that you then fix.)

***Also note — Once you have the gunicorn service running, you can no longer run the flask application on the command line with port 8003, because that port will now be in use\!***

Install and run the service with these commands:

$ **sudo cp \~/course/lab3/lab3.service-simple\_flask\_application /etc/systemd/system/lab3.service**
$ **sudo systemctl daemon-reload**
$ **sudo systemctl start lab3.service**    \# start now

You can verify that the service is running with:

$ **sudo systemctl status lab3.service**

If you see something like this, you have an error:

![][image4]

You can inspect the error log with journalctl:

$ **sudo journalctl \-u lab3.service \-e**

However, hopefully you don’t have any errors, and you see something like this:

![][image5]

"disabled" means that the service does not run when your instance starts up, but must be manually started with the systemctl start lab3.service command, like we did above..

You can now use the curl command:

$ **curl \-D \- http://localhost:8003/**
HTTP/1.1 200 OK
Server: gunicorn
Date: Thu, 14 Aug 2025 23:57:51 GMT
Connection: close
Content-Type: text/html; charset=utf-8
Content-Length: 27

\<h1\>Hello from Flask\!\</h1\>

Notice that this time, the header has this line: Server: gunicorn.

(In case you are wondering, we are using port 8003 because this is lab \#3. Each lab will have its own port number.)

# **Understanding the difference between “start” and “enable”** {#understanding-the-difference-between-“start”-and-“enable”}

On Linux systems like Ubuntu 26.04, services can be started or stopped, and they can separately be enabled or disabled.

systemctl start *servicename* — This tells Ubuntu 26.04 to start running the service.

systemctl stop *servicename* — This tells Ubuntu 26.04 to stop running the service.

systemctl enable *servicename* — This tells Ubuntu 26.04 to run the service automatically when the instance boots up.

systemctl disable *servicename* — This tells Ubuntu 26.04 not to run the service automatically when the instance boots up.

In this course, we ask that you start the lab service while you are working on the lab and then stop the lab service when you have completed the lab. It's important to stop the service because every running service takes memory, and we are having you use very small virtual machines. If you left all of the services for all of the labs running, your instance would run out of memory\!

In this course, we do not want you to enable the lab services. If you have a significant bug in your lab service, it might prevent your machine from running properly. If your service is enabled, then when you reboot your instance, it will automatically start up. This could make it very difficult for you to recover the instance in those circumstances.

(It would still be possible, but it would be so difficult that we would recommend that you create a new instance. What you would do to recover an instance in this situation is boot the instance in single-user mode and disable the service, or mount the instance’s root disk from another instance.)

# **Setting up the nginx reverse proxy** {#setting-up-the-nginx-reverse-proxy}

At this point the gunicorn server is starting automatically and serving the simple application.

Our next step is to set up an nginx “reverse proxy,” which will terminate a TLS connection and then “proxy” the HTTP request to the gunicorn server. It’s called a “reverse proxy” because it’s acting in reverse to a normal proxy, which traditionally proxies outbound HTTP requests to the Internet.

When nginx is set up as a reverse proxy, here’s what happens:

* A specific server within the flask configuration file is set to proxy to a specific URL (typically one that begins [http://127.0.0.1/](http://127.0.0.1/).
* nginx will add additional headers to the HTTP request, as specified in the configuration file.
* nginx will set a timeout (in seconds). If there is nothing sent during that time, both sides of the proxy are closed.

This is done by adding commands to the location block within the server block for the server block that is listening the virtual host.

Let’s do this now\!

Edit the file /etc/nginx/sites-available/default on your system with your editor of choice:

$ **sudo nano /etc/nginx/sites-available/default**

\-or-

$ **sudo vi /etc/nginx/sites-available/default**

\-or-

$ **sudo emacs /etc/nginx/sites-available/default**

Look for the server section that has your lab3 certificate. It should look like these lines; the second with the red highlights is what we will replace. To ensure you’re editing the correct section, make sure to match the last few lines below, up to and including the closing brace\! Then go back and replace the red-highlighted text.

server {

        \# SSL configuration
        \#
        \# listen 443 ssl default\_server;
        \# listen \[::\]:443 ssl default\_server;
        \#
        \# Note: You should disable gzip for SSL traffic.
        \# See: https://bugs.debian.org/773332
        \#
        \# Read up on ssl\_ciphers to ensure a secure configuration.
        \# See: https://bugs.debian.org/765782
        \#
        \# Self signed certs generated by the ssl-cert package
        \# Don't use them in a production server\!
        \#
        \# include snippets/snakeoil.conf;

        root /var/www/html;

        \# Add index.php to the list if you are using PHP
        index index.html index.htm index.nginx-debian.html;
    server\_name smashedemail-lab3.csci-e-11.org; \# managed by Certbot

        location / {
                \# First attempt to serve request as file, then
                \# as directory, then fall back to displaying a 404\.
                try\_files $uri $uri/ \=404;
        }

        \# pass PHP scripts to FastCGI server
        \#
        \#location \~ \\.php$ {
        \#       include snippets/fastcgi-php.conf;
        \#
        \#       \# With php-fpm (or other unix sockets):
        \#       fastcgi\_pass unix:/run/php/php7.4-fpm.sock;
        \#       \# With php-cgi (or other tcp sockets):
        \#       fastcgi\_pass 127.0.0.1:9000;
        \#}

        \# deny access to .htaccess files, if Apache's document root
        \# concurs with nginx's one
        \#
        \#location \~ /\\.ht {
        \#       deny all;
        \#}

    listen \[::\]:443 ssl; \# managed by Certbot
    listen 443 ssl; \# managed by Certbot
    ssl\_certificate /etc/letsencrypt/live/smashedemail.csci-e-11.org/fullchain.pem; \# managed by Certbot
    ssl\_certificate\_key /etc/letsencrypt/live/smashedemail.csci-e-11.org/privkey.pem; \# managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; \# managed by Certbot
    ssl\_dhparam /etc/letsencrypt/ssl-dhparams.pem; \# managed by Certbot

}

**(Don’t enable PHP — Users have reported that this breaks the grader\!)**

Here is the new code to substitute for the red-highlighted section above:

        **location / {**
            **proxy\_pass http://127.0.0.1:8003;**
            **proxy\_http\_version 1.1;**

            **proxy\_set\_header Upgrade $http\_upgrade;**
            **proxy\_set\_header Connection "upgrade";**

            **proxy\_set\_header Host $host;**
            **proxy\_set\_header X-Real-IP $remote\_addr;**
            **proxy\_set\_header X-Forwarded-For $proxy\_add\_x\_forwarded\_for;**
            **proxy\_set\_header X-Forwarded-Proto $scheme;**

            **proxy\_read\_timeout 86400;**
            **proxy\_send\_timeout 86400;**
        **}**

Test the configuration:

$ **sudo nginx \-t**
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
$

And tell the nginx service to reload:

$ **sudo systemctl reload nginx**

Finally, connect to your lab3 virtual host to verify that the simple flask application is running:

**![][image6]**

# **Creating a Student Database and Installing the Vulnerable Database Application** {#creating-a-student-database-and-installing-the-vulnerable-database-application}

Now we are going to install a web application on your instance that is susceptible to an SQL injection attack.

The server is vulnerable to an SQL injection attack because it does not use prepared SQL statements. [SQLite3 offers prepared statements](https://stackoverflow.com/questions/48587659/does-pythons-sqlite3-module-support-prepared-statements/48587835), and later in this lab you will fix your program to use them. But first we’re going to see if anyone tries to exploit your application after you publicize it.

## **The Right Starting Place** {#the-right-starting-place}

Make sure you are in the correct directory by executing:

$ **cd \~/course/lab3**

Then, activate the poetry environment:

	**$(poetry env activate)**

## **Creating the student database** {#creating-the-student-database}

We’ve given you a program called [student\_data.py](https://github.com/Harvard-CSCI-E-11/spring27/blob/main/lab3/student_data.py) that creates a database of fake student data using the [Faker](https://pypi.org/project/Faker/) python package and returns a connection to the open database. You can run this program using to see the fake data:

(lab3-py3.14) ubuntu@smashedmeail:\~/course/lab3$ **python student\_data.py**

The data is stored in a local SQLite3 database called students.db:

ubuntu@smashedemail:\~/course/lab3$ **ls \-l students.db**
\-rw-r--r-- 1 ubuntu ubuntu 16384 Aug 15 23:22 students.db
ubuntu@smashedemail:\~/course/lab3$

Test to make sure you created some records; our results are shown below in blue:

$ **sudo apt install sqlite3**
$ **echo \-e ".mode column \\n select \* from students limit 5;" | sqlite3 students.db**
name            email                           student\_id  gpa   sat
\--------------  \------------------------------  \----------  \----  \----
Diana Long      ilee@jones-higgins.net          S82218      2.22  838
Hunter Warren   phernandez@smith-francis.com    S40437      3.88  1521
Kathryn Wilson  garciarobin@gmail.com           S71840      3.19  1131
Peter Sullivan  rebeccahensley@boyer-white.com  S24004      3.29  1221
Adam Johnson    richard40@brewer.com            S55892      2.03  1593

(Of course, your students will be different, as these are randomly generated.)

This is a pipeline: the SQL commands .mode column and select \* from students limit 5; are output by the echo command (\-e means interpret escape characters) and then sent to the standard input of the sqlite3 command, which runs the commands.

Write down a few of the student ID numbers. You will need them in the next step.

## **Installing the vulnerable app** {#installing-the-vulnerable-app}

The vulnerable app is stored in the file /home/ubuntu/course/lab3/student\_server.py.

First, we need to change the lab3.service file so that gunicorn will run the file student\_server.py instead of simple\_flask\_application.py:

$ **sudo cp \~/course/lab3/lab3.service-student\_server /etc/systemd/system/lab3.service**

$ **sudo systemctl daemon-reload**

$ **sudo systemctl restart lab3**

Verify that the application running on port 8003 has been updated:

$ **curl http://localhost:8003/**

If you have problems, you can use this command to view the last 100 log lines in reverse event order:

$ **sudo journalctl \-r \-u lab3.service \-n 100**

(NOTE: If you have previous experience with Linux, you may be expecting that the logs will be stored in text files in the /var/log directory. Modern Linux systems store their logs in structured binary index files in the /var/log/journal directory.)

# **Test your web application** {#test-your-web-application}

Your web server with the vulnerable web application should now be running.

## **Test with normal code** {#test-with-normal-code}

To demonstrate the vulnerability, first run the web application normally. Go to the web page:

![][image7]

Enter one of the student IDs you previously learned (the STUDENT ID pictured below will not work in your specific instance):

![][image8]

And press Submit:

![][image9]

When the student ID S71840 was entered above, the program created this SQL command:

select \* from students where student\_id \= "S71840"

## **Demonstrate the vulnerability** {#demonstrate-the-vulnerability}

Now, try entering this text in the STUDENT ID box:

" or ""="

This will cause the SQL statement to become:

select \* from students where student\_id \= "" or ""=""

Now click SUBMIT\!

## **Debugging** {#debugging}

Is something not working? Here are some things to try:

1. Look at the last 100 lines of your webserver’s with the journalctl command:

   $ **sudo journalctl \-r \-u lab3.service \-n 100**

2. Post a question in the class forum on Canvas.
3. Ask the TA’s for help\!

# **Learn about Prepared Statements** {#learn-about-prepared-statements}

The way to fix the vulnerable web application is to make it use a prepared SQL statement.

A *prepared SQL statement* is an SQL statement template that has placeholders for values that might be provided by the user. For example, here is an SQL statement that inserts a new record into your database:

insert into students (name,email,student\_id,gpa,sat)
values ('Alyssa P. Hacker','alyssa@hacker.com','APH100',5.0,800);

Here is a prepared version of that same statement:

insert into students (name,email,student\_id,gpa,sat)
values (?, ?, ?, ?, ?);

Please review:

* [sqlite3 — DB-API 2.0 interface for SQLite databases — Python 3.14 documentation](https://docs.python.org/3/library/sqlite3.html#how-to-guides)

Our program makefake.py uses a prepared statement to insert each record:

cur.execute("insert into students values (?,?,?,?,?);",
            (name,email,student\_id,gpa,sat\_score))

# **Get an A: Fix your app** {#get-an-a:-fix-your-app}

Modify your program student\_server.py to use a prepared statement.

# **Using the e11 command** {#using-the-e11-command}

You can check your server with this command:

$ **e11 check lab3**

You can request that your lab be graded with:

$ **e11 grade lab3**

You can run the grade command as many times as you want. The highest grade is the one that we will export to Canvas. We will record your highest grade in Canvas the week after the lab is due.

When you are finished, we recommend that you stop the lab3 service to conserve your instance’s RAM:

$ **sudo systemctl stop lab3.service**

# **Going Further** {#going-further}

The Linux systemctl command is really powerful. Check out its documentation with:

$ **man systemctl**

There’s a lot more you can do with the nginx config file and gunicorn. Here are some pages from the documentation you might want to review:

* [Deploying Gunicorn \- Nginx Configuration](https://docs.gunicorn.org/en/latest/deploy.html)

In this lab, we communicate between the nginx module and the gunicorn server over a TCP port. However, nginx can also communicate over a Unix domain socket. This is more efficient and slightly more secure, but a bit harder to set up.

* Rewrite nginx configuration and the systemd service file so that the communication occurs with sockets.

This lab uses a local SQL server. However, what we are storing could easily be stored in Amazon’s [DynamoDB](https://aws.amazon.com/dynamodb/).

* Rewrite the program to store records in DynamoDB. To use it, you will need to give your instance permission to access DynamoDB, and you will need to create a table in which to store you data.
* Is the rewritten program susceptible to an SQL injection attack? Why or why not?

# **Notes on Debugging Lab3**

Having problems? Here are some notes:

## **nginx \-t must be run as root with sudo:**

Without sudo:

ubuntu@simsong40acm:\~$ **nginx \-t**
2026/02/20 19:01:37 \[warn\] 47388\#47388: the "user" directive makes sense only if the master process runs with super-user privileges, ignored in /etc/nginx/nginx.conf:1
2026/02/20 19:01:37 \[emerg\] 47388\#47388: cannot load certificate "/etc/letsencrypt/live/simsong40acm.csci-e-11.org/fullchain.pem": BIO\_new\_file() failed (SSL: error:8000000D:system library::Permission denied:calling fopen(/etc/letsencrypt/live/simsong40acm.csci-e-11.org/fullchain.pem, r) error:10080002:BIO routines::system lib)
nginx: configuration file /etc/nginx/nginx.conf test failed

With sudo:

ubuntu@simsong40acm:\~$ **sudo nginx \-t**
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful

## **Be careful about extraneous files in the /etc/nginx directories**

This is what you should see:

ubuntu@simsong40acm:\~$ **ls \-l /etc/nginx/**
total 68
drwxr-xr-x 2 root root 4096 Feb  9 14:03 conf.d
\-rw-r--r-- 1 root root 1125 Nov 30  2023 fastcgi.conf
\-rw-r--r-- 1 root root 1055 Nov 30  2023 fastcgi\_params
\-rw-r--r-- 1 root root 2837 Nov 30  2023 koi-utf
\-rw-r--r-- 1 root root 2223 Nov 30  2023 koi-win
\-rw-r--r-- 1 root root 5465 Nov 30  2023 mime.types
drwxr-xr-x 2 root root 4096 Feb  9 14:03 modules-available
drwxr-xr-x 2 root root 4096 Feb  9 14:03 modules-enabled
\-rw-r--r-- 1 root root 1446 Nov 30  2023 nginx.conf
\-rw-r--r-- 1 root root  180 Nov 30  2023 proxy\_params
\-rw-r--r-- 1 root root  636 Nov 30  2023 scgi\_params
drwxr-xr-x 2 root root 4096 Feb 20 18:59 sites-available
drwxr-xr-x 2 root root 4096 Feb 20 18:50 sites-enabled
drwxr-xr-x 2 root root 4096 Feb 20 18:50 snippets
\-rw-r--r-- 1 root root  664 Nov 30  2023 uwsgi\_params
\-rw-r--r-- 1 root root 3071 Nov 30  2023 win-utf
ubuntu@simsong40acm:\~$ **ls \-l /etc/nginx/sites-available/**
total 16
\-rw-r--r-- 1 root root 6732 Feb 20 18:59 default
\-rw-r--r-- 1 root root 6352 Feb 20 18:59 default.old
ubuntu@simsong40acm:\~$ **ls \-l /etc/nginx/sites-enabled/**
total 0
lrwxrwxrwx 1 root root 34 Feb 20 18:50 default \-\> /etc/nginx/sites-available/default
ubuntu@simsong40acm:\~$

## **Be careful about typos in your nginx.conf file**

Here is what one looks like:

ubuntu@simsong40acm:\~$ cat /etc/nginx/sites-enabled/default  | sed s/simsong40acm/smashedemail/
\#\#
\# You should look at the following URL's in order to grasp a solid understanding
\# of Nginx configuration files in order to fully unleash the power of Nginx.
\# https://www.nginx.com/resources/wiki/start/
\# https://www.nginx.com/resources/wiki/start/topics/tutorials/config\_pitfalls/
\# https://wiki.debian.org/Nginx/DirectoryStructure
\#
\# In most cases, administrators will remove this file from sites-enabled/ and
\# leave it as reference inside of sites-available where it will continue to be
\# updated by the nginx packaging team.
\#
\# This file will automatically load configuration files provided by other
\# applications, such as Drupal or Wordpress. These applications will be made
\# available underneath a path with that package name, such as /drupal8.
\#
\# Please see /usr/share/doc/nginx-doc/examples/ for more detailed examples.
\#\#

\# Default server configuration
\#
server {
	listen 80 default\_server;
	listen \[::\]:80 default\_server;

	\# SSL configuration
	\#
	\# listen 443 ssl default\_server;
	\# listen \[::\]:443 ssl default\_server;
	\#
	\# Note: You should disable gzip for SSL traffic.
	\# See: https://bugs.debian.org/773332
	\#
	\# Read up on ssl\_ciphers to ensure a secure configuration.
	\# See: https://bugs.debian.org/765782
	\#
	\# Self signed certs generated by the ssl-cert package
	\# Don't use them in a production server\!
	\#
	\# include snippets/snakeoil.conf;

	root /var/www/html;

	\# Add index.php to the list if you are using PHP
	index index.html index.htm index.nginx-debian.html;

	server\_name \_;

	location / {
		\# First attempt to serve request as file, then
		\# as directory, then fall back to displaying a 404\.
		try\_files $uri $uri/ \=404;
	}

	\# pass PHP scripts to FastCGI server
	\#
	\#location \~ \\.php$ {
	\#	include snippets/fastcgi-php.conf;
	\#
	\#	\# With php-fpm (or other unix sockets):
	\#	fastcgi\_pass unix:/run/php/php7.4-fpm.sock;
	\#	\# With php-cgi (or other tcp sockets):
	\#	fastcgi\_pass 127.0.0.1:9000;
	\#}

	\# deny access to .htaccess files, if Apache's document root
	\# concurs with nginx's one
	\#
	\#location \~ /\\.ht {
	\#	deny all;
	\#}
}

\# Virtual Host configuration for example.com
\#
\# You can move that to a different file under sites-available/ and symlink that
\# to sites-enabled/ to enable it.
\#
\#server {
\#	listen 80;
\#	listen \[::\]:80;
\#
\#	server\_name example.com;
\#
\#	root /var/www/example.com;
\#	index index.html;
\#
\#	location / {
\#		try\_files $uri $uri/ \=404;
\#	}
\#}

server {

	\# SSL configuration
	\#
	\# listen 443 ssl default\_server;
	\# listen \[::\]:443 ssl default\_server;
	\#
	\# Note: You should disable gzip for SSL traffic.
	\# See: https://bugs.debian.org/773332
	\#
	\# Read up on ssl\_ciphers to ensure a secure configuration.
	\# See: https://bugs.debian.org/765782
	\#
	\# Self signed certs generated by the ssl-cert package
	\# Don't use them in a production server\!
	\#
	\# include snippets/snakeoil.conf;

	root /var/www/html;

	\# Add index.php to the list if you are using PHP
	index index.html index.htm index.nginx-debian.html;
    server\_name smashedemail.csci-e-11.org; \# managed by Certbot
\# lab2\_patch

 location /confidential {
                 auth\_basic "CSCI E-11";
                 auth\_basic\_user\_file /home/web-passwords;
        }

	location / {
		\# First attempt to serve request as file, then
		\# as directory, then fall back to displaying a 404\.
		try\_files $uri $uri/ \=404;
	}

	\# pass PHP scripts to FastCGI server
	\#
	\#location \~ \\.php$ {
	\#	include snippets/fastcgi-php.conf;
	\#
	\#	\# With php-fpm (or other unix sockets):
	\#	fastcgi\_pass unix:/run/php/php7.4-fpm.sock;
	\#	\# With php-cgi (or other tcp sockets):
	\#	fastcgi\_pass 127.0.0.1:9000;
	\#}

	\# deny access to .htaccess files, if Apache's document root
	\# concurs with nginx's one
	\#
	\#location \~ /\\.ht {
	\#	deny all;
	\#}

    listen \[::\]:443 ssl ipv6only=on; \# managed by Certbot
    listen 443 ssl; \# managed by Certbot
    ssl\_certificate /etc/letsencrypt/live/smashedemail.csci-e-11.org/fullchain.pem; \# managed by Certbot
    ssl\_certificate\_key /etc/letsencrypt/live/smashedemail.csci-e-11.org/privkey.pem; \# managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; \# managed by Certbot
    ssl\_dhparam /etc/letsencrypt/ssl-dhparams.pem; \# managed by Certbot

}
server {
    if ($host \= smashedemail.csci-e-11.org) {
        return 301 https://$host$request\_uri;
    } \# managed by Certbot

	listen 80 ;
	listen \[::\]:80 ;
    server\_name smashedemail.csci-e-11.org;
    return 404; \# managed by Certbot

}
server {

	\# SSL configuration
	\#
	\# listen 443 ssl default\_server;
	\# listen \[::\]:443 ssl default\_server;
	\#
	\# Note: You should disable gzip for SSL traffic.
	\# See: https://bugs.debian.org/773332
	\#
	\# Read up on ssl\_ciphers to ensure a secure configuration.
	\# See: https://bugs.debian.org/765782
	\#
	\# Self signed certs generated by the ssl-cert package
	\# Don't use them in a production server\!
	\#
	\# include snippets/snakeoil.conf;

	root /var/www/html;

	\# Add index.php to the list if you are using PHP
	index index.html index.htm index.nginx-debian.html;
    server\_name smashedemail-lab3.csci-e-11.org; \# managed by Certbot
\# lab3\_patch

        location / {
            proxy\_pass http://127.0.0.1:8003;
            proxy\_http\_version 1.1;

            proxy\_set\_header Upgrade $http\_upgrade;
            proxy\_set\_header Connection "upgrade";

            proxy\_set\_header Host $host;
            proxy\_set\_header X-Real-IP $remote\_addr;
            proxy\_set\_header X-Forwarded-For $proxy\_add\_x\_forwarded\_for;
            proxy\_set\_header X-Forwarded-Proto $scheme;

            proxy\_read\_timeout 86400;
            proxy\_send\_timeout 86400;
        }
	\# pass PHP scripts to FastCGI server
	\#
	\#location \~ \\.php$ {
	\#	include snippets/fastcgi-php.conf;
	\#
	\#	\# With php-fpm (or other unix sockets):
	\#	fastcgi\_pass unix:/run/php/php7.4-fpm.sock;
	\#	\# With php-cgi (or other tcp sockets):
	\#	fastcgi\_pass 127.0.0.1:9000;
	\#}

	\# deny access to .htaccess files, if Apache's document root
	\# concurs with nginx's one
	\#
	\#location \~ /\\.ht {
	\#	deny all;
	\#}

    listen \[::\]:443 ssl; \# managed by Certbot
    listen 443 ssl; \# managed by Certbot
    ssl\_certificate /etc/letsencrypt/live/smashedemail.csci-e-11.org/fullchain.pem; \# managed by Certbot
    ssl\_certificate\_key /etc/letsencrypt/live/smashedemail.csci-e-11.org/privkey.pem; \# managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; \# managed by Certbot
    ssl\_dhparam /etc/letsencrypt/ssl-dhparams.pem; \# managed by Certbot

}
server {
    if ($host \= smashedemail-lab3.csci-e-11.org) {
        return 301 https://$host$request\_uri;
    } \# managed by Certbot

	listen 80 ;
	listen \[::\]:80 ;
    server\_name smashedemail-lab3.csci-e-11.org;
    return 404; \# managed by Certbot
}

[image1]: <images/3-logo.png>
[image2]: <images/3-privacyerror.png>
[image3]: <images/3-nginx.png>
[image4]: <images/3-serviceerror.png>
[image5]: <images/3-servicestatus.png>
[image6]: <images/3-flask.png>
[image7]: <images/3-searchform.png>
[image8]: <images/3-studentid.png>
[image9]: <images/3-results.png>
