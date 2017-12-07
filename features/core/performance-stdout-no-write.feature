# Performance Increase Without Output Streams Feature File
# ==============================================================================
#
# Warning: this feature file should only be run in development. It requires a
# docker-compose-based Archivematica deploy. The test itself must be able to
# alter the deployment, i.e., check the source code out to a new revision and
# # restart Archivematica. This feature was developed against an AM deploy
# created using https://github.com/artefactual-labs/am and Archivematica at
# branch dev/1.8.x (be8fdee61851e180cd4dbab0af54fad3f5766066). The test itself
# checks out a locally accessible dev/1.8.x-without-logs branch at the hash
# provided under `commit_without_outputs` below and restarts Archivematica using
# docker-compose.
#
# To run the test, deploy Archivematica locally using 
# https://github.com/artefactual-labs/am::
#
#     $ git clone https://github.com/artefactual-labs/am
#     $ cd am/compose
#     $ git submodule update --init --recursive
#     $ cd ../src/archivematica
#     $ git checkout be8fdee61851e180cd4dbab0af54fad3f5766066
#     $ cd ../../compose
#     $ make create-volumes
#     $ docker-compose up -d --build
#     $ make bootstrap
#     $ make restart-am-services
#
# Then run the following `behave` command, after replacing the
# `docker_compose_path` and `am_src_path` userdata options with the appropriate
# values for your development system::
#
#     behave \
#         --tags=performance-no-stdout \
#         --no-skipped \
#         --no-capture \
#         -D driver_name=Firefox \
#         -D am_url=http://127.0.0.1:62080/ \
#         -D am_password=test \
#         -D home="" \
#         -D am_version=1.7 \
#         -D docker_compose_path=/abs/path/to/am/compose \
#         -D am_src_path=/abs/path/to/am/src/archivematica
#

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
# Average runtime for without output tasks: 514.10 seconds
# Average runtime for with output tasks:    535.88 seconds
# Average time reduction:                     7.18 %


@performance-no-stdout @developer
Feature: Performance increase: stop saving stdout/stderr
  Archivematica's developers want to test whether preventing client scripts
  from sending their stdout and stderr to MCPServer to be saved to the database
  will result in a significant performance increase.

  Scenario Outline: Joel creates an AIP on an Archivematica instance that saves stdout/err and on one that does not. He expects that the processing time of the AIP on the first instance will be less than that of the AIP on the second one.
    Given an Archivematica instance at <commit_with_outputs> that passes client script output streams to MCPServer
    And the default processing config is set to automate a transfer through to "Store AIP"

    When a transfer is initiated on directory <transfer_source>
    And the user waits for the "Store AIP (review)" decision point to appear during ingest
    And performance statistics are saved to with_outputs_stats.json

    Then performance statistics at with_outputs_stats.json show output streams are saved to the database

    When the user switches to using an Archivematica instance at commit <commit_without_outputs> that does not pass client script output streams to MCPServer

    Given the default processing config is set to automate a transfer through to "Store AIP"

    When a transfer is initiated on directory <transfer_source>
    And the user waits for the "Store AIP (review)" decision point to appear during ingest
    And performance statistics are saved to without_outputs_stats.json

    Then performance statistics at without_outputs_stats.json show output streams are not saved to the database
    And the runtime of client scripts in without_outputs_stats.json is less than the runtime of client scripts in with_outputs_stats.json
    And there is no stdout or stderr for the client scripts in without_outputs_stats.json
    And there is non-zero stdout and stderr for the client scripts in with_outputs_stats.json

    When the user switches to using an Archivematica instance at commit <commit_with_outputs> that does pass client script output streams to MCPServer

    Examples: Archivematica git hashes and transfer sources
    | transfer_source                                   | commit_with_outputs                      | commit_without_outputs                   |
    | ~/small                                           | c1a144ea9eb2dd2858a6deb583d32d5a97eb4b30 | 0b3ee00ec9cdce1ad3d3777768666edee4ef9d03 |
    #| ~/archivematica-sampledata/SampleTransfers/Images | c1a144ea9eb2dd2858a6deb583d32d5a97eb4b30 | 0b3ee00ec9cdce1ad3d3777768666edee4ef9d03 |
    #| ~/images-100M-each-2G-total                       | c1a144ea9eb2dd2858a6deb583d32d5a97eb4b30 | 0b3ee00ec9cdce1ad3d3777768666edee4ef9d03 |
    #| ~/video-500M-each-10G-total                       | c1a144ea9eb2dd2858a6deb583d32d5a97eb4b30 | 0b3ee00ec9cdce1ad3d3777768666edee4ef9d03 |

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