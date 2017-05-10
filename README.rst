================================================================================
  Archivematica Acceptance Tests
================================================================================

Acceptance tests for Archivematica_ (AM) are written using Python behave_ and the
Gherkin_ language. Acceptance tests serve three goals: they enable semi-automated
or fully automated execution of tests, they can be used to specify system 
behaviour as part of Behaviour Driven Development (BDD) methods and they serve as
"living documentation" of how the system works. 

This document sets out 

- how the tests are organised in Github (so readers can determine what tests 
exist, what they do and which ones they would like to run) 
- how to install and configure the tests
- how to execute the tests against a particular deployment of Archivematica. 

Structure & Organisation of Archivematica Acceptance Tests
================================================================================

Features
--------------------------------------------------------------------------------

Features describe a particular user story. They are written in Gherkin, which can
be understood by non-programmers, while also being structured enough to support
automated validation and testing. (A feature is an acceptance test; the two terms
are used interchangeably in this document.)

Consider the following snippet from the premis-events.feature file::

    Feature: PREMIS events are recorded correctly
      Users of Archivematica want to be sure that the steps taken by
      Archivematica are recorded correctly in the resulting METS file, according
      to the PREMIS specification.

      Scenario: Isla wants to confirm that standard PREMIS events are created
      Given that the user has ensured that the default processing config is in its default state
      When a transfer is initiated on directory ~/archivematica-sampledata/SampleTransfers/BagTransfer
      Then in the METS file there are/is 7 PREMIS event(s) of type ingestion

The ``Given``, ``When`` and ``Then`` statements in the .feature files are
implemented by "step" functions in the features/steps/steps.py file, which, in
turn, may interact with Archivematica GUI(s) by calling methods of an
``archivematicaselenium.py::ArchivematicaSelenium`` instance.

Organisation of Features and use of Tags
--------------------------------------------------------------------------------
Features are held in the Features directory with the following sub-directories:

- the **core** directory holds tests that should pass the latest stable release
- the **dev** directory holds tests that should pass against a particular
development or qa release of Archivematica
- client or project directories can be added for tests that have dependencies on
a particular client or project deployment (e.g. integration with other systems)

Tags (starting with an '@' sign) provide one or moe 'labels' for each feature and 
each scenario within a feature. When the tests are executed, tags allow a tester 
to indicate which features or scenarios they want to run (or not run). 

- @am16 tag indicates the feature (or scenario) should pass against a stable 
release of Archivematica 1.6
- @dev indicates that the feature will only run on a particular dev or qa 
release of Archivematica
- every feature should have a unique tag (e.g. @premis-events) and each 
scenario within a feature should have a unique tag (e.g. @registration) so that 
testers can choose whether to execute a whole feature or certain scenarios 

Github Repository Structure and Workflow
--------------------------------------------------------------------------------
The **artefactual-labs/archivematica-acceptance-tests** repo is the public 
repository for Archivematica acceptance tests. Anyone can contribute to the 
public set of tests by creating a fork of this repo and making a pull request 
of new features developed. 

Pull requests should be made from a dev branch while the feature is in 
development. Features that are complete and pass in a development environment
can be merged to the QA branch. When a major release of Archivematica is made, 
all QA features should be tested and those that pass merged into the Master branch.

Installation
================================================================================
Acceptance tests can be run from one machine, and executed against a deployment
of Archivematica that may or may not be on the same machine.

The tests use Selenium_ to launch a browser in order to interact with 
Archivematica's web GUI. (They also make vanilla requests to AM's
API using Python's Requests_ library). They have been run successfully with
Firefox and Chrome, and in CI scenarios using Xvfb_ (X virtual framebuffer).

The installation instructions describe how to install the tests, supporting code 
and browser on the machine where the tests will be executed from.

The configuration instructions describe how to specify the specific deployment of
Archivematica to test against (e.g. the URL, the user account and password that
will used and so on). 

These instructions assume some basic familiarity with the command line, python 
and git / github. These instructions_ for setting up command line tools and python
(on a Mac) are good for beginners and should be adequate to enable you to follow
the rest of these instructions (but your mileage may vary).   

Installation of Acceptance Tests & Supporting Code
--------------------------------------------------------------------------------
Create a virualenv using Python 3 and activate it::

    $ virtualenv -p python3 env
    $ source env/bin/activate

Clone the source (to whichever machine you will run the tests from)::

    $ git clone https://github.com/artefactual-labs/archivematica-acceptance-tests.git

Since lxml is a dependency, you may need to install python3-dev. On Ubuntu
14.04 with Python 3::

    $ sudo apt-get install python3-dev

Install the Python dependencies::

    $ pip install -r requirements.txt

Installation of Browser and Browser Driver
--------------------------------------------------------------------------------
**Running tests from your desktop / laptop**

The acceptance tests can be run using Chrome or Firefox. We recommend Chrome. You will 
need to ensure the browser is installed, and that the driver is installed. See: 

- https://www.google.ca/chrome/
- http://www.kenst.com/2015/03/installing-chromedriver-on-mac-osx/

As you run the tests, a browser will be opened on the machine you run them from.
The test code will control the browser, clicking and entering data as required to 
complete the test.  

**Running tests from the server or a Linux Desktop**

To execute the tests from a server, you will need to run in 'headless' mode, without 
a visible browser (a server is 'headless' because it doesn't have a monitor). 
The browser & drivers must be installed, as well as a tool called Xvfb that enables 
headless operation. 
To install Xvfb on Ubuntu 14.04::

    $ sudo apt-get update
    $ sudo apt-get install -y xorg xvfb dbus-x11 xfonts-100dpi xfonts-75dpi xfonts-cyrillic

(note that while it is theoretically possible to run headless from a Windows or Mac 
desktop / laptop, it is challenging. We don't provide instructions here for doing that.)

See also:

- http://stackoverflow.com/questions/34548472/trying-to-configure-xvfb-to-run-firefox-headlessly
- http://elementalselenium.com/tips/38-headless

Install Chrome on Ubuntu 14.04
--------------------------------------------------------------------------------

Following the instructions from
http://askubuntu.com/questions/510056/how-to-install-google-chrome::

    $ wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add - 
    $ sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
    $ sudo apt-get update
    $ sudo apt-get install google-chrome-stable
    $ google-chrome --version
    Google Chrome 57.0.2987.133

Install chromedriver following the instructions at
https://christopher.su/2015/selenium-chromedriver-ubuntu/::

    wget -N http://chromedriver.storage.googleapis.com/2.26/chromedriver_linux64.zip
    unzip chromedriver_linux64.zip
    chmod +x chromedriver
    sudo mv -f chromedriver /usr/local/share/chromedriver
    sudo ln -s /usr/local/share/chromedriver /usr/local/bin/chromedriver
    sudo ln -s /usr/local/share/chromedriver /usr/bin/chromedriver


Install a specific Firefox version on Ubuntu 14.04
--------------------------------------------------------------------------------

We have had variable success running these tests on various versions of
Firefox. It may be necessary to purge an existing Firefox and install an older
version. We have had some success with Firefox v. 47 and provide instructions
for installing that on Ubuntu 14.04 here::

    $ firefox -v
    Mozilla Firefox 48.0
    $ sudo apt-get purge firefox
    $ wget sourceforge.net/projects/ubuntuzilla/files/mozilla/apt/pool/main/f/firefox-mozilla-build/firefox-mozilla-build_47.0.1-0ubuntu1_amd64.deb
    $ sudo dpkg -i firefox-mozilla-build_47.0.1-0ubuntu1_amd64.deb 
    $ firefox -v
    Mozilla Firefox 47.0.1


Configuration
================================================================================

Install a Compatible Archivematica System
--------------------------------------------------------------------------------

The tests require access to a live Archivematica installation. The tests tagged
``am16`` should pass against Archivematica version 1.6. Those tagged ``dev``
require specific development branches to be installed, e.g., ``dev`` tests also
tagged with ``preforma`` require AM at branch dev/issue-9478-preforma. Such
dependencies should be indicated in the comments of the relevant .feature files.

Archivematica is most easily installed using the deploy-pub ansible playbook
set at
https://github.com/artefactual/deploy-pub.git
Assuming you have VirtualBox, Vagrant and Ansible installed, here is the
quickstart::

    $ git clone https://github.com/artefactual/deploy-pub.git
    $ cd deploy-pub/playbooks/archivematica
    $ ansible-galaxy install -f -p roles/ -r requirements.yml
    $ vagrant up


Configuration via features/environment.py or Behave userdata options
--------------------------------------------------------------------------------

The tests assume by default that you have configured your Archivematica
installation to be served at a specific URL, viz. http://192.168.168.192/.
The tests should be able to detect a fresh AM install, in which case they will
create an administrator-level user with username ``test`` and
password ``testtest``. These and other configuration options can be overridden
by altering the following constants in features/environment.py...::

- ``AM_URL``
- ``AM_USERNAME``
- ``AM_PASSWORD``
- ``SS_URL``
- ``SS_USERNAME``
- ``SS_PASSWORD``
- ``TRANSFER_SOURCE_PATH``
- ``HOME``
- ``DRIVER_NAME``

... or by passing the equivalent lowercased parameters as Behave "userdata"
options. For example, the following would run the tests against an
Archivematica instance at 123.456.123.456 using the Firefox driver::

    $ behave \
        -D am_url=http://192.168.168.16 \
        -D ss_url=http://192.168.168.16:8000/ \
        -D driver_name=Firefox


.. _Archivematica: https://github.com/artefactual/archivematica
.. _behave: http://pythonhosted.org/behave/
.. _Gherkin: https://github.com/cucumber/cucumber/wiki/Gherkin
.. _Selenium: http://www.seleniumhq.org/
.. _Requests: http://docs.python-requests.org/en/master/
.. _Xvfb: https://www.x.org/archive/X11R7.6/doc/man/man1/Xvfb.1.xhtml
.. _instructions: https://www.digitalocean.com/community/tutorials/how-to-install-python-3-and-set-up-a-local-programming-environment-on-macos

How to execute Acceptance tests
================================================================================

Basic Execution (with browser)
--------------------------------------------------------------------------------
If you have just installed the tools, your virtualenv will still be activated. 
If you installed some time ago, go to the directory you installed the tests in 
and activate your python 3 virtualenv::

    $ source env/bin/activate

You initiate execution of the tests with the behave command::

    $ behave

The behave command will attempt to execute all of the tests that exist in the 
features directory. You can target specific tests (or scenarios within them) 
by specifying their tags. For example, the following command will only run the 
premis-events.feature (tagged @premis-events), and within that, only the one 
scenario with the tag @standard::

    $ behave --tags=premis-events --tags=standard --no-skipped

There is also a convenience script for running just the tests that target
Archivematica version 1.6::

    $ ./runtests.sh

There are two convenience scripts for closing all transfers and closing all
ingests via the GUI (i.e., using Selenium)::

    $ ./close_all_transfers.sh
    $ ./close_all_ingests.sh
    
Headless Execution (for server execution)
--------------------------------------------------------------------------------

Before running the commands above, use Xvfrb. Start Xvfb on display port 42 
and background the process::

    $ Xvfb :42 &

Tell the terminal session to use the display port::

    $ export DISPLAY=:42


Troubleshooting
================================================================================

If the tests generate ``cannot allocate memory`` errors, there may be unclosed
browsers. Run the following command to look for persistent firefox or chrome
browsers and kill them::

    $ ps --sort -rss -eo rss,pid,command | head


