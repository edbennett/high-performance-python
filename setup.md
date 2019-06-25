---
title: Setup
---

To follow this workshop, you will need three things: Python, an account on the Supercomputing Wales facility,
and an SSH client.


{% comment %} {% endcomment %}
<div id="scw">
  <h3>Supercomputing Wales</h3>

  <p>
  In this workshop we will use the Supercomputing Wales facilities to
  learn to use High-Performance Computing. For this, you will need an
  account on the Supercomputing Wales facilities.
  </p>

  <p>
  If you already have previously attended the "Introduction to High Performance Computing" training, and so have already joined the "scw1389" project, please contact
  {{site.email}} and we will reactivate your membership.
  </p>
  
  <p>
  If you are new to SA2C training events, create and account through the
  following steps.
  </p>
  <ol>
    <li>Visit <a href="https://my.supercomputing.wales/">My
    Supercomputing Wales</a></li>
	<li>Sign in with your Swansea University email and password</li>
	<li>Fill in the form requesting a Supercomputing Wales
    account. Your account request will be processed by an
    administrator.</li>
	<li>Once you receive an email indicating that your account has been
    created, then revisit <a
    href="https://my.supercomputing.wales/">My Supercomputing
    Wales</a>, and log in again if necessary.</li>
	<li>Click the "Reset SCW Password" button, and enter a password
    that you will use to access the Supercomputing Wales
    hardware. (This does not have to be the same as your Swansea
    University password.) Click Submit.</li>
	<li>Under "Join a project", enter {{site.scw_project}} as the
    project code for this training session, and click "Join".</li>
  </ol>
</div> {% comment %} End of 'Supercomputing Wales' section. {% endcomment %}

{% comment %} {% endcomment %}
<div id="SSH">
  <h3>SSH</h3>
  
  SSH is used to connect to the Unix shell on machines across the network.

  <div class="row">
    <div class="col-md-4">
      <h4 id="ssh-windows">Windows</h4>
      <ol>
        <li> If you are using Windows and have previously followed the <a href="https://swcarpentry.github.io/shell-novice">Unix Shell</a> lesson,
then the Git Bash tool installed as part of that lesson will provide you with this.</li>
        <li> Otherwise, then download and install <a href="https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html">PuTTY</a>.</li>
      </ol>
    </div>
    <div class="col-md-4">
      <h4 id="ssh-mac">macOS</h4>
      <ol>
        <li>SSH is installed as part of macOS and is available via the Terminal application.</li>
      </ol>
    </div>
    <div class="col-md-4">
      <h4 id="ssh-linux">Linux</h4>
      <ol>
        <li>SSH is installed as part of Linux and is available through a terminal/console application.</li>
      </ol>
    </div>
  </div>
</div>
{% comment %} End of 'SSH' section {% endcomment %}


### Python

In this lesson we will be using Python 3 with some of its scientific libraries.
Although one can install a "plain vanilla" Python 3 and all required libraries "by hand",
we recommend installing Anaconda, a Python distribution
that comes with everything we need for the lesson.

[Python](https://python.org) is a popular language for
research computing, and great for general-purpose programming as
well.  Installing all of its research packages individually can be
a bit difficult, so we recommend
[Anaconda](https://www.anaconda.com/distribution/),
an all-in-one installer.

Regardless of how you choose to install it,
**please make sure you install Python version 3.x**
(e.g., 3.6 is fine).

<div class="row">
    <div class="col-md-4">
      <h4 id="python-windows">Windows</h4>
      <a href="https://www.youtube.com/watch?v=xxQ0mzZ8UvA">Video Tutorial</a>
        <ol>
        <li>Open <a href="https://www.anaconda.com/download/#windows">https://www.anaconda.com/download/#windows</a> with your web browser.</li>
        <li>Download the Python 3 installer for Windows.</li>
        <li>Install Python 3 using all of the defaults for installation <em>except</em> make sure to check <strong>Add Anaconda to my PATH environment variable</strong>.</li>
        </ol>
    </div>
    <div class="col-md-4">
      <h4 id="ssh-mac">macOS</h4>
      <ol>
        <a href="https://www.youtube.com/watch?v=TcSAln46u9U">Video Tutorial</a>
        <ol>
            <li>Open <a href="https://www.anaconda.com/download/#macos">https://www.anaconda.com/download/#macos</a> with your web browser.</li>
            <li>Download the Python 3 installer for OS X.</li>
            <li>Install Python 3 using all of the defaults for installation.</li>
        </ol>
      </ol>
    </div>
    <div class="col-md-4">
      <h4 id="ssh-linux">Linux</h4>
        <ol>
            <li>Open <a href="https://www.anaconda.com/download/#linux">https://www.anaconda.com/download/#linux</a> with your web browser.</li>
            <li>Download the Python 3 installer for Linux.<br>
                    (The installation requires using the shell. If you aren't
                    comfortable doing the installation yourself
                    stop here and request help at the workshop.)
            </li>
            <li>
                    Open a terminal window.
            </li>
            <li>
                    Type <pre>bash Anaconda3-</pre> and then press
                    <kbd>Tab</kbd>. The name of the file you just downloaded should
                    appear. If it does not, navigate to the folder where you
                    downloaded the file, for example with:
                    <pre>cd Downloads</pre>
                    Then, try again.
            </li>
            <li>
                    Press <kbd>Return</kbd>. You will follow the text-only prompts. To move through
                    the text, press <kbd>Spacebar</kbd>. Type <code>yes</code> and
                    press enter to approve the license. Press enter to approve the
                    default location for the files. Type <code>yes</code> and
                    press enter to prepend Anaconda to your <code>PATH</code>
                    (this makes the Anaconda distribution the default Python).
            </li>
            <li>
                    Close the terminal window.
            </li>
        </ol>
    </div>
</div>
