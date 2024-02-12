.. image:: https://github.com/artefactual-labs/archivematica-acceptance-tests/actions/workflows/test.yml/badge.svg
    :target: https://github.com/artefactual-labs/archivematica-acceptance-tests/actions/workflows/test.yml

Archivematica Automated User Acceptance Tests (AMAUAT)
================================================================================

This repository contains automated user acceptance tests for Archivematica_
(AM) written using the Python behave_ library and the Gherkin_ language. Using
Gherkin to express tests makes them readable to a wide range of Archivematica
users and stakeholders [1]_. Consider the following snippet from the *PREMIS events*
feature file (``premis-events.feature``)::

    Feature: PREMIS events are recorded correctly
      Users of Archivematica want to be sure that the steps taken by
      Archivematica are recorded correctly in the resulting METS file, according
      to the PREMIS specification.

      Scenario: Isla wants to confirm that standard PREMIS events are created
        Given that the user has ensured that the default processing config is in its default state
        When a transfer is initiated on directory ~/archivematica-sampledata/SampleTransfers/BagTransfer
        Then in the METS file there are/is 7 PREMIS event(s) of type ingestion

The ``Given``, ``When`` and ``Then`` statements in the feature files allow us
to put the system into a known state, perform user actions, and then make
assertions about the expected outcomes, respectively. These steps are
implemented by *step* functions in Python modules located in the
``features/steps/`` directory, which, in turn, may interact with Archivematica
GUIs and APIs by calling methods of an ``ArchivematicaUser`` instance as
defined in the ``amuser`` package. For detailed guidance on adding feature
files, implementing steps, or adding AM user abilities, please see the
`Developer documentation <docs/developer-documentation.rst>`_. For examples of
using these tests to run (performance) experiments on Archivematica, see
`Running Experiments with the AMAUAT <docs/running-experiments.rst>`_.


Table of Contents
--------------------------------------------------------------------------------

- `High-level overview`_
- `Installation`_
- `Usage`_


High-level overview
================================================================================

The AMAUAT are a completely separate application from `Archivematica`_ (AM) and
the Archivematica `Storage Service`_ (SS). They require that you already have
an Archivematica instance deployed somewhere that you can test against (see
`Installing Archivematica`_.) The tests must be supplied with configuration
details, including crucially the URLs of the AM and SS instances as well as
valid usernames and passwords for authenticating to those instances. The AM
instance being tested may be running locally on the same machine or remotely on
an external server. Note that running all of the AMAUAT tests to completion will
likely take more than one hour and will result in several transfers, SIPs, and
AIPs being created in the AM instance that is being tested.

The tests use the `Selenium WebDriver`_ to launch a web browser in order to
interact with Archivematica's web interfaces. Therefore, you may need to
install a web browser (Chrome or Firefox) and the appropriate Selenium drivers;
see the `Browsers, drivers and displays`_ section for details.


Installation
================================================================================

This section describes how to install the AMAUAT. If you have done this before
and just need a refresher, see the `Installation quickstart`_. If you are
installing manually for the first time, see the `Detailed installation
instructions`_. If you are testing a local Archivematica deploy created using
`deploy-pub`_ (Vagrant/Ansible), then you can configure that system to install
these tests for you: see the `Install with deploy-pub`_ sections. If you are
testing a local deploy created using `am`_ (Docker Compose), then the tests
should be installed for you automatically.


Installation quickstart
--------------------------------------------------------------------------------

The following list of commands illustrates the bare minimum required in order
to install and run the tests. Note that a real-world invocation of the
``behave`` command will require the addition of flags that are particular to
your environment and the details of the Archivematica instance that you are
testing against (see Usage_). If you have never run these tests before, please
read the `Detailed installation instructions`_ first.

::

    $ virtualenv -p python3 env
    $ source env/bin/activate
    $ git clone https://github.com/artefactual-labs/archivematica-acceptance-tests.git
    $ cd archivematica-acceptance-tests
    $ pip install -r requirements.txt
    $ behave


Detailed installation instructions
--------------------------------------------------------------------------------

To install these tests manually, first create a virtual environment using Python
3 and activate it::

    $ virtualenv -p python3 env
    $ source env/bin/activate

Then clone the source::

    $ git clone https://github.com/artefactual-labs/archivematica-acceptance-tests.git

Since lxml_ is a dependency, you may need to install python3-dev. On Ubuntu
14.04 with Python 3 the following command should work::

    $ sudo apt-get install python3-dev

Finally, install the Python dependencies::

    $ pip install -r requirements.txt


Install with deploy-pub
--------------------------------------------------------------------------------

Archivematica's public Vagrant/Ansible deployment tool `deploy-pub`_ allows you
to install the AMAUAT when provisioning your virtual machine (VM). This simply
requires setting the ``archivematica_src_install_acceptance_tests`` variable to
``"yes"`` in the Ansible playbook's ``vars-`` file, e.g.,
vars-singlenode-qa.yml.


Browsers, drivers and displays
--------------------------------------------------------------------------------

A web browser (Firefox or Chrome) must be installed on the system where the
tests are being run. On a typical desktop computer this is usually not a
problem. However, on a development or CI server, this may require extra
installation steps. You will need to consult the appropriate documentation for
installing Firefox or Chrome on your particular platform.

If you are using Chrome to run the tests, you will need to install the Selenium
Chrome driver. Instructions for `installing the Selenium Chrome driver on
Ubuntu 14.04`_ are copied below::

    wget -N http://chromedriver.storage.googleapis.com/2.26/chromedriver_linux64.zip
    unzip chromedriver_linux64.zip
    chmod +x chromedriver
    sudo mv -f chromedriver /usr/local/share/chromedriver
    sudo ln -s /usr/local/share/chromedriver /usr/local/bin/chromedriver
    sudo ln -s /usr/local/share/chromedriver /usr/bin/chromedriver

When the tests are running, they will open and close several browser windows.
This can be annoying when you are trying to use your computer at the same time
for other tasks. On the other hand, if you are running the tests on a virtual
machine or a server, chances are that that machine will not have a display and
you will require a *headless* display manager. The recommended way to run the
tests headless is with `TightVNC`_. To install TightVNC on Ubuntu 14.04::

    $ sudo apt-get update
    $ sudo apt-get install -y tightvncserver

Before running the tests, start the VNC server on display port 42 and tell the
terminal session to use that display port::

    $ tightvncserver -geometry 1920x1080 :42
    $ export DISPLAY=:42

Note that the first time you run this command, TightVNC server will ask you to
provide a password so that you can connect to the server with a VNC viewer, if
desired. If you do want to connect to the VNC session to see the tests running
in real-time, use a VNC viewer to connect to display port 42 of the IP of the
VM that is running the tests. As an example, if you are using the
``xtightvncviewer`` application on Ubuntu (``sudo apt-get install
xtightvncviewer``), you could run the following command to view the tests
running on a local machine at IP ``192.168.168.192``::

   $ xtightvncviewer 192.168.168.192:42


Installing Archivematica
--------------------------------------------------------------------------------

As mentioned previously, running the AMAUAT requires having an existing
Archivematica instance installed. While describing how to do this is beyond the
scope of this document, there are several well-documented ways of installing
Archivematica, with the Docker Compose strategy being the recommended method
for development. See the following links:

- `Docker Compose`_ Archivematica installation
- `Vagrant/Ansible`_ Archivematica installation
- `Manual`_ Archivematica installation


Usage
================================================================================

Simply executing the ``behave`` command will run all of the tests and will use
the default URLs and authentication strings as defined in
``features/environment.py``. However, in the typical case you will need to
provide Behave with some configuration details that are appropriate to your
environment and which target a specific subset of tests (i.e., feature files or
scenarios).  The following command is a more realistic example of running the
AMAUAT::

    $ behave \
        --tags=icc \
        --no-skipped \
        -v \
        --stop \
        -D am_version=1.7 \
        -D home=archivematica \
        -D transfer_source_path=archivematica/archivematica-sampledata/TestTransfers/acceptance-tests \
        -D driver_name=Firefox \
        -D am_url=http://127.0.0.1:62080/ \
        -D am_username=test \
        -D am_password=test \
        -D ss_url=http://127.0.0.1:62081/ \
        -D ss_username=test \
        -D ss_password=test

The command given above is interpreted as follows.

- The ``--tags=icc`` flag tells Behave that we only want to run the *Ingest
  Conformance Check* feature as defined in the
  ``features/core/ingest-mkv-conformance.feature`` file, which has the ``@icc``
  tag.
- The ``--no-skipped`` flag indicates that we do not want the output to be
  cluttered with information about the other tests (feature files) that we are
  skipping in this run.
- The ``-v`` flag indicates that we want verbose output, i.e., that we want any
  print statements to appear in stdout.
- The ``--stop`` flag tells Behave to stop running the tests as soon as there
  is a single failure.
- The rest of the ``-D``-style flags are Behave *user data*:

  - ``-D am_version=1.7`` tells the tests that we are targeting an
    Archivematica version 1.7 instance.
  - The ``-D home=archivematica`` flag indicates that when the user clicks the
    *Browse* button in Archivematica's Transfer tab, the top-level folder for
    all ``~/``-prefixed transfer source paths in the feature files should be
    ``archivematica/``.
  - The ``-D transfer_source_path=...`` flag indicates that when the user
    clicks the *Browse* button in Archivematica's Transfer tab, the top-level
    folder for all *relative* transfer source paths in the feature files
    should be
    ``archivematica/archivematica-sampledata/TestTransfers/acceptance-tests/``.
  - The ``-D driver_name=Firefox`` flag tells Behave to use the Firefox browser.
  - Finally, the remaining user data flags provide Behave with the URLs and
    authentication details of particular AM and SS instances.

To see all of the Behave user data flags that the AMAUAT recognizes, inspect the
``get_am_user`` function of the ``features/environment.py`` module.

To run all tests that match *any* of a set of tags, separate the tags by commas.
For example, the following will run all of the *Ingest Conformance Check*
(``icc``) and *Ingest Policy Check* (``ipc``) tests::

    $ behave --tags=icc,ipc

To run all tests that match *all* of a set of tags, use separate ``--tags``
flags for each tag. For example, the following will run only the preservation
scenario of the *Ingest Conformance Check* feature::

    $ behave --tags=icc --tags=preservation

In addition to the general guidance just provided, all of the feature files in
the ``features/`` directory should contain comments clearly indicating how they
should be executed and whether they need any special configuration (flags).


Closing all units
--------------------------------------------------------------------------------

There are two shell scripts that use the AMAUAT test functionality to close all
units (i.e., transfers or ingests). These scripts call ``behave`` internally
(targeting specific feature tags) and will therefore accept the same flags as
``behave`` itself (e.g., for specifying the AM url); the basic method for
executing these scripts is by running::

    $ ./close_all_transfers.sh
    $ ./close_all_ingests.sh


Troubleshooting
--------------------------------------------------------------------------------

If the tests generate ``cannot allocate memory`` errors, there may be unclosed
browsers windows. Run the following command to look for persistent Firefox or
Chrome browsers and kill them::

    $ ps --sort -rss -eo rss,pid,command | head


Logging
--------------------------------------------------------------------------------

All log messages are written to a file named ``AMAUAT.log`` in the root
directory. Passing the ``--no-logcapture`` flag to ``behave`` will cause all of
the log messages to also be written to stdout.


Timeouts and attempt counters
--------------------------------------------------------------------------------

At various points, these tests wait for fixed periods of time or attempt to
perform some action a fixed number of times before giving up the attempt. The
variables holding these *wait* and *attempt* values are listed with their
defaults in `features/environment.py <features/environment.py>`_, e.g.,
``MAX_DOWNLOAD_AIP_ATTEMPTS``. If you find that tests are failing because of
timeouts being exceeded, or conversely that tests that should be failing are
waiting too long for an event that will never happen, you can modify these
*wait* and *attempt* values using behave user data flags, e.g.,
``-D max_download_aip_attempts=200``.



.. [1] The Gherkin syntax and the approach of defining features by describing
   user behaviours came out of the `behavior-driven development (BDD)`_
   process, which focuses on what a user wants a system to do, and not on how
   it does it. The `Behave documentation`_ provides a good overview of the key
   concepts and their origins in BDD.

.. _Archivematica: https://github.com/artefactual/archivematica
.. _`Storage Service`: https://github.com/artefactual/archivematica-storage-service
.. _behave: https://github.com/behave/behave
.. _Gherkin: https://github.com/cucumber/cucumber/wiki/Gherkin
.. _`Selenium WebDriver`: https://www.seleniumhq.org/projects/webdriver/
.. _Requests: http://docs.python-requests.org/en/master/
.. _TightVNC: http://www.tightvnc.com/vncserver.1.php
.. _`deploy-pub`: https://github.com/artefactual/deploy-pub.git
.. _`Archivematica Docker Compose deployment method`: https://github.com/artefactual-labs/am/tree/master/compose
.. _`am`: https://github.com/artefactual-labs/am/tree/master/compose
.. _`installing the Selenium Chrome driver on Ubuntu 14.04`: https://christopher.su/2015/selenium-chromedriver-ubuntu/::
.. _lxml: http://lxml.de/
.. _`Docker Compose`: https://github.com/artefactual-labs/am/tree/master/compose
.. _`Vagrant/Ansible`: https://github.com/artefactual/deploy-pub/tree/master/playbooks/archivematica-xenial
.. _`Manual`: https://www.archivematica.org/en/docs/archivematica-1.7/
.. _`behavior-driven development (BDD)`: https://en.wikipedia.org/wiki/Behavior-driven_development
.. _`Behave documentation`: http://behave.readthedocs.io/en/latest/
