# **![][image1]**

# **CSCI E-11: Artificial Intelligence, the Internet-of-Things, and Cybersecurity** **Harvard Extension School** **Spring 2026**

# **Lab \#6: Adding Computer Vision**

[Introduction and Lab Objectives](#introduction-and-lab-objectives)

[Getting Started — Read The Docs\!](#getting-started-—-read-the-docs!)

[Amazon Rekognition](#amazon-rekognition)

[Building Upon Lab 5](#building-upon-lab-5)

[Application — Security Analysis](#application-—-security-analysis)

[Add the “lab6” Virtual Host and gunicorn proxy](#add-the-“lab6”-virtual-host-and-gunicorn-proxy)

[Give Your Instance More Permissions\!](#give-your-instance-more-permissions!)

[Create and test another S3 Bucket](#create-and-test-another-s3-bucket)

[Create an API Key](#create-an-api-key)

[Test your application](#test-your-application)

[Debugging](#debugging)

[GET AN A](#get-an-a)

[What You Will Be Graded On](#what-you-will-be-graded-on)

[Going Even Further](#going-even-further)

# **Introduction and Lab Objectives** {#introduction-and-lab-objectives}

Welcome to the sixth lab\! In this lab, we will modify our photoboard from Lab \#5 to analyze the uploaded images with Amazon’s Rekognition.

Objectives for this lab:

* Learn about and employ Amazon Rekognition, Amazon’s image analysis service.
* Extend the TLS certificate to include lab6 domain name.
* Install a new “lab6” service with a gunicorn proxy.
* Generate new API keys for use with this lab.
* Extend your instances permissions to include access to Rekognition.
* Create and utilize a new S3 Bucket for lab6.

# **Getting Started — Read The Docs\!** {#getting-started-—-read-the-docs!}

This assignment makes use of Rekognition.

## **Amazon Rekognition** {#amazon-rekognition}

Amazon Rekognition is Amazon’s face recognition Software as a Service (SaaS) system. It’s very similar to an open source system called [DeepFace](https://github.com/serengil/deepface) (in fact, it may in fact be DeepFace under the hood). Rekognition can create multidimensional vectors (called *embeddings*) that abstract the salient information from a face, and can make emotional judgements. Amazon has used Rekognition to scan the entire Internet Movie Database (IMDB, which Amazon bought in 1998), and can identify if there are any individuals in an uploaded image in the IMDB database.

Amazon Rekognition docs:

* [Image Recognition Software, ML Image & Video Analysis \- Amazon Rekognition](https://aws.amazon.com/rekognition/)
* [Amazon Rekognition – Pricing – AWS](https://aws.amazon.com/rekognition/pricing/)

For video learners, here are some videos from Amazon that we’ve looked at and recommend:

* [AWS re:Invent 2017 - Introducing Amazon Rekognition](https://www.youtube.com/watch?v=D1gj_9aKRJU) \- Rekognition was launched in 2016 with images, and 2017 with video. (3 minutes)
* [AWS re:Invent 2018: \[REPEAT 1\] Deep Dive on Amazon Rekognition, ft. Pinterest (AIM307-R1)](https://www.youtube.com/watch?v=jFgtImmEH7w) This overview tells you what it does and how to use it. (54 min)

# **Building Upon Lab 5** {#building-upon-lab-5}

Lab 6 builds upon Lab 5\. In particular, most of the files in the [lab6 folder of the git repo](https://github.com/Harvard-CSCI-E-11/spring26/tree/main/lab6/server) are symbolic links to the same files in the [lab5 folder](https://github.com/Harvard-CSCI-E-11/spring26/tree/main/lab5/server), the [lab4 folder](https://github.com/Harvard-CSCI-E-11/spring26/tree/main/lab4/server), and the [lab\_common](https://github.com/Harvard-CSCI-E-11/spring26/tree/main/lab_common) folder. The only files that are different will be:

	`lab6/Makefile` — contains new targets

	`lab6/README.m`d — describes what’s different

	`lab6/lab6.service` — A new Linux service to run gunicorn for the lab6 hostname

	`lab6/lab6-nginx-patch` — Now we `proxy_pass` to port `8006`

Before we get started modifying code. Ensure that you set up the Python environment.

	`$ poetry install`

We will also make a small change to `lab6/server/image_validate.py` (which is actually a link to the file in lab5).

Look for this code:

        `##### LAB6 - CELEBRITY RECOGNITION WITH AMAZON REKOGNITION #####`
        `try:`
            `# pylint: disable=unused-variable`
            `rekognition_client = boto3.client("rekognition",`
                                              `region_name=s3_client.meta.region_name)`
            `# INSERT LAB6 CODE HERE`
        `except BotoCoreError as e:`
            `celeb = []`
            `app.logger.error("rekognition error: %s",e)`
        `################################################################`

Change it to this:

        `##### LAB6 - CELEBRITY RECOGNITION WITH AMAZON REKOGNITION #####`
        `try:`
            `# pylint: disable=unused-variable`
            `rekognition_client = boto3.client("rekognition",`
                                              `region_name=s3_client.meta.region_name)`
            **`response = rekognition_client.recognize_celebrities( Image={"Bytes": image} )`**
            **`celeb = response.get("CelebrityFaces", [])`**
            **`app.logger.info("celeb=%s",celeb)`**
        `except BotoCoreError as e:`
            `celeb = []`
            `app.logger.error("rekognition error: %s",e)`

        `################################################################`

This modifies `image_validate.py` to run Rekognition on the image, extract the Celebrity Faces, and store the results in the  `celeb` Python variable. Amazon Rekognition is fast, so we can do this the first time the image is displayed. If Rekognition was slow, we might want to queue the analysis when the image is uploaded.

Later in the file you will see that we turn `celeb` into a JSON object, which we store in the database and return to the caller of the API. If the API is called again, the value will be retrieved directly from the database, which makes the system faster and avoids a second call to the REKOGNITION API:

	`# Update the database`
        `celeb_json         = json.dumps(celeb,default=str)`
        `detected_text_json = json.dumps(detected_text,default=str)`
        `c = conn.cursor()`
        `c.execute("UPDATE images set celeb_json=?,detected_text_json=? where image_id=?",`
                  `(celeb_json,detected_text_json,image_id))`
        `conn.commit()`

	`# and update what is return to the caller (row)`

        `row['celeb_json'] = celeb_json`
        `row['detected_text_json'] = detected_text_json`

# **Application — Security Analysis** {#application-—-security-analysis}

Images present more security issues than text messages. Before we started designing our application, we considered ways an attacker could use the system. We came up with three possibilities:

* An attacker might use the system as an open proxy for Amazon’s Rekognition engine.
  * A user might upload many images to our system to utilize our access to Rekognition leaving us paying the bill for their usage.
* An attacker might use the system to host illegal materials.
  * By uploading nefarious content to our message board leaving us to clean up our servers and purge illegal data.
* An attacker might use the system as free cloud storage.
  * We are offering a service to store “stuff” if we don’t put some checks in place, a user could just upload a multitude of files leaving us to pay for storage costs.

We will address these issues by allowing images to be uploaded only by authenticated users.

# **Add the “lab6” Virtual Host and gunicorn proxy** {#add-the-“lab6”-virtual-host-and-gunicorn-proxy}

This lab builds upon the AWS instance that we’ve been using.

* Use `certbot -d` to extend your certificate to include hostnames for [*`smashedemail.csci-e-11.org`](http://smashedemail.csci-e-11.org)* as well as for:
  * [*`smashedemail-lab2.csci-e-11.org`](http://smashedemail-lab2.csci-e-11.org)*
  * [*`smashedemail-lab3.csci-e-11.org`](http://smashedemail-lab2.csci-e-11.org)*
  * [*`smashedemail-lab4.csci-e-11.org`](http://smashedemail-lab2.csci-e-11.org)*
  * [*`smashedemail-lab5.csci-e-11.org`](http://smashedemail-lab2.csci-e-11.org)*
  * *`smashedemail-lab6.csci-e-11.org`*
1. Edit the `nginx` configuration file `/etc/nginx/sites-available/default` so that the site for `lab6` is proxied to port `8006`.

   (We did this in previous labs and it is left to you to expand on those previous examples and setup the reverse proxy to point at the correct code. )

2. Install the `lab6.service` file from the `/home/ubuntu/spring26/lab6` directory.

   (We also did this in previous labs — look to them for examples if you get stuck on this point.)

   Note: Don’t forget to restart both nginx and start your lab6 service.

   `$ sudo systemctl daemon-reload`

   `$ sudo systemctl restart nginx`

   `$ sudo systemctl start lab6`



3. Create an API\_KEY and an API\_SECRET\_KEY and put them in a file called `/home/ubuntu/lab6-answers.yaml` so we can find it. Be sure you are in the lab6 directory then run these commands:

   `$ make init-db`

   `$ make new-apikey | grep API | tee $HOME/lab6-answers.yaml`

The `grep` command extracts the two lines containing the letters `API`, which is the API key and the secret key.

The `tee` command displays the two keys and writes them to the specified file.

Now try out the new API key with your web application by uploading an image.

When you complete these tasks, you can use `e11 check lab6` to verify that the web server is properly set up. It will also tell you what you need to complete to get an A on the lab. Specifically, it will tell you that the Rekognition API is not working.

Of course, the additional checks required for lab6 will fail until you complete them\! This is called [test-driven development](https://en.wikipedia.org/wiki/Test-driven_development).

# **Give Your Instance More Permissions\!** {#give-your-instance-more-permissions!}

We want your instance to be authorized to use the S3 and Rekognition APIs.

* Previously, you gave it full access to Amazon S3.
* Now we need to give it access to Rekognition\!

Give access to Rekognition by editing the IAM role **EC2\_Class\_Role** and giving it access to Rekognition.

1. Log in to your AWS console at [https://signin.aws.amazon.com](https://signin.aws.amazon.com). As a reminder, you probably logged in to the **root account** with an email address as a username.
2. Click on Instances (running): ![][image2]
3. You should still have one running instance\!
   ![][image3]
4. Instead of connecting to the instance, click on its Instance ID, then click on the **Security** tab:
   ![][image4]
5. Click on the **EC2\_Class\_Role**. A new tab will open:
   **![][image5]**
6. Click “**Add Permissions**” and “**Attach Policies**,” search for “**Rek**” and add **AmazonRekognitionReadOnlyAccess**:

   ![][image6]
   Then click “add permissions” to add the permissions to the role:

   ![][image7]

Notice that this change takes place immediately\!

This new permission will be sufficient for you to run the Rekognition celebrity recognizer. If you want to build your own recognition database, you will need to come back here and add additional policies.

# **Create and test another S3 Bucket** {#create-and-test-another-s3-bucket}

Lab 6 requires that you create another S3 Bucket and configure its CORS policy.

Your S3\_BUCKET name for this app is defined in the file `image_controller.py` and is based on your instance’s hostname and the lab number. The CORS policy is specified in the same file; it is quite permissive.

You can do both of these by logging in to your Instance and typing:

`$ cd $HOME/spring26/lab6`
`$ make init-s3`

# **Create an API Key**  {#create-an-api-key}

Use the new-apikey Makefile target to create a lab 6 API key and store it in the answer file:

`$ make new-apikey | grep API | tee $HOME/lab6-answers.yaml`

# **Test your application** {#test-your-application}

Your application should be up and running now.

1. Go to [https://smashedemail-lab6.csci-e-11.org/](https://smashedemail-lab5.csci-e-11.org/) and post a message with an image. If it works, you’ll see who Amazon’s Rekognition thinks you are:

2. Examine the JSON that your application is returning by looking at https://*smashedemail*\-lab6.csci-e-11.org/api/get-images with Chrome and clicking the “PrettyPrint” button
   ![][image8]



# **Debugging** {#debugging}

Is something not working? Start by look over the “Debugging” section of [CSCI E-11 Spring 2025 Lab \#4](https://docs.google.com/document/d/16dELJKbumS27bscnJT3eQbs-q4kAQXPun4l9-U1WDJc/edit?tab=t.0#heading=h.x3ksbgec8yoq)

Here are other things to try:

1. Always start by looking at the log files\!
2. Look at the last 100 lines of your webserver’s with the journalctl command:

   `$ journalctl -r -g lab6 -n 100`

   Remember, you can watch it in real time with:

   `$ journalctl -f -g lab6`

3. Use the `git diff` command to compare what’s different between your version of the git repo and the one on GitHub:

   `$ cd $HOME/spring26/lab6`
   `$ git diff origin`

4. Were the pictures uploaded to S3? Take a look:

   `$ aws s3 ls` — this command should list all of your s3 buckets

   `$ aws s3 ls s3://yourbucket/` — this command should list the contents of yourbucket (which you should change to be your actual bucket name)

5. Post a question in the class forum on Canvas.
6. Ask the TA’s for help\!



# **GET AN A** {#get-an-a}

We’ve been using the [Amazon Rekognition](https://aws.amazon.com/rekognition/) [celebrity recognition](https://docs.aws.amazon.com/rekognition/latest/dg/celebrities.html?pg=ln&sec=ft) API.

Modify your program so that it also passes every image through the [text detection](https://docs.aws.amazon.com/rekognition/latest/dg/text-detection.html?pg=ln&sec=ft) API. Review [Amazon’s documentation of how to access the API in Python](https://docs.aws.amazon.com/rekognition/latest/dg/text-detecting-text-procedure.html). Store the recognized text in the `text` column of the image SQL row.  Everything else should just work.

# **What You Will Be Graded On** {#what-you-will-be-graded-on}

The grader will check the following:

* Is the web server properly configured for Lab6?
* Does the API key work to request signed URLs?
* Can an object be uploaded with the signed URL?
* Are celebrities properly detected?
* Is text properly detected?

# **Going Even Further** {#going-even-further}

Here are some other ideas for extending this lab:

* You can add your own people to the Rekognition dataset. Teach Rekognition about 10 people you know and then try to identify them in photos.
* Draw boxes around detected faces and label them with the names, just like the movies.

Here are some tutorials you may find useful:

* [Amazon Rekognition for Identity Verification \- AWS](https://aws.amazon.com/awstv/watch/39d72e62618/) \- (16 min)
* [Amazon Rekognition for Identity Verification \- AWS](https://aws.amazon.com/th/awstv/watch/39d72e62618/?nc1=f_ls)
* [AWS re:Invent 2022 - AI/ML at Amazon.com (INO104)](https://www.youtube.com/watch?v=qsndwQ9-f2k) \- Amazon’s 2022 overview about AI/ML (58 min)
* [AWS re:Invent 2017: Making IoT Devices Smarter with Amazon Rekognition (MCL306)](https://www.youtube.com/watch?v=Zqk3DzNpd0E) (1 hour)

If you want a deep-dive on S3 and all of the amazing things it can do, you may enjoy this:

* [AWS re:Invent 2024 - What’s new with Amazon S3 (STG212)](https://www.youtube.com/watch?v=pbsIVmWqr2M) (55 min)

And here are some third-party videos

* [Build a Facial Recognition App on AWS from Scratch | Rekognition, Lambda, DynamoDB, API Gateway, S3](https://www.youtube.com/watch?v=FsXyfxLDDIs) (56 min, very comprehensive)
* [Using Amazon Rekognition for Celebrity Face Recognition and Comparison](https://www.youtube.com/watch?v=JLqUclh-QSU) (3 min video)
* [Amazon Rekognition Overview and Demo: Image and Video Analysis with AWS | AWS For Everyone](https://www.youtube.com/watch?v=pttoTUgsqRw) (6 min video)

[image1]: <images/6-logo.png>
[image2]: <images/6-resources.png>
[image3]: <images/6-instances.png>
[image4]: <images/6-security.png>
[image5]: <images/6-role.png>
[image6]: <images/6-rekognition.png>
[image7]: <images/6-success.png>
[image8]: <images/6-json.png>