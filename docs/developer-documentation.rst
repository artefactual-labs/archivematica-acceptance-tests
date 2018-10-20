================================================================================
  Developer Documentation: Archivematica Automated User Acceptance Tests
================================================================================

This document provides developer documentation for the Archivematica Automated
User Acceptance Tests (AMAUAT). This is technical documentation for those
seeking to understand how these tests work and how to contribute to them.

The Archivematica Automated User Acceptance Tests are high-level tests of the
Archivematica application. The tests use the `Selenium WebDriver`_ to control a
web-browser to do Archivematica set-up, perform user actions, and make
assertions about the system's expected and desired behaviour. Behaviours are
specified in human-readable Gherkin *feature* files.

Gaining a thorough understanding of the tests requires understanding these three
layers:

1. `Feature files`_: these are human-readable test specifications (see
   `features/core/ <../features/core/>`_).
2. `Step files`_: these are Python implementations of the steps used in the
   feature files (see `features/steps/ <../features/steps/>`_).
3. The ``ArchivematicaUser`` class in the `Archivematica User package`_: this
   class has the ability to interact with Archivematica via its browser-based
   GUIs and its APIs.

The following three sections describe each of these layers in more detail. The
`Configuration`_ section describes how arguments are passed to the ``behave``
CLI to configure how the tests are executed. Finally, the `Troubleshooting and
tips`_ section provides suggestions and help for writing and debugging features
and their implementations.


Feature files
================================================================================

What are feature files?
--------------------------------------------------------------------------------

Feature files describe features of Archivematica.

    A feature is a unit of functionality of a software system that satisfies a
    requirement, represents a design decision, and provides a potential
    configuration option ([APEL-2009]_).

Each feature file defines a ``Feature`` by declaring one or more scenarios.
A ``Scenario`` represents a user performing a sequence of actions on an
Archivematica instance and expecting certain results. If a ``Scenario`` is a
``Scenario Outline``, then it will contain an ``Examples`` table and it will
run once for each configuration row in that table.

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
made between user actions. Thus the implicit grammar for an AMAUAT scenario is::

    Given+ (When+ Then+)+

For more information on how to write Gherkin, see this Gherkin_ page and this
Behave_ page.


How to create new feature files
--------------------------------------------------------------------------------

New feature files should have the following properties.

1. **Names.** Feature file names have the ``.feature`` extension and are
   lowercase with hyphens used to separate words, e.g.,
   ``fpr-configuration.feature``.

2. **Location.** Feature files are stored in a subdirectory of the
   `features/ <../features/>`_ directory, typically in
   `features/core/ <../features/core/>`_.

   - Feature files in ``features/core/`` describe core features of
     Archivematica; these features should run successfully against stable
     Archivematica releases.
   - Files that describe client or project-specific features may be placed in
     an appropriately named subdirectory of ``features/``, e.g.,
     ``features/CCA/``.

3. **Tags.** Tags are labels that can be applied to features and scenarios. They
   allow for the classification of features and scenarios. This classification
   allows users to control which features are executed when they run the
   ``behave`` command.

   - While they are technically optional from ``behave``'s point of view, each
     ``Feature`` in each feature file should contain a unique tag that
     succinctly identifies that feature, e.g., ``@aip-encrypt``, thereby
     allowing a user to run just that feature with ``behave
     --tags=aip-encrypt``.
   - Each ``Scenario`` or ``Scenario Outline`` should contain a descriptive tag
     that is at least unique within its ``Feature``, e.g., ``@compressed``;
     this allows a user to run just that scenario, e.g., with ``behave
     --tags=aip-encrypt --tags=compressed``.
   - Features and scenarios may contain more than one tag.
   - Tags are prefixed by the ``@`` character in feature files. When they are
     passed as arguments to ``behave``, the ``@`` character is optional, e.g.,
     ``--tags=wip`` and ``--tags=@wip`` are equivalent. Note that ``behave``
     tags are completely distinct from Python's decorator syntax, which is
     superficially similar in that it too uses the ``@`` character as a prefix.
   - The ``@wip`` and ``@non-executable`` tags have special meaning.

     - ``@wip`` is used to indicate a work-in-progress and signifies that
       the feature is not yet expected to execute successfully.
     - ``@non-executable`` is used to indicate that a feature or scenario is
       documentary in nature and should not be expected to execute successfully,
       i.e., pass.

4. **Syntax.** Feature files should be written following the formatting
   conventions exemplified in the extant feature files. Spaces, not tabs,
   should be used for indentation. Instead of providing a detailed
   specification, the following example of a truncated PID (Persistent
   Identifier) binding feature should suffice as a guide to formatting::

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

5. **Documentation.** Comments in Gherkin feature files are lines of text preceded
   by the ``#`` character.

   - Each feature file should contain a comment indicating how it should be
     run, including any special arguments that must be passed to ``behave``.
     Best practice is to include a full ``behave`` command, including flags, as
     well as details of the type of Archivematica deploy(s) that the behave
     command was successfully run against.

6. **Existing steps.** Whenever possible, new feature files should use existing
   step definitions. All existing steps are defined in Python modules under
   `features/steps/ <../features/steps/>`_. To view a list of all existing
   steps, use ``behave`` to view the steps catalog::

       $ behave --steps-catalog


Step files
================================================================================

What are step files?
--------------------------------------------------------------------------------

Step files are Python modules defined under
`features/steps/ <../features/steps/>`_. The steps used in scenarios are
implemented as step functions. For example, the following ``Given`` step may
appear in any scenario of any feature file::

    Given the default processing config is in its default state

and its implementation is provided by a particular Python function in
`features/steps/steps.py <../features/steps/steps.py>`_::

    @given('the default processing config is in its default state')
    def step_impl(context):
        ...

A ``behave`` step function is a Python function named ``step_impl`` which is
decorated with one of ``@given``, ``@when``, and ``@then``. The decorator used
must match the initial keyword of the step. That is, a ``Given``-type step
needs a ``@given()``-decorated function, a ``When``-type step needs
``@when()``, and a ``Then``-type step needs ``@then()``.

The string argument passed to the decorator must *exactly* match the text of
the corresponding step (ignoring the ``Given/When/Then`` keyword), as
illustrated in the above two examples. The only exception to this is when the
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
Behave supplies the context object as well as `several other objects`_ as
attributes of ``context``, e.g., ``context.feature`` and ``context.scenario``.
You can assign arbitrary values to any of these objects. The ``context`` object
persists across all features and scenarios that are run as a result of
executing the ``behave`` command. The ``context.feature`` object will be
re-initialized for each new feature that is run. Similarly, the
``context.scenario`` object will be re-initialized for each new scenario.

In order to preserve state across the steps within a given scenario, the step
functions of the AMAUAT tend to set attributes on the ``context.scenario``
object. For example, one step may download an AIP from Archivematica and save
the path to the downloaded AIP as ``context.scenario.aip_path``. Then a
subsequent step can access the value of ``context.scenario.aip_path`` in order
to decompress the AIP or inspect its METS file.


How to create new steps
--------------------------------------------------------------------------------

If you need to create a step in a feature file that is not yet implemented as a
step function, then you will need to define a decorated step function for it,
as described above.

The `features/steps/steps.py <../features/steps/steps.py>`_ module is for
general-purpose steps. If a step is being used by more than one feature file,
it should be defined here. If this module becomes too large, it may be broken
up into multiple logically coherent modules.

Functions that do not implement steps (but which are called by step functions)
should be defined in `features/steps/utils.py <../features/steps/utils.py>`_ and
imported into the step modules as needed.

Step implementations that are specific to a particular feature file should be
defined in a sensibly named module in `features/steps/ <../features/steps/>`_.
For example, step functions particular to the
`aip-encryption.feature <../features/core/aip-encryption.feature>`_
feature file are defined in
`features/steps/aip_encryption_steps.py <../features/steps/aip_encryption_steps.py>`_.

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



Archivematica User package
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
downloads the AIP`` (in `steps.py <../features/steps/steps.py>`_) the AIP is
downloaded by using the Archivematica User's API ability and calling
``context.am_user.api.download_aip(...)``.

The ``ArchivematicaUser`` class and its abilities are structured using
composition and inheritance. The itemization below provides an overview of the
code structure as a guide for implementing new abilities or debugging existing
ones.

- `amuser/amuser.py <../amuser/amuser.py>`_: defines the ``ArchivematicaUser``
  class (which inherits from `amuser/base.py::Base <../amuser/base.py>`_) with
  the following instance attributes representing abilities:

  - ``.browser``: the browser ability that uses Selenium to interact with
    Archivematica via its web interfaces.
  - ``.ssh``: the SSH ability that spawns subprocesses to make ``scp`` or
    ``ssh`` calls.
  - ``.docker``: the docker ability that spawns subprocesses to make calls to
    ``docker`` or ``docker-compose``.
  - ``.localfs``: the localfs ability that makes posible to retrieve files
    when ``docker cp`` or ``scp`` are not available, e.g. when ``behave`` can
    be executed in the same machine where Archivematica is installed or inside
    a container with access to the needed assets like it is done in the
    Archivematica development environment based in Docker Compose.
  - ``.api``: the API ability that uses Python's Requests library to make API
    requests to Archivematica endpoints.
  - ``.mets``: the METS ability that can parse Archivematica METS files and
    make assertions about them.

- `amuser/base.py <../amuser/base.py>`_: defines the ``Base`` class, which is a
  super-class of ``ArchivematicaUser`` as well as of all of the ability
  classes, e.g., the ``ArchivematicaSeleniumAbility`` class that implements the
  browser ability.  The ``Base`` class does the following:

  - Initializes all of the URL getters as configured in
    `amuser/urls.py <../amuser/urls.py>`_. For example, ``Base`` uses the tuple
    ``('get_ingest_url', '{}ingest/')`` from ``urls.py`` to give all of its
    sub-class instances the ability to call ``self.get_ingest_url()`` in order
    to get the URL of the Ingest tab.

- `amuser/utils.py <../amuser/utils.py>`_: contains general-purpose functions
  used by various Archivematica User classes.

- `amuser/am_browser_ability.py <../amuser/am_browser_ability>`_: defines the
  ``ArchivematicaBrowserAbility`` class, which implements the ability to use a
  browser to interact with Archivematica; i.e., ``am_user.browser`` is an
  instance of ``ArchivematicaBrowserAbility``.

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

- `amuser/am_browser_auth_ability.py <../amuser/am_browser_auth_ability>`_:
  defines the ``ArchivematicaBrowserAuthenticationAbility`` which can login to
  an Archivematica instance or a Storage Service instance.

- `amuser/am_browser_transfer_ingest_ability.py <../amuser/am_browser_transfer_ingest_ability.py>`_:
  defines the ``ArchivematicaBrowserTransferIngestAbility`` class which defines
  abilities that are common to the Transfer and Ingest tabs, e.g., waiting for a
  micro-service to appear, or making a choice at a particular decision point.

  - Has these super-classes:

    - ``ArchivematicaBrowserJobsTasksAbility``
    - ``ArchivematicaBrowserFileExplorerAbility``
    - ``ArchivematicaBrowserTransferAbility``
    - ``ArchivematicaBrowserIngestAbility)``

- `amuser/am_browser_jobs_tasks_ability.py <../amuser/am_browser_jobs_tasks_ability.py>`_:
  defines the ``ArchivematicaBrowserJobsTasksAbility`` class which defines
  abilities related to interacting with Jobs and Tasks via the GUI, e.g.,
  getting the output of a job (e.g., ``Completed successfully``) or parsing all
  of the tasks of a job into a Python dict.

- `amuser/am_browser_file_explorer_ability.py <../amuser/am_browser_file_explorer_ability.py>`_:
  defines the ``ArchivematicaBrowserFileExplorerAbility`` class which defines
  abilities related to interacting with Archivematica's file explorer GUIs,
  e.g., for selecting a transfer source directory.

- `amuser/am_browser_transfer_ability.py <../amuser/am_browser_transfer_ability.py>`_:
  defines the ``ArchivematicaBrowserTransferAbility`` class which defines
  abilities specific to interacting with the Transfer tab, e.g., starting and
  approving a transfer.

- `amuser/am_browser_ingest_ability.py <../amuser/am_browser_ingest_ability.py>`_:
  defines the ``ArchivematicaBrowserIngestAbility`` class which defines
  abilities specific to interacting with the Ingest tab, e.g., getting a SIP
  UUID given the name of the corresponding transfer, adding metadata to an AIP,
  or parsing the normalization report.

- `amuser/am_browser_ss_ability.py <../amuser/am_browser_ss_ability.py>`_:
  defines the ``ArchivematicaBrowserStorageServiceAbility`` class for
  interacting with the Storage Service GUI, e.g., approving AIP deletion
  requests, searching for an AIP, or viewing and mutating spaces and locations.

- `amuser/am_browser_preservation_planning_ability.py <../amuser/am_browser_preservation_planning_ability.py>`_:
  defines the ``ArchivematicaBrowserPreservationPlanningAbility`` class for
  interacting with Archivematica's Format Policy Registry (FPR), e.g., to
  search for rules, ensure that certain rules or commands exist, modify
  existing rules or commands, etc.

- `amuser/selenium_ability.py <../amuser/selenium_ability.py>`_: defines the
  ``ArchivematicaSeleniumAbility`` class which implements general browser
  actions like navigating to a page or waiting for DOM elements to appear, or
  Selenium-specific actions like instantiating a driver. All of the classes
  that involve browser interaction sub-class ``ArchivematicaSeleniumAbility``.

- `amuser/am_api_ability.py <../amuser/am_api_ability.py>`_: defines the
  ``ArchivematicaAPIAbility`` class which uses the Python ``requests`` library
  to make requests to Archivematica's API endpoints in order to do things like
  download AIPs or their pointer files. *Note: the functionality implemented in
  this module would be a good candidate for a tool that could make use of an
  "Archivematica Client" Python library, which could be based on this code as
  well as that defined in the* `Automation Tools`_ *project.*

- `amuser/am_docker_ability.py <../amuser/am_docker_ability.py>`_: defines the
  ``ArchivematicaDockerAbility`` class which uses Python's ``subprocess``
  module to execute the ``docker-compose`` or ``docker`` command-line tools in
  order to do things like query the MySQL database directly, determine which
  containers are running, or copy files directly from an Archivematica
  container. Note that the ``docker`` ability implemented by this class assumes
  that the Archivematica instance being tested was deployed locally using
  Docker Compose and the am.git repository; the Acceptance Tests will know
  whether this is the case based on the configuration passed when ``behave`` is
  called.

- `amuser/am_mets_ability.py <../amuser/am_mets_ability.py>`_: defines the
  ``ArchivematicaMETSAbility`` class which defines METS-specific abilities like
  returning all of the PREMIS events defined in a METS file. *Note: This module
  might make good use of the* `METS Reader-Writer`_ *library.*

- `amuser/am_ssh_ability.py <../amuser/am_ssh_ability.py>`_: defines the
  ``ArchivematicaSSHAbility`` class which uses the Python ``subprocess`` module
  to execute ``scp`` commands that, for example, copy files or directories from
  a remote Archivematica instance to the machine running the tests.

- `amuser/constants.py <../amuser/constants.py>`_: this module defines constants
  that are useful throughout the Archivematica User package, e.g., CSS
  selectors, default values like URLs or authentication strings, useful UUIDs,
  mappings between micro-service names and their groups, etc.


.. _configuration:

Configuration
================================================================================

The Python module `features/environment.py <../features/environment.py>`_
defines a ``before_scenario`` function which is a hook that Behave_ calls
before each scenario is run. Each time this function is called, it instantiates
a new ``ArchivematicaUser`` instance and passes in parameters to configure that
instance. These parameters are controlled by defaults, unless those defaults
are overridden by "behave userdata", i.e., command-line options of the form
``-D option-name=value``. For example, to configure the tests to target an
Archivematica instance at URL ``http://my-am-instance.org/`` and to use the
Firefox web browser instead of the default Chrome::

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


How long does it take to run the tests?
--------------------------------------------------------------------------------

The time required to run the AMUAT tests depends on how many and which tests
are being run, as well as the resources behind the Archivematica instance being
tested. A very approximate rule of thumb is 5 minutes for each run of each
scenario.

`This issue`_ documents the commands used to run all of the tests expected to
pass against Archivematica version 1.7. The total runtime of all of the tests
documented there was approximately 1.5 hours.


How are the tests run in practice?
--------------------------------------------------------------------------------

The AMUAT tests have *not* yet been formally incorporated into Archivematica's
manual or automated release processes. However, we are working on a Continuous
Integration (CI) system that will run the relevant tests based on
appropriate triggers.

In the 1.7 release, we manually ran all of the relevant tests against the final
release candidate and confirmed that they passed. The tags flag used was::

    --tags=mo-aip-reingest,icc,ipc,tpc,picc,uuids-dirs,premis-events,pid-binding,aip-encrypt-mirror,aip-encrypt

which corresponds to running all of the following feature files:

- mo-aip-reingest = `metadata-only-aip-reingest.feature <../features/core/metadata-only-aip-reingest.feature>`_
- icc = `ingest-mkv-conformance.feature <../features/core/ingest-mkv-conformance.feature>`_
- ipc = `ingest-policy-check.feature <../features/core/ingest-policy-check.feature>`_
- tpc = `transfer-policy-check.feature <../features/core/transfer-policy-check.feature>`_
- picc = `transfer-mkv-conformance.feature <../features/core/transfer-mkv-conformance.feature>`_
- uuids-dirs = `uuids-for-directories.feature <../features/core/uuids-for-directories.feature>`_
- premis-events = `premis-events.feature <../features/core/premis-events.feature>`_
- pid-binding = `pid-binding.feature <../features/core/pid-binding.feature>`_
- aip-encrypt-mirror = `aip-encryption-mirror.feature <../features/core/aip-encryption-mirror.feature>`_
- aip-encrypt = `aip-encryption.feature <../features/core/aip-encryption.feature>`_

In future releases we will continue to run these tests in order to prevent
regressions and confirm the correct functioning of new features. Exactly how
that happens will be documented in more detail here as our Continuous
Integration and Continuous Delivery (CI/CD) processes mature.



.. _`This issue`: https://github.com/artefactual/archivematica/issues/942
.. _`PEP 8`: https://www.python.org/dev/peps/pep-0008/
.. _`tox`: https://tox.readthedocs.io/en/latest/
.. _`Pylint`: https://www.pylint.org/
.. _Archivematica: https://github.com/artefactual/archivematica
.. _Behave: http://behave.readthedocs.io/en/latest/
.. _Gherkin: https://github.com/cucumber/cucumber/wiki/Gherkin
.. _`Selenium WebDriver`: https://www.seleniumhq.org/projects/webdriver/
.. _Requests: http://docs.python-requests.org/en/master/
.. _TightVNC: http://www.tightvnc.com/vncserver.1.php
.. _`deploy pub`: https://github.com/artefactual/deploy-pub.git
.. _`Archivematica Docker Compose deployment method`: https://github.com/artefactual-labs/am/tree/master/compose
.. _`METS Reader-Writer`: https://github.com/artefactual-labs/mets-reader-writer
.. _`Automation Tools`: https://github.com/artefactual/automation-tools
.. _`several other objects`: http://behave.readthedocs.io/en/latest/api.html#detecting-that-user-code-overwrites-behave-context-attributes

.. [APEL-2009] Sven Apel and Christian Kästner 2009. An Overview of Feature-Oriented Software Development (http://www.jot.fm/issues/issue_2009_07/column5/)
