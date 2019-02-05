# Performance Increase Without Output Streams Feature File
# ==============================================================================

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
#     $ behave \
#           --tags=performance-no-stdout \
#           --tags=transfer.name.size-11M-files-10 \
#           --no-skipped \
#           --no-capture \
#           -D driver_name=Firefox \
#           -D am_url=http://127.0.0.1:62080/ \
#           -D am_password=test \
#           -D am_version=1.7 \
#           -D docker_compose_path=/abs/path/to/am/compose \
#           -D home=archivematica
#
# Note the flag ``--tags=transfer.name.size-11M-files-10`` in the above
# command. This tells behave to only run the scenario on the row of the
# ``Examples`` table with name ``size-11M-files-10``. Omit this flag to run all
# example rows or change it to another to run a different row.

# Results
# ==============================================================================
#
# Results against archivematica-sampledata/SampleTransfers/Images (11 MB)
# ------------------------------------------------------------------------------
#
# 1. Total runtime for without output tasks: 412.99 seconds
#    Total runtime for with output tasks:    439.22 seconds
#
# 2. Total runtime for without output tasks: 394.35 seconds
#    Total runtime for with output tasks:    434.23 seconds
#
# 3. Total runtime for without output tasks: 429.57 seconds
#    Total runtime for with output tasks:    444.76 seconds
#
# 4. Total runtime for without output tasks: 111.50 seconds
#    Total runtime for with output tasks:    117.95 seconds
#
# 5. Total runtime for without output tasks: 432.25 seconds
#    Total runtime for with output tasks:    472.20 seconds
#
# Note: run (4) was on a linux host, where docker containers run faster.
#
#
# Analysis
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#
# Average runtime for without output tasks:  337.10 seconds
# Average runtime for with output tasks:     359.04 seconds
# Average time reduction:                      6.11 %


# Results against CUL-Transfer-1 (1.8 GB)
# ------------------------------------------------------------------------------
#
# This transfer contains 9 129 MB .tif files and 9 70 MB .tif files.
#
# 1. Total runtime for without output tasks: 514.10 seconds
#    Total runtime for with output tasks:    553.88 seconds
#
#
# Analysis
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#
# Average runtime for without output tasks:  514.10 seconds
# Average runtime for with output tasks:     535.88 seconds
# Average time reduction:                      7.18 %


# Results against TestTransfers/.../images-17M-each (1.9G)
# ------------------------------------------------------------------------------
#
# This test was run using the modified (and final) version of the feature
# wherein the CAPTURE_CLIENT_SCRIPT_OUTPUT flag causes stderr to be passed from
# the gearman worker to the gearman task manager if, and only if, the exit code
# of the task was non-zero.
#
# This transfer contains 113 17M .tif files for a total size of 1.9G.
#
# 1. Total runtime for without output tasks: 1,757.50 seconds
#    Total runtime for with output tasks:    1,905.62 seconds
#
# Analysis
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#
# Average time reduction:                        7.77 %

@performance-no-stdout @developer
Feature: Performance increase: stop saving stdout/stderr
  Archivematica's developers want to test whether preventing client scripts
  from sending their stdout and stderr to MCPServer to be saved to the database
  will result in a significant performance increase.

  @transfer.name.<name>
  Scenario Outline: Joel creates an AIP on an Archivematica instance that saves stdout/err and on one that does not. He expects that the processing time of the AIP on the first instance will be less than that of the AIP on the second one.
    Given an Archivematica instance that passes client script output streams to MCPServer
    And the default processing config is set to automate a transfer through to "Store AIP"

    When a transfer is initiated on directory <transfer_source>
    And the user waits for the "Store AIP (review)" decision point to appear during ingest
    And performance statistics are saved to with_outputs_stats

    Then performance statistics show output streams are saved to the database

    When the user alters the Archivematica instance to not pass client script output streams to MCPServer
    And a transfer is initiated on directory <transfer_source>
    And the user waits for the "Store AIP (review)" decision point to appear during ingest
    And performance statistics are saved to without_outputs_stats

    Then performance statistics show output streams are not saved to the database
    And the runtime of client scripts in without_outputs_stats is less than the runtime of client scripts in with_outputs_stats
    # Note: this will currently fail because ceasing to pass client script
    # output streams to MCPServer has no effect on what is written to the METS
    # file.
    # And the size of the without_outputs_stats METS file is less than that of the with_outputs_stats METS file

    Examples: Archivematica transfer sources
    | name                | transfer_source                                                                       |
    | size-4K-files-1     | ~/archivematica-sampledata/TestTransfers/small                                        |
    | size-11M-files-10   | ~/archivematica-sampledata/SampleTransfers/Images                                     |
    | size-1.9G-files-113 | ~/archivematica-sampledata/TestTransfers/acceptance-tests/performance/images-17M-each |
    | size-11G-files-669  | ~/archivematica-sampledata/TestTransfers/acceptance-tests/performance/video-14M-each  |

    # Listed below are possible metrics of performance increase. Those checked
    # off are relatively easy to measure and are described in the scenario
    # above. Those not checked off need further work in order to determine how
    # they can be measured in this scenario or others.
    #
    # - [√] decrease in total processing time (debatable)
    # - [√] decrease in size of the AIP METS file and AIP Pointer file
    # - [√] decrease in database usage (significant decrease in total bytes written to db)
    # - [√] decrease in total size of database
    # - [ ] increase in number of files processed simultaneously (questionable)
    # - [ ] increase in size of the largest file that can be processed (questionable)
    # - [ ] increase in the total number of files that can be included in a single aip
    # - [ ] decrease in amount of memory required to process the same content
