# **![][image1]**

# **CSCI E-11: Artificial Intelligence, the Internet-of-Things, and Cybersecurity** **Harvard Extension School** **Spring 2026**

# **Lab \#5: Turn your message board into a photoboard\!**

[Introduction and Lab Objectives](#introduction-and-lab-objectives)

[Building on Lab 4](#building-on-lab-4)

[Getting Started — Read The Docs\!](#getting-started-—-read-the-docs!)

[Amazon S3](#amazon-s3)

[Application — Security Analysis](#application-—-security-analysis)

[Application — New Functional Specifications](#application-—-new-functional-specifications)

[Getting Started 1 \- Give your instance permission to access S3](#getting-started-1---give-your-instance-permission-to-access-s3)

[Getting Started 2 \- Add the “lab5” Virtual Host and gunicorn proxy](#getting-started-2---add-the-“lab5”-virtual-host-and-gunicorn-proxy)

[Create and test your own S3 Bucket](#create-and-test-your-own-s3-bucket)

[Create an API Key](#create-an-api-key)

[Test your application](#test-your-application)

[Debugging](#debugging)

[GET AN A](#get-an-a)

[For uploads that are too large:](#for-uploads-that-are-too-large:)

[For uploads that are not JPEG:](#for-uploads-that-are-not-jpeg:)

[What You Will be Graded On](#what-you-will-be-graded-on)

[Going Even Further](#going-even-further)

# **Introduction and Lab Objectives** {#introduction-and-lab-objectives}

Welcome to the fifth lab\! In this lab we will modify our message board from the Lab \#4 to allow images to be uploaded and displayed, creating a photoboard\!

Objectives for this lab:

* Learn about S3, Amazon’s Simple Storage service. We’ll use S3 to store images.
* Learn how we allow the JavaScript client to upload directly to S3 with a “signed post,” and how we allow it to download directly with a “signed get.”

In addition to the new S3 functionality we discussed above, here is the additional functionality that the application requires:

1. The Python application will need a new API called `/api/post-image` that will:

   1. Validate the API\_KEY and then provide the JavaScript application with a signed URL to use to upload the image.

2. Likewise, we will have a new API called `/api/list-images` that will be similar to `/api/list-messages`, except that it will provide the client with a list of signed URLs, one for each message.

   1. The API will generate a presigned URL to allow the JavaScript client to display the images from S3. This API will does not validate the API\_KEY: if it did, then only people with a valid API\_KEY could view the images\!

   2. The list of all the messages and linked images will then be returned as a JSON object which will be displayed by the client.

3. Because we are now executing the upload with a JavaScript function, rather than the browser’s built-in form handler, we need this add additional functionality as ell:
   1. The JavaScript application will only enable the \<upload\> button if an \<API\_KEY\> and  \<API\_SECRET\_KEY\> and an image to be uploaded are provided.
   2. When the \<upload\> button is pressed, the JavaScript application running in the browser will:
      1. Run the `/api/new-image` API with the API\_KEY, API\_SECRET\_KEY and length of the image as parameters.
      2. Receive a dictionary from the server that includes information for sending the image to S3 via signed HTTP POST.
      3. Post the image to S3.
      4. Run the `list_messages()` function so that the newly uploaded image is displayed.

(Note: The maximum size of an HTTP POST to AWS S3 is 5GB, so we shouldn’t have any size limitations. If you ever build a production system that needs to upload more than 5GB at a time, you can upload up to 50GB using an [AWS multipart upload](https://docs.aws.amazon.com/AmazonS3/latest/userguide/mpuoverview.html).)

When two functions in JavaScript are defined with the same name, the second one replaces the first. Therefore the new JavaScript application will have a new list\_messages() function that will run instead of the old one.

# **Building on Lab 4**  {#building-on-lab-4}

This lab builds upon the AWS instance that we’ve been using.

If you shut down your AWS instance (or if it failed — that happens sometimes) you will need to create a new instance and re-register it with the `e11` server and set up nginx.

In Lab 4 we added support for *smashedemail-lab4.csci-e-11.org* to nginx web server and added another Let’s Encrypt TLS certificate.

Lab 5 builds upon Lab 4\. In particular, most of the files in the [lab5 folder of the git repo](https://github.com/Harvard-CSCI-E-11/spring25/tree/main/lab5/app) are copies of the same files in the lab4 folder. The only files that are different will be:

	`lab5/Makefile` — contains new targets

	`lab5/README.m`d — describes what’s different

	`lab5/lab5.service` — A new Linux service to run gunicorn for the lab5 server on port 8005\.

	`lab5/lab5-nginx-patch` — Now we `proxy_pass` to port `8005`

	`lab5/server/image_controller.`py — Uploading and downloading of images to S3

	`lab5/server/schema_lab5.sql` —The new `images` table in the SQLite3 database.

We’ve avoided modifying the other files. The file `main.py` already imports the file `image_controller.py` (the code catches the ImportError that results if the module is not present), and the database controller reads and executes all of the files sending `.sql` in the `app` directory. In fact, many of the entries in the `server/` directory are actually symbolic links to the versions of the same files in either the `lab_common` or the `lab4` directory:

**`spring26/lab5/server:`**
**`Length  Entry (-> target)`**
**`------`**
    **`0   __init__.py`**
  **`192   __pycache__`**
  **`448   .`**
  **`512   ..`**
   **`26   apikey.py -> ../../lab_common/apikey.py`**
   **`22   db.py -> ../../lab_common/db.py`**
 **`8457   image_controller.py`**
   **`25   main.py -> ../../lab4/server/main.py`**
   **`39   message_controller.py -> ../../lab4/server/message_controller.py`**
   **`33   schema_lab4.sql -> ../../lab4/server/schema_lab4.sql`**
  **`671   schema_lab5.sql`**
   **`23   static -> ../../lab_common/static`**
   **`26   templates -> ../../lab_common/templates`**
  **`319   todo.js`**

# **Getting Started — Read The Docs\!** {#getting-started-—-read-the-docs!}

This assignment makes use of S3.

## **Amazon S3** {#amazon-s3}

S3 is an object storage system, where “object” means “any digital object consisting of one or more bytes and associated metadata.” S3 stores objects in “buckets.”

You used S3 in lab1 to send us the name and IP address of your instance — this was a little non-standard. S3 is not normally used to send messages. Instead, Amazon has a different services called the Simple Queue Service that is used for sending messages.

* We used S3 because we didn’t want you to learn yet another Amazon service (and it was slightly different on our side).
* However, because we didn’t know your account number in advance, we had to set up our S3 bucket so that *anyone on the Internet could send a file into our bucket\!*
* To minimize the potential for abuse, we configured our bucket so that:
  * You could only upload objects under a specific predefined prefix.
  * You could not list or read any of the files that were uploaded.

In this lab you will create a bucket and store each photo as a named “object.” Unlike our somewhat wide-open S3 bucket:

* Your S3 bucket will only be readable or writable by your account — specifically, you at the command line, and programs running on your authenticated instance.
* We will then use *signed posts* and *signed URLs* to make possible to send data directly from your web browser (which is not authenticated on your account) to the S3 bucket and from the S3 bucket back to your web browser.

Before you get started, we’d like you to review these background materials:

Amazon S3:

* [Amazon S3 \- Cloud Object Storage \- AWS](https://aws.amazon.com/s3/)
* [Amazon S3 Pricing \- Cloud Object Storage](https://aws.amazon.com/s3/pricing/)
  * Don’t request a quote\! Just scroll to the bottom. It’s cheap\!
* [Download and upload objects with presigned URLs \- Amazon Simple Storage Service](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html)
* [Cross-origin resource sharing \- Wikipedia](https://en.wikipedia.org/wiki/Cross-origin_resource_sharing) (info about CORS)

# **Application — Security Analysis** {#application-—-security-analysis}

Images present more security issues than text messages. Before we started to design our application, we thought about ways that the system could be used by an attacker. We came up several possibilities:

* An attacker might use the system to achieve unlimited free storage with Amazon S3.
* An attacker might use the system to store or distribute content that is objectionable or even illegal.
* Users might upload photos that are really big. Remember, we pay for every gigabyte that’s stored (although we don’t pay for upload bandwidth).
* Users might upload files other than photos.

We will address the first two of these issues by only allowing images to be uploaded by authenticated users. If users upload too much stuff, you can contact them. If they upload information that is illegal, you can report them to law enforcement.

Digging deeper, if you were hosting this application in a production environment, how would you know if a user uploaded illegal or questionable data? What would your terms of service look like? You can see the challenges of allowing user-created content and why those terms-of-service pages are so long.

# **Application — New Functional Specifications** {#application-—-new-functional-specifications}

In addition to uploading messages, we want to be able to upload images. However, uploading images is more complex\! We’re going to need new functionality.

1. We will store images in an S3 bucket. JavaScript running in the web browser client will upload images directly to S3, and the S3 will serve images to the browser using https. To prevent abuse, the S3 bucket will use Amazon’s highly restrictive S3 access control rules (the default).
   1. Uploads will be “presigned” by your python application on the server; they will only be signed for clients that have valid API\_KEY and corresponding API\_SECRET\_KEYs.
   2. Likewise, downloads will be “presigned” by the server, but they will be presigned for anyone who is accessing the photoboard. This gives your application the ability to rate-limit downloads to the same IP address or to shut off downloads that are being abused, should you choose to do so.
2. Because of the added complications of……., we can no longer use the web browser’s built-in POST command. So we will have a new JavaScript function that will:
   1. Add a button to select an image to upload.
   2. Change the title on the form’s button from a SUBMIT button that uploads the form to an UPLOAD button that runs a JavaScript function.
   3. Post the message (if one is provided).
   4. Get a presigned URL for uploading the image.
   5. Post the image

# **Getting Started 1 \- Give your instance permission to access S3** {#getting-started-1---give-your-instance-permission-to-access-s3}

1. Go back to the AW3 IAM \> Roles \> EC2\_Class\_Role page.
2. Click the “Add permissions” button
3. Select Attach Policies
4. Search for and add the **AmazonS3FullAccess** policy.
5. When you are done, the EC2\_Class\_Role should look like this:

   ![][image2]

You can test that you got this right by logging into your instance and typing:

	`$ aws s3 ls`

*If you see an error:* you have not yet added the policy to role, or the EC2 instance is using a different role. Please check the instructions above.

*If you get no output and just get another prompt:* Congratulations\! You have it configured properly. You received no output because you currently have no AWS S3 buckets associated with your AWS account.

# **Getting Started 2 \- Add the “lab5” Virtual Host and gunicorn proxy** {#getting-started-2---add-the-“lab5”-virtual-host-and-gunicorn-proxy}

**Note:** Lab5 has a different API key database than Lab4, so you will need to make new API keys. Please repeat those steps, but this time add support for the corresponding lab5 hostname and certificate. Specifically:

1. Use `certbot -d` to extend your certificate to include hostnames for [*`smashedemail.csci-e-11.org`](http://smashedemail.csci-e-11.org)* as well as for [*`smashedemail-lab2.csci-e-11.org`](http://smashedemail-lab2.csci-e-11.org)* through [*`smashedemail-lab5.csci-e-11.org`](http://smashedemail-lab5.csci-e-11.org)*. Your command will look something like this:

      `sudo certbot --nginx --expand  \`
                `--cert-name smashedemail.csci-e-11.org \`
                `-d smashedemail.csci-e-11.org \`
                `-d smashedemail-lab3.csci-e-11.org \`
                `-d smashedemail-lab4.csci-e-11.org \`
                `-d smashedemail-lab5.csci-e-11.org`


   NOTE: Remember *smashedemail* must be your information.

2. Edit the `nginx` configuration file `/etc/nginx/sites-available/default` so that the site for `lab5` is proxied to port `8005`.

   1. As you did in lab3, edit the file `/etc/nginx/sites-available/default` and find the new `server {` block that contains the `server_name smashedemail-lab5.csci-e-11.org;` command.

   2. Look for this code:

           `location / {`

                   `# First attempt to serve request as file, then`

                   `# as directory, then fall back to displaying a 404.`

                   `try_files $uri $uri/ =404;`

           `}`

   And change it to:

           `location / {`

           `proxy_pass http://127.0.0.1:8005;`

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

   NOTE: Make sure that you set the port to be 8005\! (Each lab uses a different port number\!)

   Test the config file with:

      `$ sudo nginx -t`

   ## **Restart the servers**





3. Install the `lab5.service` file from the `/home/ubuntu/spring26/lab5` directory.

   `$ sudo cp lab5.service /etc/systemd/system/`

   Restart both nginx and the gunicorn process with:

   `$ sudo systemctl restart nginx lab5`

4. Create an API\_KEY and an API\_SECRET\_KEY and put them in a file called `/home/ubuntu/lab5-answers.yaml` so we can find it.

**Be sure you are in the lab5 directory:**

`$ cd ~/spring26/lab5`

Then execute these commands:

`$ make init-db` — Initializes the database (erasing any API\_KEYs)

`$ make new-apikey` — Creates a new API\_KEY and API\_SECRET\_KEY. Save these\!

`$ make dump-db` — Shows you what is in the database. Notice that the API\_SECRET\_KEY is not stored, only the hashed key and the hashing parameters.

When you complete these tasks, you can type `e11 check lab5` to verify  that the webserver is set up properly. It will also tell you what needs to be completed to get an A on the lab.

Of course, the additional checks required for lab5 will fail until you complete\! This is called [test-driven development](https://en.wikipedia.org/wiki/Test-driven_development).

# **Create and test your own S3 Bucket** {#create-and-test-your-own-s3-bucket}

This lab requires that you create an S3 Bucket and configure its CORS policy.

Your S3\_BUCKET name for this app is defined in the file lab5/app/image\_validate.py and is based on your instance’s hostname and the lab number::

`S3_BUCKET_PREFIX = socket.gethostname().replace(".", "-")`
`S3_BUCKET_SUFFIX = "-images-bucket"`
`S3_BUCKET = S3_BUCKET_PREFIX + db.get_lab_name() + S3_BUCKET_SUFFIX`

You can change it if you wish. The CORS policy is specified in the file lab5/app/image\_controller.py; it is quite permissive:

`# Define the Cross Origin Resource Sharing Policy for the S3 bucket.`
`# This tells the browser that it is safe to retrieve the S3 objects it gets the redirect`
`# from the application.`
`# See:`
`# https://en.wikipedia.org/wiki/Cross-origin_resource_sharing`
`# https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS`

`CORS_CONFIGURATION = {`
    `"CORSRules": [`
        `{`
            `"AllowedOrigins": ["*"],  # Allow all origins with presigned POST and GETs`
            `"AllowedMethods": ["GET", "POST", "PUT"],  # Methods to allow`
            `"AllowedHeaders": ["*"],  # Allow all headers`
            `"MaxAgeSeconds": 3000,  # Cache duration for preflight requests`
        `}`
    `]`
`}`

Now **create the bucket and set the CORS policy** by logging in to your instance and typing:

`$ cd $HOME/spring26/lab5`
`$ make init-s3`

# **Create an API Key**  {#create-an-api-key}

Use the new-apikey Makefile target to create a lab 5 API key:

`$ make new-apikey`

# **Test your application** {#test-your-application}

Your application should be up and running now.

1. Go to [https://smashedemail-lab5.csci-e-11.org/](https://smashedemail-lab5.csci-e-11.org/) and post a message with an image. If it works, you’ll see the message and photos (here we upload two):

![][image3]

# **Debugging** {#debugging}

Is something not working? Start by look over the “Debugging” section of [CSCI E-11 Spring 2025 Lab \#4](https://docs.google.com/document/d/16dELJKbumS27bscnJT3eQbs-q4kAQXPun4l9-U1WDJc/edit?tab=t.0#heading=h.x3ksbgec8yoq)

Here are other things to try:

1. Always start by looking at the log files\!
2. Look at the last 100 lines of your webserver’s with the journalctl command:

   `$ journalctl -r -u lab5.service -n 100`

3. Use the `git diff` command to compare what’s different between your version of the git repo and the one on GitHub:

   `$ cd $HOME/spring26/lab5`

   `$ git diff origin`

4. Were the pictures uploaded to S3? Take a look:

   `$ aws s3 ls` 	— *this command should list all of your s3 buckets*

   `$ aws s3 ls s3://yourbucket/` — *this command should list the contents of yourbucket (which you should change to be your actual bucket name)*

5. Post a question in the class forum on Canvas.



# **GET AN A** {#get-an-a}

There are two security issues we identified at the top of this document that are easily address: uploads that are too large, and uploads that are not JPEGs.

## **For uploads that are too large:** {#for-uploads-that-are-too-large:}

1. Review the AWS web page [generate\_presigned\_post \- Boto3 1.41.5 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/generate_presigned_post.html) .
2. Modify the file `image_validate.py` so that uploads smaller than 125 bytes or larger than 4MiB are not accepted (you will find the variable `MAX_IMAGE_SIZE_BYTES` already defined in the file `image_validate.py`.

## **For uploads that are not JPEG:** {#for-uploads-that-are-not-jpeg:}

The call to generate\_presigned\_post already restricts the uploads to files that are the JPEG MIME type. In practice, this simply means that they end with the `.jpeg` extension.  What’s needed is to *validate* the file after it has been uploaded.

We will store the validation in the boolean variable `validated` is that part of the database schema.

1. Modify the file `image_validate.py` so that the uploaded data is validated. If not validated, delete the uploaded. Read through the code \- we’ve given you most of what you need to get this done.

# **What You Will be Graded On** {#what-you-will-be-graded-on}

The grader will check the following:

* Is the web server properly configured for Lab5?
* Does the API key work to request signed URLs?
* Can an object be uploaded with the signed URL?

# **Going Even Further** {#going-even-further}

Here are some other ideas for extending this lab:

* Allow uploads in other formats — in particular, the HEIC format, which is commonly used on iPhones.
* Add summary statistics about the uploaded images.

If you want a deep-dive on S3 and all of the amazing things it can do, you may enjoy watching this:

* [AWS re:Invent 2024 - What’s new with Amazon S3 (STG212)](https://www.youtube.com/watch?v=pbsIVmWqr2M) (55 min)

[image1]: <images/5-logo.png>
[image2]: <images/5-s3policy.png>
[image3]: <images/5-uploads.png>