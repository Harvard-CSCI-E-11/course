# **![][image1]**

# **CSCI E-11: Artificial Intelligence, the Internet-of-Things, and Cybersecurity** **Harvard Extension School** **Spring 2026**

# **Lab \#1 \- Instance – Create an AWS EC2 instance and monitor for attacks**

[Lab 1 Introduction and lab objectives](#lab-1-introduction-and-lab-objectives)

[Getting started — first read the docs\!](#getting-started-—-first-read-the-docs!)

[Accessibility](#accessibility)

[Create Your Account](#create-your-account)

[Set a budget](#set-a-budget)

[Set up Multi-factor](#set-up-multi-factor)

[Create an AWS EC2 Instance running Ubuntu 26.04 LTS](#create-an-aws-ec2-instance-running-ubuntu-26.04-lts)

[Getting to know your instance](#getting-to-know-your-instance)

[ps](#ps)

[lsof](#lsof)

[netstat](#netstat)

[\-h, \--help, and man](#-h,---help,-and-man)

[apt install](#apt-install)

[The sudo command means that the command apt install make is run as the super user.](#the-sudo-command-means-that-the-command-apt-install-make-is-run-as-the-super-user.)

[Install clone the course repo and install the e11 command](#install-clone-the-course-repo-and-install-the-e11-command)

[Run the course installer](#run-the-course-installer)

[Tell us about your AWS instance](#tell-us-about-your-aws-instance)

[Modify your system to retain logs for 6 months](#modify-your-system-to-retain-logs-for-6-months)

[Start Monitoring Your SSH logs](#start-monitoring-your-ssh-logs)

[Get an A: Find our hack](#get-an-a:-find-our-hack)

[Getting Automated Help](#getting-automated-help)

[Getting Graded](#getting-graded)

[Going Further](#going-further)

[Explore the Instance Metadata Service](#explore-the-instance-metadata-service)

[Learn about SSH Access](#learn-about-ssh-access)

[Look behind the curtain](#look-behind-the-curtain)

# **Lab 1 Introduction and lab objectives** {#lab-1-introduction-and-lab-objectives}

Welcome to the first lab\! We will be using Amazon Web Services for our labs.

You can complete all of the labs using a new AWS account and taking advantage of the company’s “free tier.” **Please note that 12-months of free EC2 virtual machine are only available to new accounts, so you must create a new AWS account for this course\!**   Also, you will need to register with a credit card, because AWS does have services that cost money, and there are no guardrails to prevent you from using them\! So be careful\!

This brings us to the objectives for this lab:

* Understand the account structure of AWS.
* Create your AWS account.
* Set up budgets for AWS account, so that you will be alerted if your spending goes too high.
* Create a virtual machine with a “ssh” server running to allow remote login.
* Log into the course dashboard and obtain a **course key**.
* Download and install the `e11` tools.
* Register your virtual machine using the e11 tool.
* Obtain your own DNS name that you will use for upcoming labs.
* Modify your virtual machine to retain its logs indefinitely.
* Wait to see who or what attacks your machine.

How you will be graded:

* **Canvas lab1 assignment:** When you are ready, use the `grade` command to request that your virtual machine be graded. When you do this, our dashboard will log into your virtual machine, run some tests, and report to you which of the tests you have passed. To get an A on the lab assignment in Canvas, your VM needs to pass all of the tests. If you don’t pass them the first time, don’t worry — you can ask it to be regarded as many times as necessary. The highest grade is the one that is transferred from the AWS to Canvas.
* **Canvas lab1 discussion:** You are invited to optionally post some of the attacks that your virtual machine receives to the Ed discussion board for **Lab1**. The Canvas discussion is optional and will not be graded.

# **Getting started — first read the docs\!** {#getting-started-—-first-read-the-docs!}

If you have never used AWS before, expect to feel a little overwhelmed. Amazon is the world’s largest cloud infrastructure provider, and AWS has hundreds of different offerings. Fortunately, you only need to use a small number of them to be successful in this lab and in the course.

We recommend looking at these pages:

* [An Introduction to AWS](https://www.youtube.com/watch?v=gv4m1fjuthU) — Amazon’s intro video
* [https://aws.amazon.com/about-aws/](https://aws.amazon.com/about-aws/) \-
* [https://aws.amazon.com/what-is-aws/](https://aws.amazon.com/what-is-aws/)
* [https://aws.amazon.com/what-is-cloud-computing/](https://aws.amazon.com/what-is-cloud-computing/)
* [https://aws.amazon.com/about-aws/global-infrastructure/regions\_az/](https://aws.amazon.com/about-aws/global-infrastructure/regions_az/)

For our first lab, we will only be using the following AWS offerings:

* Amazon’s Billing and Account Management system.
* AWS Elastic Compute Cloud (EC2), to create a virtual machine
* Simple Storage Service (S3) to submit information from your EC2 virtual machine, called an instance, to us.

AWS services are located in [AWS regions](https://aws.amazon.com/about-aws/global-infrastructure/regions_az/) throughout the world. You can use whichever region you wish.

If you live near the East Coast of the US, you will likely want to use **us-east-1** or **us-east-2**. Although **us-east-1** is the more popular, you should check out **us-east-2** because it frequently has lower prices and is sometimes more reliable than **us-east-1**, which was the first AWS region and is still one of the most heavily used.

If you have questions about AWS, we strongly recommend consulting the AWS documentation before searching Google. The AWS documentation is well written and frequently goes into greater detail than the answers you will find on Medium or Stack Overflow or from ChatGPT. Although these services all have their place, we have literally wasted hours trying to get working code, only to find what we needed in the documentation with just a few minutes of searching.

You can find the AWS documentation here:

* [https://docs.aws.amazon.com/](https://docs.aws.amazon.com/)

Of course, there’s nothing wrong with typing your question into Google, ChatGPT, or Gemini and trying the answer you get\! We encourage you to do that.

## **Accessibility** {#accessibility}

Accessibility is an important part of modern computing. “Accessibility” broadly means making sure that computing systems can be used by people who may have issues perceiving information on a computer’s display (such as people who are color blind) or operating a computer through the traditional keyboard and mouse interface (such as people with limited dexterity). If you are interested in accessibility issues, you can learn more about how AWS addresses these issues here:

* [https://aws.amazon.com/accessibility/](https://aws.amazon.com/accessibility/)
* [https://cloudscape.design/foundation/core-principles/accessibility/Building-accessible-experiences/](https://cloudscape.design/foundation/core-principles/accessibility/Building-accessible-experiences/)

# **Create Your Account** {#create-your-account}

We are requesting that you create a new AWS account for this course. **Please do this even if you have used AWS before—it is the only way that you can leave your virtual machine running for the course without being charged for it.** This is because new AWS accounts qualify for “free tier” for certain services for 12 months, but not afterwards.

Note: If you previously have an AWS account, you must create your new account with a different email address.

1. Go to [https://aws.amazon.com/](https://aws.amazon.com/) and click “Create account.”  (Note: Amazon changes their buttons and text from time-to-time, so these screenshots may be out of date by the time you see them.)
   ![][image2]
2. You can use any email address you want.
3. Amazon will send you a code. Type this code into the account box. This is a form of authentication called “email-based identification and authentication.”
4. You will now need to create a “root user password.” Make it good and **save it in your password manager.** (Later, we will show you how to make a passkey, which allows you to log into your AWS account without using a password.) If you are not using a password manager, now is a good time to start.
5. Choose “Free (6 months)” (the plan on the left)

   ![][image3]

6. Fill out the information with your real name.
   1. Specify “personal” as your account type, because your account is for your personal use—you are not an employee of Harvard and using this in your official Harvard capacity.
7. Provide billing information. Sadly, you need to use a real credit card. But don’t worry\! We will set up a billing alert and you should be able to qualify for free credits. If you follow the directions in these labs correctly, you shouldn’t receive any charges.
8. Confirm your identity with a text message.
9. Be sure to sign up for **Basic Support \- Free**:
   ![][image4]
10. Wait to receive an email from Amazon that your account has been created (you may have to click on a link to validate your email address), and then go to the AWS management console by clicking:
    ![][image5]

Congratulations\! You have created your AWS account.

Now there are two things that you must do immediately:

1. Set up a budget to protect your credit card.
2. Set up multi factor to protect your account.

# **Set a budget** {#set-a-budget}

The very first thing we want you to do is to set a billing alarm so you will be told if you are spending money on that credit card you provided to Amazon.

On the AWS console, click on your account name in the upper right hand corner, then select “Billing and Cost Management:”

![][image6]

1. Under “Cost monitor”, under “Budgets status,” click “Setup Required.”
2. Select **Use a template (simplified)** and **zero spend budget.**
3. Give the budget a name and set up email addresses to email when your spending goes over $0.01. We recommend that you provide at least two email addresses, such as a personal email and a work email.
4. Click “Create Budget”

When you are done, you should see a budget in the budget list:

![][image7]

You may wish to create additional budgets.

**NOTE: You will be notified when you exceed your budget, but the billing will not stop\! You can configure an AWS policy that will shut down your resources the moment that a budget is exceeded, but we will not be doing that in this course. *It is your responsibility to monitor your AWS usage and keep it within your budget.***

Learn more about AWS budgets here:

* https://aws.amazon.com/aws-cost-management/aws-budgets/faqs/

# **Set up Multi-factor** {#set-up-multi-factor}

AWS offers many options for identity and access management (IAM) of its accounts. We recommend that you assign at least two MFA approaches to your account.

On the AWS console, click on your account name in the upper right hand corner, then select “Security credentials:”

![][image8]

1. Verify that your Account name and Email address are correct.
2. Copy down your AWS account ID
3. Also copy your “Canonical user ID”
4. Click “Assign MFA device” and add one or more MFA devices.

***Confused about Multi-factor? Ask your questions on [the Ed Discussion board](https://edstem.org/us/courses/89671/discussion).***

# **Create an AWS EC2 Instance running Ubuntu 26.04 LTS** {#create-an-aws-ec2-instance-running-ubuntu-26.04-lts}

Now we are going to create a micro virtual machine running Ubuntu 26.04 LTS Linux.

**NOTE:** AWS offers many Linux versions to choose from. In this course, we will be using Ubuntu 26.04 LTS exclusively because of its excellent support and the wide number of tutorials available for it.

If you are new to AWS EC2, we recommend you read these pages—but don’t type any commands yet\!

* [https://aws.amazon.com/pm/ec2/](https://aws.amazon.com/pm/ec2/)
* [What is Amazon EC2? \- Amazon Elastic Compute Cloud](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/concepts.html)
* [AWS Nitro System \- Lightweight Hypervisor](https://aws.amazon.com/ec2/nitro/)
* [Manage detailed monitoring for your EC2 instances \- Amazon Elastic Compute Cloud](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/manage-detailed-monitoring.html)


1. Type “ec2” into the search box at the top of the AWS console. Select the ★ so that the EC2 button will be added to your dashboard. Then click on the EC2 letters to enter the EC2 console.
   ![][image9]
2. Scroll down to “Launch a virtual server” and click Launch Instance.
   1. Give your instance a name
   2. Select “Ubuntu Server 26.04 LTS (HVM), SSD Volume Type” as the Application and OS.
   3. Select the 64-bit (x86) AMD64 architecture.
   4. In “Instance type,” select an AMD64-v3-compatible instance type that is “free tier eligible.” We recommend **t3.micro** or a newer generation; do not use older instance types that lack AMD64-v3 support.

The current Canonical Ubuntu 26.04 LTS AMD64 image identifiers are:

| Region | AMI ID | EC2 image ARN |
|---|---|---|
| `us-east-1` | `ami-03ceeebf93c41fdae` | `arn:aws:ec2:us-east-1::image/ami-03ceeebf93c41fdae` |
| `us-east-2` | `ami-066bae1901917f0ae` | `arn:aws:ec2:us-east-2::image/ami-066bae1901917f0ae` |

These images were published by Canonical on August 19, 2026. Verify that the
selected image is owned by Canonical (`099720109477`) before launching it.
3. Under “Key pair (login)”, click “Create a new keypair.”  This creates an SSH keypair that you will use to log into the server.
   1. Give the keypair a memorable name.
   2. Select ED25519 (\*)
   3. Select .pem as the Private key file format.
   4. Click the orange “Create Keypair” button.
4. **NOTE:** In our example below, you will be logging in using the web-based UI. However, you can also download the SSH keypair file and use it to log in from your personal computer using the `ssh` command line program available in macOS, Linux, [Windows git environment](https://git-scm.com/downloads), or the Windows Subsystem for Linux. We will not be discussing how to use SSH from the command line in this course, but there are many tutorials available online. If you wish to use your own `ssh`, download the “.pem” file. ***Do not lose this file\!***
5. Select “Create security group” with these options:
   1. “Allow SSH traffic from Anywhere,”
   2. “Allow HTTPS traffic from the Internet,” and
   3. “Allow HTTP traffic from the Internet.”

*\*ED25519 refers to a public key encryption algorithm based on elliptic curves and a specific curve known as ED25519. This key is secure against all known cryptographic attacks today, although it is not secure against an attack using a cryptographically relevant quantum computer (CRQC). We will be discussing such computers at the end of this course.*

Your AWS console should look something like this:

![][image10]

Note: The pale yellow box recommends "setting security group rules to allow access from known IP addresses only." We are ignoring this advice; otherwise, you won’t get anyattacks logged. The attacker should not be able to log into your computer because they don’t have your private key\!

6. Click ![][image11]

If your instance launches successfully, you will see something like this:

![][image12]

You can click on that identifier (i-005131764b1b87207 above) to go to the control panel for your instance:

![][image13]

Note that the above example uses the US-EAST-2B “availability zone.” This means that I need to access this page using the US-EAST-2 console URL:

* [https://us-east-2.console.aws.amazon.com/ec2/home](https://us-east-2.console.aws.amazon.com/ec2/home)

**Please observe that this URL is specific to the AWS us-east-2 region; if you are using a different region, that region will appear in the first part of the URL.** It doesn’t matter which region you use. Here we use us-east-2 because it tends to be a little cheaper than us-east-1.

You can also return to this page by pressing the EC2 button in the command bar and click on the Instances Running button:

 ![][image14]  \-\>  ![][image15]

7. Click on the instance ID to bring up the detailed control panel for the instance. Wow\! Look at all that stuff.
8. We want to log into the server. Click the “Connect” button:
   ![][image16]
9. Be sure that the **EC2 Instance Connect** tab is selected:

![][image17]

10. Click ![][image18]

    (Note: if you know how to use SSH, you can click on the “SSH client” tab to get information on how to access your instance from your computer using ssh. More information is available at [Connect to your Linux instance using an SSH client \- Amazon Elastic Compute Cloud](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/connect-linux-inst-ssh.html). You will need the SSH key that you previously downloaded.

11. You are now logged in to your VM and at the bash shell prompt. Here’s what we got when we did this in July 2025:

![][image19]

(We actually logged in from a Mac using **ssh**, rather than the Amazon console.)

Notice that the instance thinks that its IP address is 172.31.10.16. That’s the *internal AWS IP address* for this instance. We used a different IP address to log in (in our case, 3.144.237.235). The user is **ubuntu**, which is the default user on Ubuntu 26.04 installations.

Once you log in, be sure that your instance is up-to-date by typing this command:

`$ sudo apt update`

Note that you do not type the `$` is the example above, but you do type the text that is in the **`bold green fixed-width`** `font`. The `$` is the bash prompt. (In our screen shot above, the prompt is actually `ubuntu@ip-172-31-10-16:~$`.)

The `$` is a generic prompt. It tells you that Linux’s bash shell is ready to accept your next command.

# **Getting to know your instance** {#getting-to-know-your-instance}

Welcome to the Linux command line\! You will be spending a lot of time here for the labs. We would like you to learn about some basic commands.

## **ps** {#ps}

You are logged into your instance as the `ubuntu` user. You can list all of the processes that your user is currently running with this command:

`$ ps ux`

**T**he `u` option means generate a user-oriented output, and the `x` option means list all running processes belonging to the current user, even those that were not started by an interactive prompt.

If you add an `a` option you will list all of the processes currently running. Give it a try:

`$ ps aux`

## **lsof** {#lsof}

The lsof command lists every open file in use by every program. Give it a try:

`$ lsof`

## **netstat** {#netstat}

The `netstat` command shows all of the open network connections. However, to run it, you will first need to install it. Before you do that, you need to update the apt database:

`$ sudo apt update`

`$ sudo apt install net-tools`

`$ netstat -t`

## **\-h, \--help, and man** {#-h,---help,-and-man}

Many commands will display help if you run them with a single argument of `-h` or `--h`.

The `man` command prints the manual pages for nearly all commands:

`$ man ps`

`$ man lsof`

`$ man netstat`

`$ man man`

## **apt install** {#apt-install}

As you saw above, you can use the `apt install` to install additional software.

For many of the labs in this course, you will need to edit text files on the remote Linux instance. The easiest way to do this is by running a character-based `editor` on the server such as `emacs`, `vim`, or `nano`. When you edit these files you will typically need to edit them as the Linux superuser.

**NOTE:** Several programs that you can run on a Windows or Macintosh desktop will allow you to contact directly to your instance without going through the AWS console. For example, you can use the `ssh` program to log into your instance, and programs like `scp` or `WinSCP` to copy files.

**NOTE:** If you are using Microsoft’s Visual Studio Code editor, you can configure it to let you use it to log in to the remote instance and edit files there (see [Remote Development using SSH](https://code.visualstudio.com/docs/remote/ssh)). We recommend against using VSCode or another editor in this manner, as it is important to learn how to edit files directly on your instance. It is also complciated to use these programs to edit files that must be edited as superuser.

The editors `vim` and `nano` are pre-installed in Ubuntu 26.04, and our installer script (below) will install `emacs` on your instance.

`emacs` is a powerful programmer’s editor developed at MIT in the 1970s. The name “emacs” originally stood for “Editing Macros” but today it stands for “Emacs Makes All Computing Simple.” If you want to learn emacs, you can type `emacs` at the command line and then type control-h followed by the letter `t`. This will start the emacs tutorial. Simson recommends learning `emacs`.

`vi` is the visual editor that was developed at Berkeley in the 1970s. It is not as powerful as emacs, but people who learn `vi` first generally do not want to learn emacs. `vim` stands for Vi IMproved; this program was created in 1991\. Nobody uses `vi` anymore, but many people call `vim` by the name `vi`. You can run it with either command. We do not recommend learning `vi`, but you will probably stick with it if you already know it. Geoff still uses `vi`.

`nano` is an editor that is easier for beginners to use than either `vi` or `emacs` because it displays a menu along the bottom of the screen explaining what each control character does. If you absolutely need to edit a file and you don’t wish to learn `emacs` or `vi`, you can get by using `nano`. However this editor is highly limiting, so you are advised to learn a more sophisticated editor. Both Simson and Geoff recommend avoiding `nano`.

System software typically needs to be installed by the system administrator account, called the “superuser” in Linux. We use the `sudo` command to accomplish this. The `sudo` command causes the command that follows on the command line to be run using the superuser account.

We will eventually want to use the tool `make`, which lets us build programs automatically. We won’t use it in this lab but will want it later, so let’s install that too:

`$ sudo apt install make`

# The `sudo` command means that the command `apt install make` is run as the super user. {#the-sudo-command-means-that-the-command-apt-install-make-is-run-as-the-super-user.}

# **Install clone the course repo and install the e11 command** {#install-clone-the-course-repo-and-install-the-e11-command}

We have created a collection of programs, configuration files, and documentation for this course. All of these are stored on GitHub in the CSCI E-11 Course Repo (repository). You can find it here:

[https://github.com/Harvard-CSCI-E-11/spring26](https://github.com/Harvard-CSCI-E-11/spring26)

In order to complete the labs, you will need to “clone” this repo into the home directory of the **ubuntu** user on your instance.

Ubuntu 26.04 comes with the git client pre-installed, so the only thing you need to do is to type this command:

`$` **`git clone https://github.com/Harvard-CSCI-E-11/spring26.git`**

(Note: the above goes all on a single line, and the “.git” at the end of the clone command is optional.)

Here’s what happened when we typed the `clone` command; you will likely see something slightly different:

![][image20]

This message is telling you that there are 1322 “objects” in the git repo at GitHub. (There will be more when you clone the repo.) Git works by giving the client a list of all these objects. Your client then downloads the objects that it doesn’t have. In this way, git can quickly download updates during the course if we make changes to the repo.

# **Run the course installer** {#run-the-course-installer}

There’s a lot of other software that needs to be installed for CSCI E-11. Rather than making you install it all, we’ve created our own installer program. You can run it with a single command:

`$ spring26/etc/install-e11`

Once the installer finishes, run the following command:

`$ source $HOME/.bashrc`

**NOTE: This may take 5-10 minutes to complete\!**

This installer will:

* Apply all necessary updates to your Ubuntu 26.04 operating system. (This is what takes the longest time\!)
* Install the `aws` command (provided by Amazon Web Services)
* Install the python `poetry` package manager
* Install the `e11` command (which  we wrote specifically for this course) into the directory `$HOME/.local/bin`.
* Install sample code for each of the labs, which you will find in the directories `spring26/lab1` through `spring26/lab8*`.

The second command above (the `source` command) updates your `PATH` environment variable to add `$HOME/.local/bin` to your path, so that you can run the `e11` command. (Logging out and logging back in would have the same effect.)

The next time you log in after you run the installer, you will see something that looks like this:

`*** System restart required ***`
`E11 local version: 0.2.2`
`E11 server version: 0.2.2 (deployed 2025-12-03T17:51:27-0500)`
`CSCI E-11 Course admin and grader DO NOT HAVE ACCESS to this instance.`
               `total        used        free      shared  buff/cache   available`
`Mem:           909Mi       286Mi        76Mi       1.0Mi       642Mi       622Mi`
`Swap:             0B          0B          0B`

The “System restart required” indicates that some of the installed software requires that you reboot your instance. You can do this by typing:

`$ sudo shutdown -r now`

Don’t do this now\! But you want to do it at some point.

The next two lines indicate the version of the `e11` command running on your instance and the matching version running on [`csci-e-11.org`](http://csci-e-11.org). If these two numbers do not match, you can use the e11 update command to update your version:

`$ e11 update`

The next line indicates that the grader software cannot log into your instance to grade it. You need to give access, which you do with this command:

`$ e11 access on`

The final lines indicate that there is 76 MiB of free memory on this instance, but 622 MiB of available memory. This is possible because 642MiB of the 909MiB available to the operating system is being used by purgable buffers. Labs 3, 4, 5, 6 and 7 all consume memory if you leave their servers running, and in some cases, this will cause problems. You can avoid these problems by shutting down each lab service after you have received a grade. We will give you instructions on how to do this.

The line with “Swap” indicates how much virtual memory is available. By default AWS EC2 instances do not swap, although you can enable it if you wish.

Finally, you can get more information about the `e11` command by typing:

`$ man e11`

# **Tell us about your AWS instance** {#tell-us-about-your-aws-instance}

Next, we want you to tell us about your AWS account. We are going to do this by having you:

1. Get your public IP address
2. Get your instance ID
3. Enter this information into the `e11` command by using the command **`e11 config`**.
4. Send this information to our AWS S3 bucket by using the command **`e11 register`**.

You can get the public IP address and your InstanceID from the account console. However, we’re going to get them from within the instance.

You can get your IP address with the command:

 `$ curl -s https://checkip.amazonaws.com`

Here is an example:

`![][image21]`

You can get your AWS Instance ID using this command:

`$ aws sts get-caller-identity`

If you run this command now, you will see an error message like this:

![][image22]

This error message is misleading\! It correctly states that the `aws` command has not been configured with your account credentials. But don’t follow its recommendation\!

Although you *could* get account credentials from the AWS console and program them into the AWS instance, *doing so would not be secure*, because anyone who gained access to your instance (perhaps by hacking their way into it) would be able to take over your AWS account.

Instead, you will configure that AWS infrastructure so that specific commands executed on your instance are automatically authorized. You will do this by creating an AWS “Role” that has the authorization to execute these commands and then assigning that Role to your instance. (This is called role-based access control, or RBAC.)

To get your Account ID, the instance needs to be assigned an IAM Role that has access to your account information.

1. In the **instance summary page on the AWS console**, select **Modify IAM Role** from the Security menu under Actions. (Look carefully at the screenshot, because there are other “Security” settings on the page which are not relevant here.)

   ![][image23]

2. Select “Create new IAM role” (on the right-hand side)
   ![][image24]

We will need to create a new IAM Role and give it permission to execute the **sts:GetCallerIdentity** and **ec2:DescribeInstances** functions.

3. Click the orange “Create Role” button:
   ![][image25]
4. Select **AWS Service** as the Trusted Entity type and EC2 as the Use Case and click “Next”:

   ![][image26]

5. Type “accountmanage” in the search box to find **AWSAccountManagementReadOnlyAccess**, then check the box. Then search “ec2read” to find **AmazonEc2ReadOnlyAccess**, and check the box.

   **![][image27]**

   **![][image28]**

6. Click the orange “Next” button
7. Give your role the name **EC2\_Class\_Role**. Notice the JSON Trust Policy that AWS has created for you:
   ![][image29]
8. Click “Create Role” at the bottom:
   ![][image30]
   You now have a role:
   ![][image31]
9. Go back to the other tab “Modify IAM role | EC2”:
   ![][image32]
10. Click the button with the arrow in the circle in it to refresh your list of roles:
    ![][image33]
11. Select your role from the pull-down menu:
    ![][image34]
12. Click “Update IAM role” and your role will be added to the running virtual machine\!
13. Verify that the role is now there by clicking on the “Security” tab:
    ![][image35]

14. Verify that your instance can now run that command:

    `$ aws sts get-caller-identity`

    ![][image36]

    This is a JSON object:

* UserID — This is the “UserId” of the instance. The second part is the instance identifier.
* Account — This is Simson’s Amazon account. (Well, not really.)
* Arn — This is the Amazon Resource Name (Arn) for the caller identity. Notice that it includes the words “assumed-role” and “EC2\_Class\_Role”. This means that the “caller” of the `aws sts get-caller-identity` is the instance running in the role that we created.

15. Log in to [https://csci-e-11.org/](https://csci-e-11.org/) with your Harvard Key and get your `course_key`. When Simson logged in, he saw this:

    ![][image37]

Of course, the details of what you see will be different..

Now you can enter this information into the `e11` command:

16. Run the `e11 config` command from your instance. Below, we run it for Simson. (You can get your instance’s id, and your instance’s public IP address, from the AWS dashboard. *Don’t use the “Web browser IP address seen in the “HARVARD CSCI E-11 Dashboard” as seen in the screenshot here above\!)*
    `ubuntu@sgarfinkelfas:~$ e11 config`
    `preferred_name: [] Simson Garfinkel`
    `email: [] sgarfinkel@fas.harvard.edu`
    `course_key: [] d11f49`
    `public_ip: [] 3.133.144.134`
    `instanceId: [] i-051217472c438d44b`
    `Writing configuration to /home/ubuntu/e11-config.ini:`
    `[student]`
    `preferred_name = Simson Garfinkel`
    `email = sgarfinkel@fas.harvard.edu`
    `course_key = d11f49`
    `public_ip = 3.133.144.134`
    `instanceid = i-051217472c438d44b`


    `Done!`
    `ubuntu@sgarfinkelfas:~$`



17. Run the `e11 register` command. Below we run it:
    `ubuntu@sgarfinkelfas:~$ e11 register`
    `Attempting to register...`
    `Registered!`
    `If you do not receive a message in 60 seconds, check your email address and try again.`
    `ubuntu@sgarfinkelfas:~$`

    Note: If you made an error when you ran `e11 config`, you will need to run it again\!

18. Click **(reload)** on the web page or reload the web page by clicking shift\-![][image38]

![][image39]

19. Now, click **check** to see if the dashboard can access your instance. If everything works, you should see it change to:

    ![][image40]

“Access On” means that the dashboard can log into your AWS instance using the `ssh` command. **This access is required to grade your instance.** The course staff can also log into your instance and look around in exceptional cases if you need help.

Some students don’t like the course staff's ability to log into their VMs. If you feel that you don’t want anybody to be able to log in other than you, you can turn off access with the `e11 access` command:

`ubuntu@sgarfinkelfas:~$ e11 access off`
`2025-09-13 08:21:23,335 INFO [e11 __main__.py:70 do_access_off] Revoking access from course admins...`
`ubuntu@sgarfinkelfas:~$`

Now if you reload the dashboard and click **check**, you should see:

![][image41]

Be sure to turn access back on before the lab is due, or we will not be able to grade your lab, and you will receive no credit for the assignment.

20. Check your email. You should see something like this:

![][image42]

# **Modify your system to retain logs for 6 months** {#modify-your-system-to-retain-logs-for-6-months}

You will now modify the journal retention time of your instance to be 6 months.

Traditionally Linux systems stored logs in text files in the `/var/log` directory. A program called `syslog` received messages from programs and wrote them to log files according to rules specified in the file `/etc/syslog.conf`. A program called `newsyslog` rotated the log files, compressing or deleting them as necessary. If you search online, you are likely to find many references to this style of logging, and some programs (such as the Apache web server) manually write log files to the `/var/log` directory.

Modern Linux systems use a new logging system called `systemd` and a logging program called `journald`:

* [Wikipedia has a good explanation of what’s going on](https://en.wikipedia.org/wiki/Systemd), and we defer to it.
* We also refer you to this [online tutorial](https://sematext.com/blog/journald-logging-tutorial/).
* And [here is the original blog post](https://docs.google.com/document/u/0/d/1IC9yOXj7j6cdLLxWEBAGRL6wl97tFxgjLUEHIX3MSTs/pub) (updated) explaining the motivation.

The configuration files for systemd are kept in the directory `/etc/systemd`:

`[ec2-user@ip-172-31-17-177 ~]$ ls -l  /etc/systemd/`
`total 64`
`-rw-r--r--.  1 root root   845 Feb 28  2024 coredump.conf`
`-rw-r--r--.  1 root root   766 Feb 28  2024 homed.conf`
`-rw-r--r--.  1 root root  1282 Feb 28  2024 journald.conf`
`-rw-r--r--.  1 root root  1539 Jun 17 21:20 logind.conf`
`drwxr-xr-x.  2 root root     6 Jun 17 21:21 network`
`-rw-r--r--.  1 root root   846 Feb 28  2024 networkd.conf`
`-rw-r--r--.  1 root root   804 Feb 28  2024 oomd.conf`
`-rw-r--r--.  1 root root   670 Feb 28  2024 pstore.conf`
`-rw-r--r--.  1 root root  1398 Jun 17 21:20 resolved.conf`
`-rw-r--r--.  1 root root   953 Feb 28  2024 sleep.conf`
`drwxr-xr-x. 21 root root 16384 Nov 22 05:04 system`
`-rw-r--r--.  1 root root  2080 Jun 17 21:20 system.conf`
`drwxr-xr-x.  2 root root    28 Nov 22 05:04 system.conf.d`
`-rw-r--r--.  1 root root   856 Jun 17 21:20 timesyncd.conf`
`drwxr-xr-x.  5 root root   107 Nov 22 05:02 user`
`-rw-r--r--.  1 root root  1415 Jun 17 21:20 user.conf`
`[ec2-user@ip-172-31-17-177 ~]$`

The configuration file we care about is `/etc/systemd/journald.conf`:

`[ec2-user@ip-172-31-17-177 ~]$ cat /etc/systemd/journald.conf`
`#  This file is part of systemd.`
`#`
`#  systemd is free software; you can redistribute it and/or modify it under the`
`#  terms of the GNU Lesser General Public License as published by the Free`
`#  Software Foundation; either version 2.1 of the License, or (at your option)`
`#  any later version.`
`#`
`# Entries in this file show the compile time defaults. Local configuration`
`# should be created by either modifying this file, or by creating "drop-ins" in`
`# the journald.conf.d/ subdirectory. The latter is generally recommended.`
`# Defaults can be restored by simply deleting this file and all drop-ins.`
`#`
`# Use 'systemd-analyze cat-config systemd/journald.conf' to display the full config.`
`#`
`# See journald.conf(5) for details.`

`[Journal]`
`#Storage=auto`
`#Compress=yes`
`#Seal=yes`
`#SplitMode=uid`
`#SyncIntervalSec=5m`
`#RateLimitIntervalSec=30s`
`#RateLimitBurst=10000`
`#SystemMaxUse=`
`#SystemKeepFree=`
`#SystemMaxFileSize=`
`#SystemMaxFiles=100`
`#RuntimeMaxUse=`
`#RuntimeKeepFree=`
`#RuntimeMaxFileSize=`
`#RuntimeMaxFiles=100`
`#MaxRetentionSec=`
`#MaxFileSec=1month`
`#ForwardToSyslog=no`
`#ForwardToKMsg=no`
`#ForwardToConsole=no`
`#ForwardToWall=yes`
`#TTYPath=/dev/console`
`#MaxLevelStore=debug`
`#MaxLevelSyslog=debug`
`#MaxLevelKMsg=notice`
`#MaxLevelConsole=info`
`#MaxLevelWall=emerg`
`#LineMax=48K`
`#ReadKMsg=yes`
`#Audit=yes`

As you can see, there are a lot of configuration options\!

1. Using the editor of your choice, edit the file `/etc/systemd/journald.conf`. Change the line that reads:

   `#MaxRetentionSec=`

	To read:

`MaxRetentionSec=6month`



**NOTE 1 — Be sure to remove the "\#" at the beginning of the line\! That's the comment character. If you don't remove it, the line is ignored.**

**NOTE 2 — Remember, this file must be edited as the superuser, so you will probably use one of the following commands to edit the file:**

`$ sudo nano /etc/systemd/journald.conf`

`$ sudo vim /etc/systemd/journald.conf`

`$ sudo emacs /etc/systemd/journald.conf`

2. Restart the journal daemon:

   `$ sudo systemctl restart systemd-journald`

Your instance will now retain logs for 6 months.

# **Start Monitoring Your SSH logs** {#start-monitoring-your-ssh-logs}

Your instance is equipped with a server with the Secure Shell program. When you connect to the server in the web console, the AWS console actually uses the SSH program to connect to your server.

The Linux command `last` will show every time you log into your server:

`$ last`

However, the `last` command does not show login *attempts*. To see those, look at the SSH logs. You do that with the `journalctl` command, with an argument  **`-g`** that indicates a string to search the journal entries:

`$ journalctl -g sshd`

If you want to see the invalid user attempts, you can use this command:

`$ journalctl -g 'Invalid user'`

After your computer has been running for a while, you will notice that a lot of people have tried to break into it. But if you don’t see anything at first, that just means you haven’t waited long enough…

The times are in UTC; you can change them to local time by changing the TZ variable. For example:

`$ export TZ="America/New_York"`

![][image43]

For security reasons, `sshd` logs the username but not the attempted password. This is to avoid accidentally logging typos.

Want to learn everything that `journalctl` can do? Type **`man journalctl`**.

This command writes all of the attacks in the last two weeks to a file:

`$ journalctl  --since "14 days ago" -g 'Invalid user'`

Note the single quotes versus double quotes. They are different, but in this example, you can use either, as long as you use them in matching pairs\! Most important, they must be **straight quotes** (like this: "14 days ago" and 'Invalid user'), not angle quotes or curly quotes (not like this:  “14 days ago” or '`Invalid user`' or \``Invalid user`\`).

Also, notice that **`--since`** has two hyphens in a row, while **`-g`** has a single hyphen.

(Of course, you’ll get no results if you don't have any attacks.)

Want to learn about systemd time? Type:

`$ man systemd.time`

This command writes the attacks to a file called `attacks.log` (enter it all on one line):

`$ journalctl  --since "14 days ago" -g 'Invalid user' > attacks.log`

Let’s look at how big the file is:

`$ ls -l attacks.log`

`$ wc -l attacks.log`

Let’s look at the first 5 lines:

`$ head -5 attacks.log`

`Jan 25 12:00:03 simsong.csci-e-11.org sshd[620240]: Invalid user csci-e-11-veritas-E11-3.14.68.84 from 137.83.22.241 port 51916`
`Jan 25 12:35:11 simsong.csci-e-11.org sshd[622193]: Invalid user sammy from 177.11.184.55 port 29669`
`Jan 25 12:36:32 simsong.csci-e-11.org sshd[622262]: Invalid user steam from 186.13.143.106 port 58872`
`Jan 25 12:38:54 simsong.csci-e-11.org sshd[622388]: Invalid user ubuntu from 186.13.143.106 port 59646`
`Jan 25 12:40:48 simsong.csci-e-11.org sshd[622516]: Invalid user deploy from 186.13.143.106 port 35960`

Let’s look at the last 5 lines:

`$ tail -5 attacks.log`

`Feb 08 08:38:53 simsong.csci-e-11.org sshd[1724137]: Invalid user ubuntu from 121.188.189.5 port 33524`
`Feb 08 08:38:55 simsong.csci-e-11.org sshd[1724139]: Invalid user pi from 121.188.189.5 port 33675`
`Feb 08 08:38:57 simsong.csci-e-11.org sshd[1724141]: Invalid user baikal from 121.188.189.5 port 33905`
`Feb 08 08:42:41 simsong.csci-e-11.org sshd[1724337]: Invalid user user1 from 121.224.115.232 port 32934`
`Feb 08 11:21:10 simsong.csci-e-11.org sudo[1733127]: ec2-user : TTY=pts/9 ; PWD=/home/ec2-user ; USER=root ; COMMAND=/usr/bin/journalctl -g 'Invalid user'`

Notice that the last line is not an attack, but rather my `su` command – which is also written to the log, and contains the text `Invalid user`\! To fix that, we can tell journalctl to only give us the logs from the `ssh` by adding the `-u ssh` option.

Also, we can make the dates easier to read by adding by the `--output=short-full` option.

So now our command looks like this:

`$ journalctl -u ssh --output=short-full --since "14 days ago" –g 'Invalid user' > attacks2.log`

`$ head attacks2.log`

`Sat 2025-01-25 12:00:03 UTC simsong.csci-e-11.org sshd[620240]: Invalid user csci-e-11-veritas-E11-3.14.68.84 from 137.83.22.241 port 51916`
`Sat 2025-01-25 12:35:11 UTC simsong.csci-e-11.org sshd[622193]: Invalid user sammy from 177.11.184.55 port 29669`
`Sat 2025-01-25 12:36:32 UTC simsong.csci-e-11.org sshd[622262]: Invalid user steam from 186.13.143.106 port 58872`
`Sat 2025-01-25 12:38:54 UTC simsong.csci-e-11.org sshd[622388]: Invalid user ubuntu from 186.13.143.106 port 59646`
`Sat 2025-01-25 12:40:48 UTC simsong.csci-e-11.org sshd[622516]: Invalid user deploy from 186.13.143.106 port 35960`

That’s much better\!

(Once again, if your server hasn’t been attacked yet, you won’t see any log entries.)

# **Get an A: Find our hack** {#get-an-a:-find-our-hack}

We hacked your server when you ran the CSCI E-11 installer: we created a new user and made it trust our SSH key.

To get an A, you will need to find the user and remove it with the **`deluser`** command.

# **Getting Automated Help** {#getting-automated-help}

The `e11` command can find basic problems with this lab with this command:

`$ e11 check lab1`

If the command doesn’t work, you can also try:

`$ e11 doctor`

# **Getting Graded** {#getting-graded}

You can use the e11 command to check your system:

`$ e11 check lab1`
`=== lab1 Results ===`
`Score: 5.0 / 5.0`

`-- PASSES --`
  `✔ test_autograder_key_present`
  `✔ test_hacker_user_deleted`
  ~~`✔ test_no_ssh_on_port_80`~~
  ~~`✔ test_ssh80_service_inactive_and_disabled`~~
`$`

You may see more tests\!

If you have not enabled access for the grader, you will see something like this:

`$ e11 check lab1`
`=== lab1 Results ===`
`Score: 3.75 / 5.0`

`-- PASSES --`
  `✔ test_hacker_user_deleted`
  ~~`✔ test_no_ssh_on_port_80`~~
  ~~`✔ test_ssh80_service_inactive_and_disabled`~~

`-- FAILURES --`

`✘ test_autograder_key_present: Expected pattern not found: ssh\-ed25519\ AAAAC3NzaC1lZDI1NTE5AAAAIEK/6zvwwWOO\+ui4zbUYN558g\+LKh5N8f3KpoyKKrmoR\ auto\-grader\-do\-not\-delete`
`----- context -----`
    `1  ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFf8CTMuTHq2ak59hMseTqten9v9QI30DUgH+C6Z0Xv4 Seasons`
`$`

If you see that, you need to turn access on for the grader:

`$ e11 access on`

Remember, you can request that the lab be graded at any time using this command:

`$ e11 grade lab1`

Note: If you have not passed all of the tests, we will continue to grade your lab once a day in the 5 days leading up to the assignment being due. After the assignment is due, you can continue to run the `check` command, but you can no longer be graded.

You can run the `grade` command as many times as you want. The highest grade is the one that we will export to Canvas. We will record your highest grade in Canvas the week after the lab is due.

Once you have been graded, you can suspend your instance and restart it later to do lab2. Or you can leave it running — if you are on the free tier, you will not be charged.

**Do not terminate your instance. If you do, you will need to create a new one, re-run the installer, and redo lab 1 before proceeding to lab 2\!**

# **Going Further** {#going-further}

Amazon’s EC2 instances are the basis of many services in Amazon AWS. Beyond spinning up your own virtual machines, many of Amazon's services (such as the [Amazon Relational Database Service](https://aws.amazon.com/rds/)) simply spin up EC2 instances and then install a pre-specified software package.

If you are interested in learning more about your EC2 instance, here are some things to try:

## **Explore the [Instance Metadata Service](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html)** {#explore-the-instance-metadata-service}

The instance metadata service is protected with an authentication token. To use it, you first need to get a token:

**TOKEN=$(curl \-X PUT "http://169.254.169.254/latest/api/token" \-H "X-aws-ec2-metadata-token-ttl-seconds: 21600")**

Once you have the token, you can start to explore:

**curl \-H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/**

##

## **Learn about SSH Access** {#learn-about-ssh-access}

You don’t need to log into the AWS console to access your EC2 instance — you can use the `ssh` client from your Mac or Windows system.

You log into your instance using the SSH protocol. When you created your instance, the public key was stored in the file `/home/ec2-user/.ssh/authorized_keys`. You can add more keys to this file. (Attackers that break into your system frequently add their own\!) So take a look at these files:

$ **ls \-al .ssh**
total 28
drwx------.  2 ec2-user ec2-user    71 Jan 14 16:00 ./
drwx------. 13 ec2-user ec2-user 16384 Jan 18 23:33 ../
\-rw-------.  1 ec2-user ec2-user    92 Jan 14 02:39 authorized\_keys
\-rw-------.  1 ec2-user ec2-user   828 Jan 14 16:00 known\_hosts
\-rw-r--r--.  1 ec2-user ec2-user    92 Jan 14 16:00 known\_hosts.old

The `known_hosts` file is a list of other servers that this server has contacted with ssh. Do you have one?

Apple has [documentation for using ssh from your computer](https://support.apple.com/zh-sg/guide/mac-help/mchlp1066/mac).

If you are using a Windows computer, we recommend installing [Windows Subsystem for Linux](https://learn.microsoft.com/en-us/windows/wsl/install) and then using the Linux ssh command, which you will need to install. You can do that with these commands:

Install both the ssh client and server:

**`sudo apt install openssh-server`**

This will allow you to remotely access other machines from your Windows computer. If you want to access your Windows computer remotely via SSH, you will need to do some additional work. [This article we found](https://jmmv.dev/2022/02/wsl-ssh-access.html) contains the necessary instructions. s

## **Look behind the curtain** {#look-behind-the-curtain}

Interested in building your own version of our server?  Here’s how we did it:

* The CSCI-E-11.ORG domain is hosted with [Amazon’s Route53 service](https://aws.amazon.com/route53/). This makes it easy for us to update the DNS records.
* The emails are sent via Amazon’s [Simple Email Service](https://docs.aws.amazon.com/sdk-for-javascript/v2/developer-guide/ses-examples.html).  If you create your own SES account, you can send an email to pre-registered email addresses. However, to minimize spam, you cannot email arbitrary email addresses (like us emailing to you) without getting approval from an AWS admin. The first time we asked for approval, we were denied\! We had to appeal.
* Our “server” is actually a Python function that runs on [Amazon Lambda](https://aws.amazon.com/lambda/) using the Amazon [Serverless Application Model (SAM)](https://aws.amazon.com/serverless/sam/).  (Note: we do *not* use the popular “Serverless” framework from serverless.org.)

You can find our entire source code for the S3 watching system that receives events and sends emails [here](https://github.com/Harvard-CSCI-E-11/spring25/tree/main/staff/s3watch). You can try standing up your own program to watch your S3 bucket. If you want to send an email, you’ll need to register your email address with SES.

[image1]: <images/1-logo.png>
[image2]: <images/1-create.png>
[image3]: <images/1-signup.png>
[image4]: <images/1-plan.png>
[image5]: <images/1-console.png>
[image6]: <images/1-accountmenu.png>
[image7]: <images/1-budget.png>
[image8]: <images/1-securitymenu.png>
[image9]: <images/1-ec2.png>
[image10]: <images/1-launchform.png>
[image11]: <images/1-launchbutton.png>
[image12]: <images/1-success.png>
[image13]: <images/1-instance.png>
[image14]: <images/1-ec2icon.png>
[image15]: <images/1-running.png>
[image16]: <images/1-controls.png>
[image17]: <images/1-connectform.png>
[image18]: <images/1-connectbutton.png>
[image19]: <images/1-terminal.png>
[image20]: <images/1-clone.png>
[image21]: <images/1-ipaddress.png>
[image22]: <images/1-credentials.png>
[image23]: <images/1-actionsmenu.png>
[image24]: <images/1-rolewarning.png>
[image25]: <images/1-roles.png>
[image26]: <images/1-trustedentity.png>
[image27]: <images/1-accountpolicy.png>
[image28]: <images/1-ec2policy.png>
[image29]: <images/1-roleform.png>
[image30]: <images/1-rolebutton.png>
[image31]: <images/1-rolecreated.png>
[image32]: <images/1-roletab.png>
[image33]: <images/1-refresh.png>
[image34]: <images/1-roleselect.png>
[image35]: <images/1-security.png>
[image36]: <images/1-identity.png>
[image37]: <images/1-dashboard.png>
[image38]: <images/1-reload.png>
[image39]: <images/1-dashboardcheck.png>
[image40]: <images/1-accesson.png>
[image41]: <images/1-accessoff.png>
[image42]: <images/1-email.png>
[image43]: <images/1-attackers.png>
