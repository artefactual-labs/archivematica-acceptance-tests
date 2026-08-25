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

The tests use Playwright_ to interact with Archivematica's web interfaces in
Chrome or Firefox. Browser drivers are not required; see `Browsers and
headless mode`_ for installation details.


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

    $ git clone https://github.com/artefactual-labs/archivematica-acceptance-tests.git
    $ cd archivematica-acceptance-tests
    $ make sync-runtime
    $ make install-browsers
    $ make behave


Detailed installation instructions
--------------------------------------------------------------------------------

To install these tests manually, first install uv using the
`uv installation documentation`_, then clone the source::

    $ git clone https://github.com/artefactual-labs/archivematica-acceptance-tests.git
    $ cd archivematica-acceptance-tests

On Ubuntu, install the system tools used by the browser and Python installers::

    $ sudo apt-get install curl python3-dev unzip

Finally, create the project environment and install its locked runtime
dependencies. You can activate the environment if you want to invoke commands
without the ``uv run`` prefix::

    $ make sync-runtime
    $ make install-browsers
    $ source .venv/bin/activate


Managing Python dependencies
--------------------------------------------------------------------------------

Declare runtime dependencies in ``pyproject.toml`` and development dependencies
in its ``dependency-groups.dev`` table. ``uv.lock`` records the exact versions
used across supported Python versions and platforms and must be committed.
This repository is configured as a uv virtual project because it is a test
suite rather than an installable Python package. It uses uv's project commands
(``uv lock``, ``uv sync``, and ``uv run``) rather than the pip-compatible
interface. The lockfile is the sole dependency lock; requirements exports are
not maintained.

The Makefile provides shortcuts for common workflows:

- ``make sync-runtime`` installs only the dependencies needed to run the tests.
- ``make install-browsers`` installs the pinned Chrome for Testing Stable build,
  Playwright Chromium on Linux arm64, and Playwright's Firefox build.
- ``make sync`` also installs development tools.
- ``make lock-check`` verifies that ``uv.lock`` matches ``pyproject.toml``.
- ``make lock`` refreshes the lockfile without upgrading existing versions,
  while ``make upgrade`` upgrades all dependencies.
- ``make check`` verifies the lockfile and runs all pre-commit checks.
- ``make smoke-test`` runs the browser smoke test used by CI.
- ``make behave BEHAVE_ARGS="..."`` runs the acceptance tests with optional
  Behave arguments.
- ``make docker-build`` builds the test image. Override ``PYTHON_VERSION`` or
  ``DOCKER_IMAGE`` when needed.

The exact project interpreter is pinned in ``.python-version``. Local uv
commands and the ``setup-uv`` GitHub Action discover this file automatically;
the Docker builder copies it before running ``uv python install``. The
``project.requires-python`` value in ``pyproject.toml`` separately declares
the supported Python minor line and controls dependency resolution.

The CI test matrices intentionally override ``.python-version`` to exercise
every supported Python version. Normal local, lint, and Docker workflows use
the pinned version; the Makefile derives its Docker build argument from the
file by default.

To upgrade the default Python version, update ``.python-version`` and run
``make lock``. If the supported range changes, also update
``project.requires-python`` and the CI matrices; Ruff derives its target from
the minimum supported version.

``tool.uv.required-version`` in ``pyproject.toml`` declares the minimum uv
version and intentionally accepts newer global installations. Local uv commands
enforce it, and the ``setup-uv`` GitHub Action reads it automatically and
selects a compatible release. The Docker build independently pins its uv image
version and digest for reproducible builds.

To raise the minimum supported uv version, update
``tool.uv.required-version``. To upgrade the Docker build's uv release, update
``UV_VERSION`` and ``UV_DIGEST`` in ``Dockerfile``. Obtain the multi-platform
image digest with::

    $ docker buildx imagetools inspect ghcr.io/astral-sh/uv:VERSION

Standalone installer users can then run ``uv self update VERSION``; other
installations must be updated through their package manager. Finally, run
``make lock``, ``make check``, and ``make docker-build``.


Install with deploy-pub
--------------------------------------------------------------------------------

Archivematica's public Vagrant/Ansible deployment tool `deploy-pub`_ allows you
to install the AMAUAT when provisioning your virtual machine (VM). This simply
requires setting the ``archivematica_src_install_acceptance_tests`` variable to
``"yes"`` in the Ansible playbook's ``vars-`` file, e.g.,
vars-singlenode-qa.yml.


Browsers and headless mode
--------------------------------------------------------------------------------

Run ``make install-browsers`` after syncing dependencies. It installs the
project's pinned Chrome for Testing Stable build and the Firefox build matched
to the locked Playwright release. Although regular Chrome Stable is available
for Linux arm64, Chrome for Testing Stable does not publish a portable Linux
arm64 artifact. The installer uses Playwright's matching Chromium build on
that platform; other supported Linux and macOS platforms use the pinned Chrome
for Testing Stable build.

Chrome is the default, with Chromium used on Linux arm64. Select Firefox with
``-D browser_name=Firefox``. To use a Chrome executable installed elsewhere,
pass ``-D chrome_executable_path=/absolute/path/to/chrome`` or set
``CHROME_EXECUTABLE_PATH``.

Set ``HEADLESS=1`` when no display is available. Playwright provides headless
operation directly, so a VNC or virtual-display server is not required. On a
failed browser scenario, screenshots and Playwright traces are retained under
``output/playwright/``.


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
scenarios). If the virtual environment is not activated, use ``make behave``
and pass the same options through ``BEHAVE_ARGS``, for example::

    $ make behave BEHAVE_ARGS="--tags=icc,ipc"

The following command is a more realistic example of running the AMAUAT from
an activated environment::

    $ behave \
        --tags=icc \
        --no-skipped \
        -v \
        --stop \
        -D am_version=1.7 \
        -D home=archivematica \
        -D transfer_source_path=archivematica/archivematica-sampledata/TestTransfers/acceptance-tests \
        -D browser_name=Firefox \
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
  - The ``-D browser_name=Firefox`` flag tells Behave to use Firefox instead of
    the default Chrome browser.
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
.. _Playwright: https://playwright.dev/python/
.. _Requests: http://docs.python-requests.org/en/master/
.. _`deploy-pub`: https://github.com/artefactual/deploy-pub.git
.. _`Archivematica Docker Compose deployment method`: https://github.com/artefactual-labs/am/tree/master/compose
.. _`am`: https://github.com/artefactual-labs/am/tree/master/compose
.. _lxml: http://lxml.de/
.. _`Docker Compose`: https://github.com/artefactual-labs/am/tree/master/compose
.. _`Vagrant/Ansible`: https://github.com/artefactual/deploy-pub/tree/master/playbooks/archivematica-xenial
.. _`Manual`: https://www.archivematica.org/en/docs/archivematica-1.7/
.. _`behavior-driven development (BDD)`: https://en.wikipedia.org/wiki/Behavior-driven_development
.. _`Behave documentation`: http://behave.readthedocs.io/en/latest/
.. _`uv installation documentation`: https://docs.astral.sh/uv/getting-started/installation/
