================================================================================
  Archivematica Acceptance Tests
================================================================================

This respository contains acceptance tests for Archivematica written using
Python behave and the Gherkin language.


Installation
================================================================================

Create a virualenv using Python 3 and use it::

    $ sudo virtualenv -p python3 env
    $ source env/bin/activate

Install dependencies::

    $ pip install -r requirements.txt


Configuration
================================================================================

Install a Compatible Archivematica System
--------------------------------------------------------------------------------

In order for these tests to work, they must be run against the version of
Archivematica that they were written to target. TODO: give instructions for how
to use a specific branch of deploy-pub to install the appropriate Archivematica
version.

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

The tests also require that you have configured your Archivematica installation
so that it is being served at the following URL and has an administrator-level
user with the following username and password. These values can be altered in
features/environment.py.

- URL:      http://192.168.168.192/
- username: test
- password: testtest


Usage
================================================================================

To run the tests::

    $ behave


