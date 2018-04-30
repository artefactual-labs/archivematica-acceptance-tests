================================================================================
  Developer Documentation: Archivematica Automated User Acceptance Tests
================================================================================

This document provides developer documentation for the Archivematica Automated
User Acceptance Tests (AMAUAT). This is technical documentation for those
seeking to understand how these tests work and how to contribute to them.

The Archivematica Automated User Acceptance Tests (or just the AM Acceptance
Tests, or just AT) are high-level tests of the Archivematica_ application which
use Selenium_ to drive a browser to do setup, perform user actions, and make
assertions as specified in human-readable Gherkin_ "feature" files.

Gaining a thorough understanding of the tests requires understanding these three
layers:

1. The `Feature files`_: human-readable test specifications (see
   ``features/core/``).
2. The `Steps files`_: Python implementations of the steps used in the feature
   files (see ``features/steps/``).
3. `The Archivematica User package`_: the ``ArchivematicaUser`` class which has
   the ability to interact with Archivematica via its browser-based GUIs and
   its APIs.

The following three sections describe each of these layers in more detail. The
`Configuration`_ section describes how arguments passed to the ``behave`` CLI
configure how the tests are run. Finally, the `Troubleshooting and tips`_
section provides suggestions and help for writing and debugging features and
their implementations.


Feature files
================================================================================

What are feature files?
--------------------------------------------------------------------------------

The feature files describe features of Archivematica. Each feature file defines
a ``Feature`` by declaring one or more scenarios. These ``Scenario`` objects
represent a user performing some actions on an Archivematica instance and
expecting certain results. If a ``Scenario`` is a ``Scenario Outline``, then it
will contain an ``Examples`` table and it will run once for each configuration
row in that table.

A scenario is constructed as a sequence of steps. Each step is a ``Given``, a
``When``, or a ``Then``. These setup preconditions, perform user actions, and
make assertions, respectively:

- ``Given``: put Archivematica into a known state, e.g., set the processing
  configuration in a certain way.
- ``When``: perform a user action, e.g., start a transfer on a specific
  directory, or wait for an AIP to appear in Archival Storage.
- ``Then``: make an assertion about the state of Archivematica, e.g., that the
  AIP METS file contains certain types of PREMIS events.

The step lines of a feature file all begin with one of the following words:
``Given``, ``When``, ``Then``, ``And``, or ``But``. Steps beginning with
``And``, or ``But`` have the same meaning as the previous ``Given``, ``When``,
or ``Then``. For example, the following two scenarios are exactly equivalent::

    Given the processing config is in its default state
    And the user sets UUIDs to be assigned to directories
    When the user starts a transfer on Images/
    And the user waits for the "Assign UUIDs to directories" micro-service
    Then the micro-service has status "Completed Successfully"
    And the task standard output indicates UUID creation for directories

    Given the processing config is in its default state
    Given the user sets UUIDs to be assigned to directories
    When the user starts a transfer on Images/
    When the user waits for the "Assign UUIDs to directories" micro-service
    Then the micro-service has status "Completed Successfully"
    Then the task standard output indicates UUID creation for directories

We allow for ``When+ Then+`` sequences to be repeated so that assertions may be
made between user actions. Thus the implicit grammar for an AT scenario is::

    Given+ (When+ Then+)+

For more information on how to write Gherkin, see this Gherkin_ page and this
behave_ page.


How to create new feature files
--------------------------------------------------------------------------------

New feature files should have the following properties.

1. Names. Feature file names have the ``.feature`` suffix and are lowercase with
   hyphens used to separate words, e.g., ``fpr-configuration.feature``.

2. Location. Feature files are stored in a subdirectory of the ``features/``
   directory, typically in ``features/core/``.

   - Feature files in ``features/core/`` describe core features of
     Archivematica; these features should run successfully against stable
     Archivematica releases.
   - Files that describe client or project-specific features may be placed in
     an appropriately named subdirectory of ``features/``, e.g.,
     ``features/CCA/``.

3. Tags. Feature files contain tags so that users running the ``behave``
   command can control which features get executed.

   - Each ``Feature`` in each feature file should contain a unique tag that
     succinctly identifies that feature, e.g., ``@aip-encrypt``, thereby
     allowing a user to run just that feature with ``behave
     --tags=aip-encrypt``.
   - Each ``Scenario`` or ``Scenario Outline`` should contain a descriptive tag
     that is at least unique within its ``Feature``, e.g., ``@compressed``;
     this allows a user to run just that scenario, e.g., with ``behave
     --tags=aip-encrypt --tags=compressed``.
   - Features and scenarios may contain more than one tag.
   - The special ``@wip`` tag indicates a work-in-progress and signifies that
     the feature is not yet expected to execute successfully.
   - The special ``@non-executable`` tag indicates a feature that is
     documentary in nature only and which should not be expected to execute
     successfully, i.e., pass.

4. Syntax. Feature files should be written following the formatting conventions
   exemplified in the extant feature files. Spaces, not tabs, should be used for
   indentation. Instead of providing a detailed specification, the following
   example of a truncated PID binding feature should suffice as a guide to
   formatting::

       @pid-binding
       Feature: Archivematica's entities can be assigned PIDs with specified resolution properties.
         Users of Archivematica want to be able to generate Persistent IDentifiers
         (PIDs)---in this case Handle System handles---for Files and SIP/DIPs (and
         possibly also Directories) processed by Archivematica. The PIDs are based ...
       
         Scenario Outline: Lucien wants to create an AIP with a METS file that documents the binding of persistent identifiers to all of the AIP's original files and directories, and to the AIP itself.
           Given a fully automated default processing config
           When a transfer is initiated on directory <directory_path> with accession number <accession_no>
           Then the AIP METS file documents PIDs, PURLs, and UUIDs for all files, directories and the package itself
       
           Examples: transfer sources
           | directory_path                                                                                 | accession_no | empty_dir_rel_path  |
           | ~/archivematica-sampledata/TestTransfers/acceptance-tests/pid-binding/hierarchy-with-empty-dir | 42           | dir2/dir2a/dir2aiii |

5. Documentation. Comments in Gherkin feature files are lines of text following
   the ``#`` character.

   - Each feature file should contain a comment indicating how that feature
     should be run, including any special arguments that must be passed to
     ``behave``. Best practice is to include a full ``behave`` command,
     including flags, as well as details of the type of Archivematica deploy(s)
     that the behave command was successfully run against.

6. Existing steps. Whenever possible, new feature files should use existing
   step definitions. All existing steps are defined in Python modules under
   ``features/steps/``. To view a list of all existing steps, use ``behave`` to
   view the steps catalog::

       $ behave --steps-catalog


Steps files
================================================================================

What are steps files?
--------------------------------------------------------------------------------

Steps files are Python modules defined under ``features/steps/``. The steps
used in the feature files are implemented as step functions. For example, the
following ``Given`` step may appear in any ``.feature`` file::

    Given the default processing config is in its default state

and its implementation is provided by a particular Python function in
``features/steps/steps.py``::

    @given('the default processing config is in its default state')
    def step_impl(context):
        ...

A ``behave`` step function is a function named ``step_impl`` which is decorated
with one of ``@given``, ``@when``, and ``@then``. The string argument passed to
the decorator must *exactly* match the text of the corresponding step (ignoring
the ``Given/When/Then`` keyword.) The only exception to this is when the
argument contains variable patterns which are mapped to arguments passed to
``step_impl``. For example, the step::

    When a transfer is initiated on directory ~/.../hierarchy-with-empty-dir with accession number 42

is implemented by the following function::

    @when('a transfer is initiated on directory {transfer_path} with accession'
          ' number {accession_no}')
    def step_impl(context, transfer_path, accession_no):
       ...

where the parameter ``transfer_path`` will have value
``'~/.../hierarchy-with-empty-dir'`` and ``accession_no`` will have value
``'42'``.

The ``context`` object is the first argument passed to every step function.
Each time a scenario is run, it is given a fresh scenario object accessible as
``context.scenario``. In order to preserve state across steps, you should set
attributes on this ``scenario`` object. For example, you may download an AIP
from archivematica in one step and save the path to the downloaded AIP as
``context.scenario.aip_path``. Then in a subsequent step you might access
``context.scenario.aip_path`` in order to decompress the AIP or inspect its
METS file.


How to create new steps
--------------------------------------------------------------------------------

If you need to create a step in a feature file that is not yet implemented as a
step function, then you will need to define a decorated step function for it,
as described above.

The ``features/steps/steps.py`` module is for general-purpose steps. If a step
is being used by more than one feature file, it should be defined here. If this
module becomes too large, it may be broken up into multiple logically coherent
modules.

Functions that do not implement steps but which are used by step functions
should be defined in ``features/steps/utils.py`` and imported into the step
modules as needed.

Step implementations that are specific to a particular feature file should be
defined in a sensibly named module in ``features/steps/``. For example, step
functions particular to the ``aip-encryption.feature`` feature file are defined
in ``features/steps/aip_encryption_steps.py``.

In some cases, it is convenient to be able to execute one or more steps from
within a step. This can be done by calling the ``execute_steps`` method of the
``context`` object and passing in a string of step declarations using the same
syntax in the feature files. For example, the following in a step function::

    context.execute_steps(
        'Given the default processing config is in its default state\n'
        'And there is a standard GPG-encrypted space in the storage service')

would be equivalent to the following in a feature file scenario::

    Given the default processing config is in its default state
    And there is a standard GPG-encrypted space in the storage service

Remember to include the line breaks when calling ``execute_steps`` or it will
not work as expected.



The Archivematica User package
================================================================================

The Archivematica User package in ``amuser/`` defines the ``ArchivematicaUser``
class. An ``ArchivematicaUser`` instance has "abilities" which allow it to
interact with an Archivematica instance. For example, it might use its
``browser`` ability to navigate to a particular page and click on a certain
link, its ``api`` ability to make API requests to the Archivematica instance,
or its ``docker`` or ``ssh`` abilities in order to inspect the state of some
internal artifact created by the Archivematica instance.

The step functions described in the section above can access the
``ArchivematicaUser`` instance using the ``am_user`` attribute of the
``context`` object. For example, in the step function for ``When the user
downloads the AIP`` (in steps.py) the AIP is downloaded by using the
Archivematica User's API ability and calling
``context.am_user.api.download_aip(...)``.

The ``ArchivematicaUser`` class and its abilities are structured using
composition and inheritance. The itemization below provides an overview of the
code structure as a guide for implementing new abilities or debugging existing
ones.

- ``amuser/amuser.py``: defines the ``ArchivematicaUser`` class (which inherits
  from ``amuser/base.py::Base``) with the following instance attributes
  representing abilities:

  - ``.browser``: the browser ability that uses Selenium to interact with
    Archivematica via its web interfaces.
  - ``.ssh``: the SSH ability that spawns subprocesses to make ``scp`` or
    ``ssh`` calls.
  - ``.docker``: the docker ability that spawns subprocesses to make calls to
    ``docker`` or ``docker-compose``.
  - ``.api``: the API ability that uses Python's Requests library to make API
    requests to Archivematica endpoints.
  - ``.mets``: the METS ability that can parse Archivematica METS files and
    make assertions about them.

- ``amuser/base.py``: defines the ``Base`` class, which is a super-class of
  ``ArchivematicaUser`` as well as of all of the ability classes, e.g., the
  ``ArchivematicaSeleniumAbility`` class that implements the browser ability.
  The ``Base`` class does the following:

  - Initializes all of the URL getters as configured in ``amuser/urls.py``. For
    example, ``Base`` uses the tuple ``('get_ingest_url', '{}ingest/')`` from
    urls.py to give all of its sub-class instances the ability to call
    ``self.get_ingest_url()`` in order to get the URL of the Ingest tab.

- ``amuser/utils.py``: contains general-purpose functions used by various
  Archivematica User classes.

- ``amuser/am_browser_ability.py``: defines the ``ArchivematicaBrowserAbility``
  class, which implements the ability to use a browser to interact with
  Archivematica; i.e., ``am_user.browser`` is an instance of
  ``ArchivematicaBrowserAbility``.

  - Has these super-classes:

    - ``ArchivematicaBrowserAuthenticationAbility``
    - ``ArchivematicaBrowserTransferIngestAbility``
    - ``ArchivematicaBrowserStorageServiceAbility``
    - ``ArchivematicaBrowserPreservationPlanningAbility``

  - Defines functionality for interacting with the following components of
    Archivematica. (If the class becomes too large, some of this functionality
    may be moved to other (super-)classes.)

    - Archival Storage tab (e.g., request AIP deletion)
    - Transfer Backlog tab (e.g., wait for a transfer to appear)
    - Administration tab (e.g., configure a Handle server client)
    - Processing Configuration (e.g., set a particular processing configuration
      option)
    - Installer (e.g., handle a new Archivematica installation's configuration,
      e.g., registering the SS's API key, etc.)

- ``amuser/am_browser_auth_ability.py``: defines the
  ``ArchivematicaBrowserAuthenticationAbility`` which can login to an
  Archivematica instance or a Storage Service instance.

- ``amuser/am_browser_transfer_ingest_ability.py``: defines the
  ``ArchivematicaBrowserTransferIngestAbility`` class which defines abilities
  that are common to the Transfer and Ingest tabs, e.g., waiting for a
  micro-service to appear, or making a choice at a particular decision point.

  - Has these super-classes:

    - ``ArchivematicaBrowserJobsTasksAbility``
    - ``ArchivematicaBrowserFileExplorerAbility``
    - ``ArchivematicaBrowserTransferAbility``
    - ``ArchivematicaBrowserIngestAbility)``

- ``amuser/am_browser_jobs_tasks_ability.py``: defines the
  ``ArchivematicaBrowserJobsTasksAbility`` class which defines abilities
  related to interacting with Jobs and Tasks via the GUI, e.g., getting the
  output of a job (e.g., ``Completed successfully``) or parsing all of the
  tasks of a job into a Python dict.

- ``amuser/am_browser_file_explorer_ability.py``: defines the
  ``ArchivematicaBrowserFileExplorerAbility`` class which defines abilities
  related to interacting with Archivematica's file explorer GUIs, e.g., for
  selecting a transfer source directory.

- ``amuser/am_browser_transfer_ability.py``: defines the
  ``ArchivematicaBrowserTransferAbility`` class which defines abilities
  specific to interacting with the Transfer tab, e.g., starting and approving a
  transfer.

- ``amuser/am_browser_ingest_ability.py``: defines the
  ``ArchivematicaBrowserIngestAbility`` class which defines abilities
  specific to interacting with the Ingest tab, e.g., getting a SIP UUID given
  the name of the corresponding transfer, adding metadata to an AIP, or parsing
  the normalization report.

- ``amuser/am_browser_ss_ability.py``: defines the
  ``ArchivematicaBrowserStorageServiceAbility`` class for interacting with the
  Storage Service GUI, e.g., approving AIP deletion requests, searching for an
  AIP, or viewing and mutating spaces and locations.

- ``amuser/am_browser_preservation_planning_ability.py``: defines the
  ``ArchivematicaBrowserPreservationPlanningAbility`` class for interacting
  with Archivematica's Format Policy Registry (FPR), e.g., to search for rules,
  ensure that certain rules or commands exist, modify existing rules or
  commands, etc.

- ``amuser/selenium_ability.py``: defines the ``ArchivematicaSeleniumAbility``
  class which implements general browser actions like navigating to a page or
  waiting for DOM elements to appear, or Selenium-specific actions like
  instantiating a driver. All of the classes that involve browser interaction
  sub-class ``ArchivematicaSeleniumAbility``.

- ``amuser/am_api_ability.py``: defines the ``ArchivematicaAPIAbility`` class
  which uses the Python ``requests`` library to make requests to
  Archivematica's API endpoints in order to do things like download AIPs or
  their pointer files. *Note: the functionality implemented in this module
  would be a good candidate for a tool that could make use of an "Archivematica
  Client" Python library, which could be based on this code as well as that
  defined in the `Automation Tools`_ project.*

- ``amuser/am_docker_ability.py``: defines the ``ArchivematicaDockerAbility``
  class which uses Python's ``subprocess`` module to execute the
  ``docker-compose`` or ``docker`` command-line tools in order to do things
  like query the MySQL database directly, determine which containers are
  running, or copy files directly from an Archivematica container. Note that
  the ``docker`` ability implemented by this class assumes that the
  Archivematica instance being tested was deployed locally using Docker Compose
  and the am.git repository; the Acceptance Tests will know whether this is the
  case based on the configuration passed when ``behave`` is called.

- ``amuser/am_mets_ability.py``: defines the ``ArchivematicaMETSAbility`` class
  which defines METS-specific abilities like returning all of the PREMIS events
  defined in a METS file. *Note: This module might make good use of the `METS
  Reader-Writer`_ library.*

- ``amuser/am_ssh_ability.py``: defines the ``ArchivematicaSSHAbility`` class
  which uses the Python ``subprocess`` module to execute ``scp`` commands that,
  for example, copy files or directories from a remote Archivematica instance
  to the machine running the tests.

- ``amuser/constants.py``: this module defines constants that are useful
  throughout the Archivematica User package, e.g., CSS selectors, default
  values like URLs or authentication strings, useful UUIDs, mappings between
  micro-service names and their groups, etc.


.. _configuration:

Configuration
================================================================================

The file at ``features/environment.py`` defines a ``before_scenario`` function
which is a hook that behave_ calls before each scenario is run. Each time this
function is called, it instantiates a new ``ArchivematicaUser`` instance and
passes in parameters to configure that instance. These parameters are
controlled by defaults, unless those defaults are overridden by "behave
userdata", i.e., command-line options of the form ``-D option-name=value``. For
example, to configure the tests to target an Archivematica instance at URL
``http://my-am-instance.org/`` and to use the Firefox web browser instead of
the default Chrome::

    $ behave \
          -D am_url=http://my-am-instance.org/ \
          -D driver_name=Firefox



Troubleshooting and tips
================================================================================


How do I debug very long-running tests?
--------------------------------------------------------------------------------

Sometimes a test runs for several minutes getting Archivematica into a certain
state and performing user actions, e.g., creating an AIP and re-ingesting it,
before making any assertions, e.g., about the contents of the METS file. Then,
if one of those assertions fails because its code contains a bug, it would
appear necessary to run the entire test again in order to debug the new
assertion code. Often there is a simple strategy to avoid this.

1. First, comment out all steps prior to the assertion step in the feature
   file.
2. Then, modify the step function that implements the assertion so that it
   references the AIP or transfer that has already been created in the original
   run of the test. Assuming the original transfer had the name
   ``BagTransfer123`` and the SIP created has UUID
   ``96552612-fdbb-4e91-88db-eeda1e8dd89d``, temporarily adding the following
   two lines to the beginning of the step function will usually suffice::

       context.scenario.transfer_name = 'BagTransfer123'
       context.scenario.sip_uuid = '96552612-fdbb-4e91-88db-eeda1e8dd89d'

3. Finally, re-running ``behave`` should result in just the assertion step
   running on the previously created SIP/AIP.


How do I run the tests of the tests?
--------------------------------------------------------------------------------

The Python code in ``features/steps/`` and ``amuser/`` should adhere to `PEP
8`_. To test this locally, make sure you have tox_ and Pylint_ installed and
then call ``tox`` to run the tests on the tests::

    $ pip install -r requirements/test.txt
    $ tox



.. _`PEP 8`: https://www.python.org/dev/peps/pep-0008/
.. _`tox`: https://tox.readthedocs.io/en/latest/
.. _`Pylint`: https://www.pylint.org/
.. _Archivematica: https://github.com/artefactual/archivematica
.. _behave: http://pythonhosted.org/behave/
.. _Gherkin: https://github.com/cucumber/cucumber/wiki/Gherkin
.. _Selenium: http://www.seleniumhq.org/
.. _Requests: http://docs.python-requests.org/en/master/
.. _TightVNC: http://www.tightvnc.com/vncserver.1.php
.. _`deploy pub`: https://github.com/artefactual/deploy-pub.git
.. _`Archivematica Docker Compose deployment method`: https://github.com/artefactual-labs/am/tree/master/compose
.. _`METS Reader-Writer`: https://github.com/artefactual-labs/mets-reader-writer
.. _`Automation Tools`: https://github.com/artefactual/automation-tools
