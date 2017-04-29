================================================================================
  Archivematica Acceptance Tests
================================================================================

Acceptance tests for Archivematica_ (AM) written using Python behave_ and the
Gherkin_ language. Deploying an Archivematica system to test against is a
necessary separate step. The tests use Selenium_ to launch a browser in order to
interact with Archivematica's web GUI. (They also make vanilla requests to AM's
API using Python's Requests_ library). They have been run successfully with
Firefox and Chrome, and in CI scenarios using Xvfb_ (X virtual framebuffer).

Using Gherkin to express tests makes them quite readable to non-programmers.
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


Installation
================================================================================

Create a virualenv using Python 3 and activate it::

    $ virtualenv -p python3 env
    $ source env/bin/activate

Clone the source (either to the same machine where Archivematica is installed,
or to another)::

    $ git clone https://github.com/artefactual-labs/archivematica-acceptance-tests.git

Since lxml is a dependency, you may need to install python3-dev. On Ubuntu
14.04 with Python 3::

    $ sudo apt-get install python3-dev

Install the Python dependencies::

    $ pip install -r requirements.txt

One way to run the tests headless, i.e., without a visible browser, is with
Xvfb. To install Xvfb on Ubuntu 14.04::

    $ sudo apt-get update
    $ sudo apt-get install -y xorg xvfb dbus-x11 xfonts-100dpi xfonts-75dpi xfonts-cyrillic

See also:

- http://stackoverflow.com/questions/34548472/trying-to-configure-xvfb-to-run-firefox-headlessly
- http://elementalselenium.com/tips/38-headless

A browser (Chrome or Firefox) must be installed on the system where the tests
are being run; see below. On a dev or CI server, this may require installation.


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


Troubleshooting
================================================================================

If the tests generate ``cannot allocate memory`` errors, there may be unclosed
browsers. Run the following command to look for persistent firefox or chrome
browsers and kill them::

    $ ps --sort -rss -eo rss,pid,command | head


Usage
================================================================================

Basic usage::

    $ behave

The above will launch many annoying browser windows. Use Xvfb to hide all that
rubbish. Start Xvfb on display port 42 and background the process::

    $ Xvfb :42 &

Tell the terminal session to use the display port::

    $ export DISPLAY=:42

Run the tests, this time just those targetting the correct creation of PREMIS
events::

    $ behave --tags=premis-events --tags=standard --no-skipped

There is also a convenience script for running just the tests that target
Archivematica version 1.6::

    $ ./runtests.sh

The scenarios in the .feature files may be tagged with zero or more tags. The
above command runs all scenarios tagged ``@premis-events`` and ``@standard``.

There are two convenience scripts for closing all transfers and closing all
ingests via the GUI (i.e., using Selenium)::

    $ ./close_all_transfers.sh
    $ ./close_all_ingests.sh


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
