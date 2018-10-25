# Compare Branches Feature File
# =============================

# Warning: this feature file should only be run in development. It requires a
# docker-compose-based Archivematica deploy. The test itself must be able to
# alter the deployment by changing an environment variable and recreating a
# docker container.
#
# To run the test, deploy Archivematica locally using
# https://github.com/artefactual-labs/am::
#
#     $ git clone https://github.com/artefactual-labs/am
#     $ cd am/compose
#     $ git submodule update --init --recursive
#     $ make create-volumes
#     $ docker-compose up -d --build
#     $ make bootstrap
#     $ make restart-am-services
#
# Then run the following ``behave`` command, after replacing the
# ``docker_compose_path`` userdata option with the appropriate value for your
# development system::
#
# behave \
#         --tags=performance-compare-branches \
#         --tags=transfer.name.size-11M-files-10 \
#         --no-skipped \
#         --no-logcapture \
#         -D driver_name=Firefox \
#         -D am_url=http://127.0.0.1:62080/ \
#         -D am_password=test \
#         -D am_version=1.7 \
#         -D docker_compose_path=/abs/path/to/am/compose \
#         -D home=archivematica \
#         -D version_a=archivematica:branch-a \
#         -D version_b=archivematica:branch-b \
#         -D max_check_transfer_appeared_attempts=7200
#

# The ``version_a`` and ``version_b`` flags control which source
# versions will be checked out for each run.  You can specify more
# than one project here by separating them with commas.  For example:
#
#     -D version_a=archivematica:somebranch,archivematica-storage-service:anotherbranch
#
# Will set things running with particular versions for archivematica
# and the storage service.
#
#
# Note the flag ``--tags=transfer.name.size-11M-files-10`` in the above
# command. This tells behave to only run the scenario on the row of the
# ``Examples`` table with name ``size-11M-files-10``. Omit this flag to run all
# example rows or change it to another to run a different row.

@performance-compare-branches @developer
Feature: Compare ingest/transfer performance across branches
  Archivematica's developers want to test whether one branch completes
  ingests/transfer more quickly than another

  @transfer.name.<name>
  Scenario Outline: Two branches enter.  One branch leaves.
    Given an Archivematica instance running version_a
    And the default processing config is set to automate a transfer through to "Store AIP"

    When a transfer is initiated on directory <transfer_source>
    And the user waits for the "Store AIP (review)" decision point to appear during ingest
    And performance statistics are saved to version_a_stats

    when the user alters the Archivematica instance to run version_b

    When a transfer is initiated on directory <transfer_source>
    And the user waits for the "Store AIP (review)" decision point to appear during ingest
    And performance statistics are saved to version_b_stats

    And the difference in runtime between version_a_stats and version_b_stats is printed

    Examples: Archivematica transfer sources
    | name                | transfer_source                                                                       |
    | size-4K-files-1     | ~/archivematica-sampledata/TestTransfers/small                                        |
    | size-11M-files-10   | ~/archivematica-sampledata/SampleTransfers/Images                                     |
    | size-1.9G-files-113 | ~/archivematica-sampledata/TestTransfers/acceptance-tests/performance/images-17M-each |
    | size-11G-files-669  | ~/archivematica-sampledata/TestTransfers/acceptance-tests/performance/video-14M-each  |

