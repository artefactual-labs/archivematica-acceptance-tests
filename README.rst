================================================================================
  Archivematica Acceptance Tests
================================================================================

This respository contains acceptance tests for Archivematica written using
Python behave and the Gherkin language.


Installation
================================================================================

Create a virualenv using Python 3 and activate it::

    $ sudo virtualenv -p python3 env
    $ source env/bin/activate

Install the dependencies::

    $ pip install -r requirements.txt


Configuration
================================================================================

In order for these tests to work, they must be run against the version of
Archivematica that they were written to target and the target Archivematica
Storage Service must contain the transfers in test-transfers/. This section
shows how to configure a system that meets those requirements.


Install a Compatible Archivematica System
--------------------------------------------------------------------------------

In order for these tests to work, they must be run against the version of
Archivematica that they were written to target. The deploy-pub ansible playbook
set at https://github.com/jrwdunham/deploy-pub/tree/dev/issue-9478-acceptance-tests-preforma
should allow you to install such a system. Assuming you have VirtualBox,
Vagrant and Ansible installed, use the following instructions::

    $ git clone https://github.com/jrwdunham/deploy-pub.git
    $ cd deploy-pub
    $ git checkout dev/issue-9478-acceptance-tests-preforma
    $ cd playbooks/archivematica
    $ ansible-galaxy install -f -p roles/ -r requirements.yml
    $ vagrant up

The tests also assume that you have configured your Archivematica installation
so that it is being served at the following URL and has an administrator-level
user with the following username and password. These values can be altered in
features/environment.py.

- URL:      http://192.168.168.192/
- username: test
- password: testtest


Move the Test Transfers Over
--------------------------------------------------------------------------------

These tests require that the test transfer directories in test-transfers/ be
present in the directory specified in
features/environment.py:TRANSFER_SOURCE_PATH (which defaults to
/home/vagrant/acceptance-tests/. Assuming you are using Artefactual's
deploy-pub repo to create an Archivematica installation to test on, one way to
move the test transfers over is::

    $ cp -r test-transfers /path/to/archivematica/vagrant/synced/folder
    $ cd /path/to/archivematica/Vagrantfile/dir/
    $ vagrant ssh
    $ vagrant@am-local:~$ mv /vagrant/src/test-transfers ~/acceptance-tests


Usage
================================================================================

To run the tests::

    $ behave

There are also two convenience scripts for closing all transfers and closing
all ingests via the GUI (i.e., using Selenium)::

    $ python close_all_transfers.py
    $ python close_all_ingests.py

