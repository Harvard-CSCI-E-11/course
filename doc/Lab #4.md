# **![][image1]**

# **CSCI E-11: Artificial Intelligence, the Internet-of-Things, and Cybersecurity** **Harvard Extension School** **Spring 2027**

# **Lab \#4: Message Board — An API server with password hashing**

[Introduction and Lab Objectives](#introduction-and-lab-objectives)

[Getting Started — Read The Docs\!](#building-on-lab-3)

[Application — Functional Specifications](#application-—-functional-specifications)

[Understanding the Security Issues](#understanding-the-security-issues)

[Install and test the lab4 application on port 8004](#install-and-test-the-lab4-application-on-port-8004)

[Test the application from the command line](#test-the-application-from-the-command-line)

[Install the lab4.service gunicorn server on port 8004](#install-the-lab4.service-gunicorn-server-on-port-8004)

[Add Another Virtual Host](#add-another-virtual-host)

[Expand the certificate](#expand-the-certificate)

[Edit the configuration file](#edit-the-configuration-file)

[Restart the servers](#restart-the-servers)

[Test](#test)

[Review the SQLite schema](#review-the-sqlite-schema)

[Initialize the database and create an API key](#initialize-the-database-and-create-an-api-key)

[Try it out\!](#try-it-out!)

[Debugging](#debugging)

[Going Even Further](#going-even-further)

# **Introduction and Lab Objectives** {#introduction-and-lab-objectives}

Welcome to the fourth lab\! In this lab we will use Amazon Web Services to deploy a secure message board. By “secure” we mean that only authorized clients will be able to post messages. By “message board” we mean that anyone on the Internet will be able to read the messages.

Objectives for this lab:

* Learn about *password hashing*, an authentication method that combines an *identifier* and a *shared secret.*
* Deploy a web-based message board that is built on an API that uses password hashing for authentication and an SQLite database for data storage.
* Build in computer security from the start rather than add it as an after-thought.

What you will turn in:

* Screen shots indicating that your service works.

# **Building on Lab 3** {#building-on-lab-3}

This assignment builds on the instance created in Lab 1 and updated in Labs 2 and 3\. If you stopped it, now is a good time to restart it.

NOTE: If you **terminated** your instance, we highly recommend that you stop terminating your instance at the end of the labs\! Just **stop** the instance, do not terminate it.

**terminating the instance — **This erases the instance’s drive and removes it from your AWS control panel.

**stopping the instance** — This gives up your instance’s IP address but keeps the instance’s virtual drive.

If you did terminate your instance, you will need to create a new instance, reinstall the installer, register it again, and re-do labs 1, 2 and 3\.

In Lab 3 we added support for the *smashedemail-lab3.csci-e-11.org* virtual host to the nginx web server and provisioned Let’s Encrypt TLS certificate for the hostname.

Lab 4 builds upon Lab 3\. In particular, many of the files in the [lab4 folder of the git repo](https://github.com/Harvard-CSCI-E-11/spring25/tree/main/lab4) are copies of the same files in the lab4 folder. The only files that are different will be:

	`lab4/Makefile` — contains new targets

	`lab4/README.m`d — describes what’s different

	`lab4/lab4.service` — A new Linux service to run gunicorn for the lab4 server on port 8004\.

	`lab4/lab4-nginx-patch` — Now we `proxy_pass` to port `8004`

	`lab4/server/` — The new server\!

# **Getting Started — Read The Docs\!**

This assignment makes use of an approach called *password hashing.*

For more information about password hashing, we recommend this blog entry from Okta:

* [https://www.okta.com/blog/2019/03/what-are-salted-passwords-and-password-hashing/](https://www.okta.com/blog/2019/03/what-are-salted-passwords-and-password-hashing/)

For more more technical information, we recommend these optional readings:

* [https://en.wikipedia.org/wiki/Hash\_function](https://en.wikipedia.org/wiki/Hash_function)
* [https://en.wikipedia.org/wiki/Secure\_Hash\_Algorithms](https://en.wikipedia.org/wiki/Secure_Hash_Algorithms)
* [https://en.wikipedia.org/wiki/Salt\_(cryptography)](https://en.wikipedia.org/wiki/Salt_\(cryptography\))

We will be using Flask’s ability to serve static files and templates, so read up on that as well:

* [Templates — Flask Documentation (3.1.x)](https://flask.palletsprojects.com/en/stable/tutorial/templates/)
* [Static Files — Flask Documentation (3.1.x)](https://flask.palletsprojects.com/en/stable/tutorial/static/)

# **Application — Functional Specifications** {#application-—-functional-specifications}

In this lab we will build a simple message board application. Messages can be posted to the board by authorized users from a web browser, and they can be viewed by anyone on the Internet.

Here are the functional specifications of the application:

1. The application will consist of multiple parts:

   1. A Python application running on your AWS instance. We’re going to use the same instance that we used in the previous labs, with the same IP address, but we’ll use a different hostname, which means that we’ll need to upgrade its Let’s Encrypt TLS certificate.

   2. The lab 4 application will:

      1. Maintain a list of authorized users who can post new messages

      2. Maintain the database of messages that have been posted.

      3. The database will be an SQLite file called `/home/ubuntu/lab4/app/message_board.db`

   3. An HTML file that will display a form and load a simple JavaScript application into the browser. The form will:

      1. Allow a person to enter their *authorization credentials* and their *message* to posted.

      2. Have a **submit** button that submits the form to the server.

      3. Each HTML file is stored as a template in the directory `/home/ubuntu/lab4/app/templates/`

   4. A JavaScript application running in the web browser that will:

      1. Display all of the messages that have been posted.

      2. The JavaScript application is stored in the directory `/home/ubuntu/lab4/app/static/`

2. The authorization system will be based on API (Application Programmer Interface) keys.

   1. Each API key will consist of two parts:

      1. An API\_KEY that will be stored in a database. It’s like a username, except it looks like a random group of letters and numbers.

      2. A corresponding API\_SECRET\_KEY that is created at the same time as the API\_KEY but that is processed with a one-way function called the [Password-Based Key Derivation Function 2](https://en.wikipedia.org/wiki/PBKDF2). The resulting string, called a *hash* (because the processing involves a [cryptographic hash function](https://en.wikipedia.org/wiki/Cryptographic_hash_function)) is also stored in the database.

   2. The advantage of having an API\_KEY and the hash (rather than the API\_SECRET\_KEY itself) stored in the server is that it reduces the security risk if the server’s password database is compromised and downloaded by an attacker. Anyone who has the file will have a list of valid API\_KEYs, but they won’t be able to actually authenticate to the server. This is useful, because it is far more common for attackers to be able to *read* a confidential password database than to *write* to the database (which would let them create their own users).

3. The API keys and the messages will all be kept in the SQLite database on the instance.

4. The Python application will implement an API called `/api/post-message` that will:
   1. Verify that the API\_KEY exists and that the API\_SECRET\_KEY is correct.

   2. Add the provided message to the database.

5. The Python application will also implement an API called `/api/get-messages` that will return all of the messages as a JSON object.

6. The application running in the web browser will consist of a web page at will present a web form that has:

   1. Text fields for the \<API\_KEY\> and the \<API\_SECRET\_KEY\>.

   2. A text field with the message to post.

   3. An **\[upload\]** button. Pressing this button will run the `/api-post-message` API on the server.

7. The application running in the web browser will also have a JavaScript function called `list_messages()` that will run the `/api/get-messages` API and display all the current messages.

   1. A timer will cause the `list_messages()` function to run every 5 seconds to check for new messages.  This approach is called “polling.” It is not very efficient, but it works for this example.

Our system is different from a production system in several key ways:

* In a production system, the `/api/get-messages` API would only return the 10 or 20 most recent messages, and there would be arguments that allowed access to older messages.
* Instead of polling, a production system would likely use a more efficient approach such as [*long polling*](https://ably.com/topic/long-polling), [*web sockets*](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API) or [*server side events*](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events) to notify clients that new messages are available.
* A production system might limit the number of times that each API key could be used within a certain time period. This would prevent abuse.
* Instead of using an SQLite database on a single server, a production system would likely use a scalable, redundant database such as Amazon’s DynamoDB,

# **Understanding the Security Issues** {#understanding-the-security-issues}

While it is common in software engineering to first develop a minimum working product and then to add security, **you should never do this.** Instead, it’s vital to think about security from the very beginning and make it part of your initial design. That’s why our initial design includes a way for authenticating messages that are posted.

Remember our example in class of the NIST Risk Management Framework. Think about:

- What threat actors might exist (pranksters, hackers, stalkers, scammers…)
- What they might want to do with your application (pretend to be other people, bring down your system, spread malicious or dangerous information,...)
- What the impact on you would be (becoming complicit in harm, legal liability, loss of your application, …)
- And what vulnerabilities in your system might allow those threats to occur (unauthenticated access, anonymous posting, open usage of resources to anyone on the net, …)

However, even with our design, there are several security issues that we haven’t covered.

* Think about the design of our system and the resources that it makes available on the Internet. Identify at least one security risk that we have not addressed.

We are now ready to start implementing Lab 4\.

# **Install and test the lab4 application on port 8004** {#install-and-test-the-lab4-application-on-port-8004}

We have provided a template lab4 application for you that will display a HTML page on a web browser and command the browser to download and run the JavaScript application.

## **Test the application from the command line** {#test-the-application-from-the-command-line}

First, make sure the application works.

In one window type:

`$ cd ~/course/lab4`

Now lets use `poetry`, the python package manager, to install all the dependencies we need.

`$ poetry install`

Now we update the python environment based on the lock files in \~/lab4/

`$ poetry sync`

And now we run the application from the command line to make sure it is working before we automate the running of the application.

`$ poetry run flask --app server.main:app run --debug --port 8004 --reload`

In a second window type:

`$ curl http://localhost:8004/`

When you have verified that this is working (that is, the Message Board html is echoed back to you), type ^C in the first window to stop the flask application

Notice that the server is now called `server:app`. This is because the server is the `app` object that is created in the file `~/course/lab4/server/main.py`

## **Install the lab4.service gunicorn server on port 8004** {#install-the-lab4.service-gunicorn-server-on-port-8004}

In lab3 you installed the lab3 gunicorn service. Here you install the lab4 gunicorn server on port 8004\.

Review the file:

`$ cd ~/course/lab4`

`$ cat lab4.service`

If it looks good, install it:

`$ sudo cp lab4.service /etc/systemd/system/`

# **Add Another Virtual Host** {#add-another-virtual-host}

In Lab 2 you set the hostname of your instance to be *`smashedemail`*`.csci-e-11.org`*,* where  *`smashedemail`* is related to your email address.

When we created that DNS name for you in the `csci-e-11.org` domain, we actually created several other DNSs, all pointing to the same IP address:

*`smashedemail`*`.csci-e-11.org`

*`smashedemail`*`-lab1.csci-e-11.org`

*`smashedemail`*`-lab2.csci-e-11.org`

*`smashedemail`*`-lab3.csci-e-11.org`

*`smashedemail`*`-lab4.csci-e-11.org`

*`smashedemail`*`-lab5.csci-e-11.org`

*`smashedemail`*`-lab6.csci-e-11.org`

[*`smashedemail-lab7.csci-e-11.org`](http://smashedemail-lab7.csci-e-11.org)*

[*`smashedemail-lab8.csci-e-11.org`](http://smashedemail-lab7.csci-e-11.org)*

Each of these DNS entries have the same IP address.

In Lab3 you configured the web server so that [*`smashedemail`*`.csci-e-11.org`](http://smashedemail.csci-e-11.org) and [*`smashedemail`*`-lab3.csci-e-11.org`](http://smashedemail-lab2.csci-e-11.org) have different websites—the first served the default page, and the second served a database driven application.

In this lab we will configure the `lab4` server so that it serves yet another database-driven application. This application is similar to the one in lab 3, with the following differences:

|  | Lab3 | Lab4 |
| :---- | :---- | :---- |
| nginx server name | *`smashedemail`*`-lab3.csci-e-11.org` | *`smashedemail`*`-lab4.csci-e-11.org` |
| reverse proxy port | localhost:8003 | localhost:8004 |
| Installation directory | `/home/ubuntu/course/lab3` | `/home/ubuntu/course/lab4` |
| Python virtual environment | `/home/ubuntu/course/lab3/.venv` | `/home/ubuntu/course/lab4/.venv` |
| Application | Simple database lookup | Client/Server message board |

## **Expand the certificate** {#expand-the-certificate}

Use the `cerbot -d` command to expand the Let’s Encrypt certificate:

`$ sudo certbot -d smashedemail.csci-e-11.org \`
  **`-d smashedemail-lab3.csci-e-11.org \`**
  **`-d smashedemail-lab4.csci-e-11.org`**

Above we use `\` to allow the command to bridge multiple lines, but you can put everything on the same line if you wish:

`$ sudo certbot -d smashedemail.csci-e-11.org -d smashedemail-lab3.csci-e-11.org -d smashedemail-lab4.csci-e-11.org`

**Remember to choose to expand the certificate when the certbot command asks\!**

## **Edit the configuration file** {#edit-the-configuration-file}

As you did in lab3, edit (using sudo)  the file `/etc/nginx/sites-available/default` and find the new `server {` block that contains the `server_name smashedemail-lab4.csci-e-11.org;` command.

Look for this code:

        `location / {`
                `# First attempt to serve request as file, then`
                `# as directory, then fall back to displaying a 404.`
                `try_files $uri $uri/ =404;`
        `}`

And change it to:

        `location / {`
        `proxy_pass http://127.0.0.1:8004;`
        `proxy_http_version 1.1;`

        `proxy_set_header Upgrade $http_upgrade;`
        `proxy_set_header Connection "upgrade";`

        `proxy_set_header Host $host;`
        `proxy_set_header X-Real-IP $remote_addr;`
        `proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;`
        `proxy_set_header X-Forwarded-Proto $scheme;`

        `proxy_read_timeout 86400;`
        `proxy_send_timeout 86400;`
        `}`

NOTE: Make sure that you set the port to be 8004\! (Each lab uses a different port number\!)

Similar to lab3, you can find this file at `~/course/lab4/lab4-nginx-patch`.

You may wish to review [Lab \#3](Lab%20%233.md) for instructions on how to edit this file.

Test the config file with:

`$ sudo nginx -t`

## **Restart the servers** {#restart-the-servers}

Restart the server with:

`$ sudo systemctl restart nginx lab4`

## **Test** {#test}

Test your lab4 server with:

`$ curl https://smashedemail-lab4.csci-e-11.org/`

You should see the filled-in template for the lab4 application web page.

It should look different from what you get with:

`$ curl https://smashedemail-lab3.csci-e-11.org/`

Neither should generate an error

You can also try it from your web browser by going to the page **`https://smashedemail-lab4.csci-e-11.org/.`**

# **Review the SQLite schema** {#review-the-sqlite-schema}

Please review the SQLite schema for lab 4:

[https://github.com/Harvard-CSCI-E-11/spring27/blob/main/lab4/server/schema\_lab4.sql](https://github.com/Harvard-CSCI-E-11/spring27/blob/main/lab4/server/schema_lab4.sql)

This is a simple schema that has two tables \- one for the API keys and one for the messages that are posted.

# **Initialize the database and create an API key** {#initialize-the-database-and-create-an-api-key}

We have given you a makefile target to initialize the SQLite database and create an API key.

**Be sure you are in the lab4 directory,** then execute these commands:

`make init-db` — Initializes the database (erasing any API\_KEYs)

`make new-apikey` — Creates a new API\_KEY and API\_SECRET\_KEY.  ***Save these\!***

`make dump-db` — Shows you what is in the database. Notice that the API\_SECRET\_KEY is not stored, only the hashed key and the hashing parameters.

The system of using a hashed value and a secret key is called Hash-Based Message Authentication Communication, or HMAC. You’ll often see these keys labeled as HMAC\_KEY. See [https://en.wikipedia.org/wiki/HMAC](https://en.wikipedia.org/wiki/HMAC)

# **Try it out\!** {#try-it-out!}

1. Go to the web page *smashedemail-*lab4.csci-e-11.org

2. Enter the API\_KEY and the API\_SECRET\_KEY from above

3. Enter a message

4. Click POST

5. From the command line window in \~/lab4:

   `$ make dump-db`

Your screen should look something like this:

**`![][image2]`**

# **Debugging** {#debugging}

Is something not working? Here are some things to try:

1. Make sure that the `lab4` Linux service that launches `gunicorn` is running:

   `$ systemctl status lab4.service`

2. You can look at the logs for the lab4 service with journalctl:

   `$ journalctl -u lab4.service`

3. You can watch the logs as they happen by adding the `-f` (follow) option:

   `$ journalctl -u lab4.service -f`

Here’s what it looks like on a good system:

`ubuntu@sgarfinkelfas:~/course/lab4$ journalctl -u lab4.service`

`Aug 17 23:47:58 sgarfinkelfas.csci-e-11.org systemd[1]: Started lab4.service - Gunicorn instance to serve Flask application for lab 4.`
`Aug 17 23:47:58 sgarfinkelfas.csci-e-11.org gunicorn[29609]: [2025-08-17 23:47:58 +0000] [29609] [INFO] Starting gunicorn 23.0.0`
`Aug 17 23:47:58 sgarfinkelfas.csci-e-11.org gunicorn[29609]: [2025-08-17 23:47:58 +0000] [29609] [INFO] Listening at: http://127.0.0.1:8004 (29609)`
`Aug 17 23:47:58 sgarfinkelfas.csci-e-11.org gunicorn[29609]: [2025-08-17 23:47:58 +0000] [29609] [INFO] Using worker: sync`
`Aug 17 23:47:58 sgarfinkelfas.csci-e-11.org gunicorn[29618]: [2025-08-17 23:47:58 +0000] [29618] [INFO] Booting worker with pid: 29618`
`Aug 17 23:47:58 sgarfinkelfas.csci-e-11.org gunicorn[29619]: [2025-08-17 23:47:58 +0000] [29619] [INFO] Booting worker with pid: 29619`
`Aug 17 23:52:18 sgarfinkelfas.csci-e-11.org gunicorn[29619]: [2025-08-17 23:52:18 +0000] [29619] [INFO] Worker reloading: /home/ubuntu/course/lab4/server/db.py modified`
`Aug 17 23:52:18 sgarfinkelfas.csci-e-11.org gunicorn[29619]: [2025-08-17 23:52:18 +0000] [29619] [INFO] Worker exiting (pid: 29619)`
`Aug 17 23:52:18 sgarfinkelfas.csci-e-11.org gunicorn[29618]: [2025-08-17 23:52:18 +0000] [29618] [INFO] Worker reloading: /home/ubuntu/course/lab4/server/db.py modified`
`Aug 17 23:52:18 sgarfinkelfas.csci-e-11.org gunicorn[29618]: [2025-08-17 23:52:18 +0000] [29618] [INFO] Worker exiting (pid: 29618)`
`Aug 17 23:52:18 sgarfinkelfas.csci-e-11.org gunicorn[29703]: [2025-08-17 23:52:18 +0000] [29703] [INFO] Booting worker with pid: 29703`
`Aug 17 23:52:18 sgarfinkelfas.csci-e-11.org gunicorn[29704]: [2025-08-17 23:52:18 +0000] [29704] [INFO] Booting worker with pid: 29704`

4. Look at other system logs as they appear:

   `$ journalctl -f`

5. Try running `gunicorn` service manually by running the code inside the lab4 service.

   **`sudo systemctl stop lab4`**

   **`/home/ec2-user/course/lab4/venv/bin/gunicorn --reload -w 4 -b 127.0.0.1:8004 app:app`**

   Remember to restart the lab4 service when you have it working\!

   **`sudo systemctl stop lab4`**

6. Use the `git diff` command to see which lines you’ve changed in the git repo.
7. Post a question in the [class forum on Canvas.](https://canvas.harvard.edu/courses/150159/discussion_topics)
8. [Ask TA’s for help](mailto:cscie-11-staff@googlegroups.com)\!

**GET AN A**

To get an A you need to:

1. Create an API\_KEY and an API\_SECRET\_KEY and store them in a file called `/home/ubuntu/lab4-answers.yaml.` It should look like this:

   `API_KEY: "lab4:27cb6bef97f29b71"`
   `API_SECRET_KEY: "04238c0e048c5d2ba4a1657b497d9a83"`

2. Use this information to post a message to your message board with the text “Give me an A”

When you think you have it all working, check with:

`$ e11 check lab4`

And request grading with:

`$ e11 grade lab4`

You can run the `grade` command as many times as you want. We will record your highest grade in Canvas the week after the lab is due.

# **Going Even Further** {#going-even-further}

Here are some other ideas for extending this lab:

* Expand the SQLite database and server application to record the IP address of the client.
* Add resource limiting so that each API key can only be used a certain number of times. This requires tracking how many times each API key can be used and refusing to process requests when a limit is reached.
* Add rate limiting to the system so it cannot execute more than NN requests every minute, where NN is a value stored in the database with a default of 1\.
* Add a page to the web application to print a status report.
* Add a page to the web application to print a list of all the API keys, when each was last used, and the last IP address (but not the secret hash\!)
* Add logs to the SQLite database to track each use of the server, and add a API-protected page on the web server to show the logs.

Here are some tutorials you may find useful:

* [Click and Python: Build Extensible and Composable CLI Apps](https://realpython.com/python-click/) (Real Python)

[image1]: <images/4-logo.png>
[image2]: <images/4-database.png>
