# **![][image1]**

# **CSCI E-11: Artificial Intelligence, the Internet-of-Things, and Cybersecurity** **Harvard Extension School** **Spring 2027**

# **Lab \#2 \- Public & Confidential — A web server with password-based access control**

[Introduction and Lab Objectives](#introduction-and-lab-objectives)

[Building on Lab1](#building-on-lab1)

[Getting Started — First Read The Docs\!](#getting-started-—-first-read-the-docs!)

[Verify and Update your inbound rules.](#verify-and-update-your-inbound-rules.)

[Set your instance’s hostname.](#set-your-instance’s-hostname.)

[Install the nginx web server](#install-the-nginx-web-server)

[Test nginx on port 80 (not secure)](#test-nginx-on-port-80-\(not-secure\))

[Upgrading nginx to use a TLS certificate from Let’s Encrypt](#upgrading-nginx-to-use-a-tls-certificate-from-let’s-encrypt)

[Create a simple website](#create-a-simple-website)

[Verify that your web pages are visible](#verify-that-your-web-pages-are-visible)

[Get an A: Fix your app](#get-an-a:-fix-your-app)

[If you have problems, here are some commands you can type:](#if-you-have-problems,-here-are-some-commands-you-can-type:)

[Getting Automated Help](#getting-automated-help)

[Getting Graded](#getting-graded)

[Going Further](#going-further)

# **Introduction and Lab Objectives** {#introduction-and-lab-objectives}

Welcome to the second lab\! We will continue to use Amazon Web Services for our labs.

Objectives for this lab:

* Install the Nginx webserver on your AWS instance and verify that it works.
* Obtain a Let’s Encrypt server certificate for your web server using the DNS name that you obtained in the first lab.
* Deploy a simple website with two pages — one that is available to everybody, one that contains sensitive data and is password-protected.

What we will test when you ask the lab to be graded with the **`e11`** command:

* We will verify that you are running a web server on port 80
* We will verify that you are running a “secure” webserver on port 443 with a Let’s Encrypt certificate.
* We will verify that you have properly password-protected the sensitive web page.

# **Building on Lab1** {#building-on-lab1}

This lab builds on the EC2 instance that was created in Lab \#1. If you stopped it, now is a good time to restart it and re-register it (using “**`e11 register`**”). If you terminated it, please recreate the instance and re-run the installer script, then re-register it with the E11 course management system.

# **Getting Started — First Read The Docs\!** {#getting-started-—-first-read-the-docs!}

This assignment assumes some familiarity with HTTP, TLS, SQL and Python. We are providing you with these resources that you might want to read first:

* [An overview of HTTP](https://developer.mozilla.org/en-US/docs/Web/HTTP/Overview)
* [Serve Static Content | NGINX Documentation](https://docs.nginx.com/nginx/admin-guide/web-server/serving-static-content/)
* [Restricting Access with HTTP Basic Authentication | NGINX Documentation](https://docs.nginx.com/nginx/admin-guide/security-controls/configuring-http-basic-authentication/)

# **Verify and Update your inbound rules.** {#verify-and-update-your-inbound-rules.}

It’s possible that you created your instance with restrictive inbound rules on its firewall. If you created the instance in Lab \#1 without checking the boxes for “Allow inbound HTTP” and “Allow inbound HTTPS,” then Lab \#2 won’t work for you.

So right now, you should check your instance’s inbound rules by selecting in the EC2 control panel and inspecting the inbound rules of the security group that is used by the instance. These rules only allow inbound SSH.

You can view these rules by visiting EC2 \> Security Groups, and selecting the security group that likely has the words “launch-wizard” within. You will see a screen similar to the following:

![][image2]

Notice how, in the case above, only SSH is available. Inbound HTTPS and HTTP are not allowed in the case of this above screenshot.

If that’s what you see, you will need to add permissions for HTTP and HTTPS. You can do this by clicking “Edit inbound rules.” You will then see:

![][image3]

Click the “Add Rule” and add an inbound rule to allow inbound HTTP (port 80\) with the Source of any IP address (0.0.0.0/0).

Now click "Add Rule" a second time and add a second inbound rule to allow inbound HTTPS (port 443), again with a source of any IP address (0.0.0.0/0). Your inbound rules will then look like this:

![][image4]

Now click “Save rules:”

![][image5]

That’s better\!

# **Set your instance’s hostname.** {#set-your-instance’s-hostname.}

Remember that we sent you an email message with your instance’s hostname? That hostname is probably *smashedemail*.csci-e-11.org, where *smashedemail* is based on your email mailbox (what’s to the left of the @ sign) and a portion of the domain name (what’s to the right of the @ sign).

Before proceeding, make sure that you have your *smashedemail* on hand. Likely, you received a prior email from us with the subject line “CSCI E-11 Update: New DNS records created for”, etc. Your *smashedemail* will appear within the “Hostname” field in that email.

It’s now time to configure your instance to use that hostname\!

Connect to your instance and type this command:

	`$ sudo hostnamectl hostname smashedemail.csci-e-11.org`

(Remember, replace *`smashedemail`* `with the particular hostname that we mailed you.)` As always, you can find out what the `hostnamectl` command does by looking at the online documentation:

`$ man hostnamectl`

We’ve had some problems when changing the hostname with the ssh server, so you might want to restart that as a preventative measure:

`$ sudo systemctl restart ssh`

Verify that the DNS hostname for your instance has been created by going to another computer (not your EC2 instance window; like a Windows, Mac, or Linux machine) and typing:

`$ nslookup smashedemail.csci-e-11.org`

You should see something like this:

`$ nslookup smashedemail.csci-e-11.org`
`Server:		127.0.0.53`
`Address:	127.0.0.53#53`

`Non-authoritative answer:`
`Name:	smashedemail.csci-e-11.org`
`Address: 3.14.68.84`

The first two lines of the command’s output indicate that we are using the DNS server `127.0.0.53` (an IPv4 address) on port `53` (the standard DNS port).

The second block is the DNS lookup of the host. It says `Non-authoritative answer` because the response came from a server that is not the authoritative server for the [`csci-e-11.org`](http://csci-e-11.org) domain. Here the Address should match the IPv4 address of your instance.

# **Install the nginx web server** {#install-the-nginx-web-server}

Type this command on your server to install the nginx web server:

**`$ sudo apt -y install nginx`**

The nginx is a lightweight, “modern” web server that was publicly released in 2004\. It is open source. It is now maintained by F5. You can learn more about nginx at [Nginx \- Wikipedia](https://en.wikipedia.org/wiki/Nginx). Another widely used webserver is the Apache web server.

# **Test nginx on port 80 (not secure)** {#test-nginx-on-port-80-(not-secure)}

From the command line, type:

`$ curl localhost:80`

You should see something like:

`ubuntu@ip-172-31-33-13:~$ curl localhost:80`
`<!DOCTYPE html>`
`<html>`
`<head>`
`<title>Welcome to nginx!</title>`
`<style>`
`html { color-scheme: light dark; }`
`body { width: 35em; margin: 0 auto;`
`font-family: Tahoma, Verdana, Arial, sans-serif; }`
`</style>`
`</head>`
`<body>`
`<h1>Welcome to nginx!</h1>`
`<p>If you see this page, the nginx web server is successfully installed and`
`working. Further configuration is required.</p>`

`<p>For online documentation and support please refer to`
`<a href="http://nginx.org/">nginx.org</a>.<br/>`
`Commercial support is available at`
`<a href="http://nginx.com/">nginx.com</a>.</p>`

`<p><em>Thank you for using nginx.</em></p>`
`</body>`
`</html>`
`ubuntu@ip-172-31-33-13:~$`

Let’s try this in a web browser:

In your web browser, try going to [http://*smashedemail*.csci-e-11.org/](http://username.csci-e-11.org/), where *smashedemail* is really the hostname we previously gave you.

Note that we are using “http:” and not “https:”

If you are using a modern web browser, you may get a security warning like this:

![][image6]

If so, click “Continue to site.” You should see the message “Welcome to nginx\! If you see this page, the nginx web server is successfully installed and working. Further configuration is required” in your web browser.

Since you are the site owner, you will now upgrade your site to HTTPS.

# **Upgrading nginx to use a TLS certificate from Let’s Encrypt** {#upgrading-nginx-to-use-a-tls-certificate-from-let’s-encrypt}

We will use the Let’s Encrypt `certbot` to install and manage the TLS (Transport Layer Securityh) certificate on the nginx server.

nginx stores its configuration files in the directory `/etc/nginx`. Let’s look at them:

`ubuntu@ip-172-31-14-166:~$ ls -lF /etc/nginx/`
`total 68`
`drwxr-xr-x 2 root root 4096 May 27 03:28 conf.d/`
`-rw-r--r-- 1 root root 1125 Nov 30  2023 fastcgi.conf`
`-rw-r--r-- 1 root root 1055 Nov 30  2023 fastcgi_params`
`-rw-r--r-- 1 root root 2837 Nov 30  2023 koi-utf`
`-rw-r--r-- 1 root root 2223 Nov 30  2023 koi-win`
`-rw-r--r-- 1 root root 5465 Nov 30  2023 mime.types`
`drwxr-xr-x 2 root root 4096 May 27 03:28 modules-available/`
`drwxr-xr-x 2 root root 4096 May 27 03:28 modules-enabled/`
`-rw-r--r-- 1 root root 1446 Nov 30  2023 nginx.conf`
`-rw-r--r-- 1 root root  180 Nov 30  2023 proxy_params`
`-rw-r--r-- 1 root root  636 Nov 30  2023 scgi_params`
`drwxr-xr-x 2 root root 4096 Aug 13 20:46 sites-available/`
`drwxr-xr-x 2 root root 4096 Aug 13 20:46 sites-enabled/`
`drwxr-xr-x 2 root root 4096 Aug 13 20:46 snippets/`
`-rw-r--r-- 1 root root  664 Nov 30  2023 uwsgi_params`
`-rw-r--r-- 1 root root 3071 Nov 30  2023 win-utf`
`ubuntu@ip-172-31-14-166:~$`

The `root root` on every line means that the file is owned by the `root` user (the superuser) and the `root` group (the superuser's group). We can read these files and access the directories, but the file permissions are set up so that we cannot modify them without using the `sudo` command.

Pay attention to the `-lF`

	`-`	— The hyphen character tells the `ls` command that options will follow
	`l`	— The `l` tells the `ls` command to provide a "long" directory listing.
	`F`	— The `F` says that directories should end with a `/`.

You can learn more about the `ls` command by typing `man ls`.

The web server can manage multiple websites on the same AWS instance. Sites are determined by domain name. The key directories that matter are `sites-available`, which contains a configuration file for every site that your web server maintains, and `sites-enabled`, which has a symbolic link to each of the available websites.

Initially there is only the default website:

`ubuntu@ip-172-31-14-166:~$ ls -lF /etc/nginx/sites-available/`
`total 4`
`-rw-r--r-- 1 root root 2412 Nov 30  2023 default`
`ubuntu@ip-172-31-14-166:~$`

And it is enabled:

`ubuntu@ip-172-31-14-166:~$ ls -lF /etc/nginx/sites-enabled/`
`total 0`
`lrwxrwxrwx 1 root root 34 Aug 13 20:46 default -> /etc/nginx/sites-available/default`
`ubuntu@ip-172-31-14-166:~$`

The `->` means that the name `default` in the directory `/etc/nginx/sites-enabled/` is a symbolic link that points to the file `/etc/nginx/sites-available/default.`

All of the `nginx` configuration files are kept in the `/etc/nginx/sites-available` directory; they are enabled when a symbolic link is placed in the `/etc/nginx/sites-enabled` directory.  Confused? Read [Symbolic link \- Wikipedia](https://en.wikipedia.org/wiki/Symbolic_link)

Look at the contents of the file `/etc/nginx/sites-available/default`:

`$ cat /etc/nginx/sites-available/default`

**BEFORE YOU DO ANYTHING ELSE, MAKE A BACKUP OF THIS FILE\!**

`$ sudo cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.bak`

Now install the certbot program:

`$ sudo apt -y install certbot python3-certbot-nginx`

Ask certbot to create a certificate for your site. This will automatically edit the configuration files. (Notice the double hypen.)

`$ sudo certbot --nginx -d smashedemail.csci-e-11.org`

Then restart the web server:

`$ sudo systemctl restart nginx`

And finally, verify that you are now running with a TLS certificate:

`$ curl https://smashedemail.csci-e-11.org/`

Remember — you will actually type your hostname instead of `smashedemail.csci-e-11.org.` For example:

![][image7]

Or, in a web browser:

![][image8]

Click the icon to the left of the hostname in the address bar to look at the certificate and verify that you are using a Let’s Encrypt certificate. On each of the images below, the red circle indicates where you should click:

![][image9]![][image10]

![][image11]

![][image12]

Look to see how certbot modified your configuration file:

`$ diff /etc/nginx/sites-available/default.bak  /etc/nginx/sites-available/default`

The `certbot.timer` service will automatically check your certificates twice a day and renew them as necessary.

# **Create a simple website** {#create-a-simple-website}

When `nginx` serves static web pages, what is happening behind the scenes is this:

* `nginx` receives the web request.
* `nginx` checks the domain and matches up to the specific configuration file
* `nginx` looks at the directory in the configuration file for `root`. In the default file, the `root` is `/var/www/html`
* If the path specified is the name of a directory and a file, `nginx` sends that file to the web browser.
* If the path specified is the name of a directory, `nginx` looks for a file specified by the  `index` directive in the configuration file and sends that file.

In the default configuration file, the root and index directives looks like this:

	`root /var/www/html;`

	`index index.html index.htm index.nginx-debian.html;`

Thus, when you access your webserver, the file `/var/www/html/index.nginx-debian.html` gets sent to the web browser.

You will now create two web files:

`/var/www/html/public.html`
`/var/www/html/confidential/confidential.html`

By default, the `/var/www/html` directory is owned by `root` — that is, the superuser. We can see these directories but we cannot add files to them without using the `sudo` command. Below, we will use the `sudo` command to change the ownership of this directory to the `ubuntu` user — that is, the same user that we are logged in as:

`$ sudo chown -R ubuntu /var/www/html/`
`$ mkdir /var/www/html/confidential/`

We have also given you two files that you can use as a starter point. You can install them with:

`$ cp $HOME/course/lab2/public.html /var/www/html/`
`$ cp $HOME/course/lab2/confidential/confidential.html /var/www/html/confidential/`

These `cp` commands will fail if you have not changed the ownership of the directory with the chown command above\!

# **Verify that your web pages are visible** {#verify-that-your-web-pages-are-visible}

This is the easy part\! Go to these two URLs and verify that both of your web pages are visible:

[https://*smashedemail*.csci-e-11.org/public.html](https://smashedemail.csci-e-11.org/public.html)

[https://*smashedemail*.csci-e-11.org/confidential/confidential.html](https://smashedemail.csci-e-11.org/confidential/confidential.html)

Oh wait\! We want the data in the `confidential/` directory to be password-protected\!

# **Get an A: Fix your app** {#get-an-a:-fix-your-app}

Now your goal is to password-protect the `confidential/` directory so that it can only be read using a username/password.

You will be using using these instructions, with modification: [https://docs.nginx.com/nginx/admin-guide/security-controls/configuring-http-basic-authentication/](https://docs.nginx.com/nginx/admin-guide/security-controls/configuring-http-basic-authentication/)

Here’s how you will do it:

1. You will first install the `htpasswd` utility to create a password file.

   To install `htpasswd` use:
   `$ sudo apt install apache2-utils`



2. You will create the password file `/home/web-passwords` with the username `student` and the password `secret`.  The command you use will look like this:

   `$ sudo htpasswd -c /home/web-passwords`

   For instructions on how to use `htpasswd`, type:

   `$ man htpasswd`

   (Question: Why does doc warn so strenuously against using the \-b option? Hint: It’s not just because someone might be looking over your shoulder as you type the password.)

3. You will modify the configuration file `/etc/nginx/sites-available/default` to protect the `location` `/confidential`. Do this by adding these lines:

           **`location /confidential {`**
                    **`auth_basic "CSCI E-11";`**
                    **`auth_basic_user_file /home/web-passwords;`**
           **`}`**

   You will find the lines to add in the file `course/lab2/lab2-nginx-patch`.

   ***Be sure to put it in the correct section inside the*** `server {` ***section—the one that contains the*** `server_name` ***directive with your smashed email domain and the*** `listen 443` ***ssl directive.***

   You can edit the configuration file with this command:

   `$ sudo nano /etc/nginx/sites-available/default`

4. Test the configuration file with **`sudo nginx -t`**.
5. Restart the nginx server with **`sudo systemctl restart nginx`**.
6. The web server needs to be able to access the/home/web-passwords file. The nginx web server runs under the user `www-data`, so execute these commands:

   `$ sudo chgrp www-data /home/web-passwords`
   `$ sudo chmod 755 /home/web-passwords`



You will find instructions for how to set up the password-protected directory here:

* [Restricting Access with HTTP Basic Authentication | NGINX Documentation](https://docs.nginx.com/nginx/admin-guide/security-controls/configuring-http-basic-authentication/)

Once you have completed your task, go back to the two URLs and verify that the first page is visible without a password, but that the second page requires a password:

[https://*smashedemail*.csci-e-11.org/public.html](https://smashedemail.csci-e-11.org/public.html)

[https://*smashedemail*.csci-e-11.org/confidential/confidential.html](https://smashedemail.csci-e-11.org/confidential/confidential.html)

##

## **If you have problems, here are some commands you can type:** {#if-you-have-problems,-here-are-some-commands-you-can-type:}

test the configuration of the nginx web server with:

`$ nginx -t`

Look the nginx servers error log with:

`$ tail -f  /var/log/nginx/error.log`

Look the nginx servers access log with:

`$ tail -f  /var/log/nginx/access.log`

Look the nginx service log with:

`$ sudo journalctl -u nginx -f`

# **Getting Automated Help** {#getting-automated-help}

The `e11` command can find basic problems with this lab with this command:

`$ e11 check lab2`

# **Getting Graded** {#getting-graded}

You can request grading of your instance using the `e11 grade` command:

`$ e11 grade lab2`

You can run the `grade` command as many times as you want. The highest grade is the one that we will export to Canvas. We will record your highest grade in Canvas the week after the lab is due.

# **Going Further** {#going-further}

In this lab we set up a web server to serve static web pages.

It is possible to run applications within a web page. A popular way to do this is with the PHP language. (PHP is the language that Wikipedia is written in). You could install PHP with these commands:

`$ sudo apt install -y php-fpm php-mysql php-cli php-curl php-xml php-mbstring`
`$ sudo systemctl start php8.3-fpm`
`$ sudo systemctl status php8.3-fpm`

The `systemctl start` command starts up `php8.3-fpm`, the PHP 8.3 FastCGI Process Manager, which handles FastCGI requests from nginx. This program keeps a “pool” of worker processes alive and ready to go to handle your incoming PHP requests.

The `php8.3-fpm` program will run until your Ubuntu 26.04 instance shuts down. If you want it to restart automatically if your instance reboots, you need to enable it:

`$ sudo systemctl enable php8.3-fpm`

You would then add this block to the webserver’s default file to enable PHP processing on files ending `.php`:

`location ~ \.php$ {`
    `include snippets/fastcgi-php.conf;`
    `fastcgi_pass unix:/var/run/php/php8.3-fpm.sock;`
    `fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;`
    `include fastcgi_params;`
`}`

Ask yourself — what security concerns would you have if PHP were running?

**(If you do enable PHP, be sure to turn it off — reportedly it breaks the grader\!)**

[image1]: <images/2-logo.png>
[image2]: <images/2-securitygroup.png>
[image3]: <images/2-httprule.png>
[image4]: <images/2-httpsrule.png>
[image5]: <images/2-inboundrules.png>
[image6]: <images/2-certificateerror.png>
[image7]: <images/2-certbot.png>
[image8]: <images/2-nginx.png>
[image9]: <images/2-siteinfo.png>
[image10]: <images/2-connection.png>
[image11]: <images/2-security.png>
[image12]: <images/2-certificate.png>
