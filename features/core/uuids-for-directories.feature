# To run this feature file against a Docker-compose deploy of Archivematica (cf.
# https://github.com/artefactual-labs/am/tree/master/compose)::
#
#     $ behave \
#           --tags=uuids-dirs \
#           -D am_url=http://127.0.0.1:62080/ \
#           -D ss_url=http://127.0.0.1:62081/ \
#           -D am_username=test \
#           -D am_password=test \
#           -D ss_username=test \
#           -D ss_password=test \
#           --no-skipped \
#           -D driver_name=Firefox \
#           -D transfer_source_path=archivematica/archivematica-sampledata/TestTransfers/acceptance-tests \
#           -D am_version=1.7 \
#           -D docker_compose_path=/home/jdunham/Development/Archivematica/am/compose/ \
#           -D home=archivematica
#
# Warning: the uuids-for-directories.feature is not idempotent. That is, you
# cannot run it more than once and expect it to pass. This is because it
# involves starting a Zipped Bag type transfer and such transfers cannot be
# given unique names using Archivematica: their names are based on the basename
# of the .zip file used as the transfer source. Therefore, in order to run this
# feature multiple times, you have to close all transfers and ingests (or at
# least the ones named "BagTransfer"). You can do this with the following two
# commands:
#
#     $ ./close_all_transfers.sh \
#           -D am_url=http://127.0.0.1:62080/ \
#           -D ss_url=http://127.0.0.1:62081/ \
#           -D am_username=test \
#           -D am_password=test \
#           -D ss_username=test \
#           -D ss_password=test \
#           -D driver_name=Firefox \
#           -D am_version=1.7
#     $ ./close_all_ingests.sh \
#           -D am_url=http://127.0.0.1:62080/ \
#           -D ss_url=http://127.0.0.1:62081/ \
#           -D am_username=test \
#           -D am_password=test \
#           -D ss_username=test \
#           -D ss_password=test \
#           -D driver_name=Firefox \
#           -D am_version=1.7

@uuids-dirs
Feature: UUIDs for Directories
  Sometimes Archivematica users want to be able to treat the directories in a
  transfer as intellectual entities. They want to be able to assign identifiers
  (UUIDs) to them and, ultimately, be able to assign persistent identifiers
  (PIDs) to them, such as handles or DOIs.

    Scenario Outline: Lucien wants to create an AIP where each subdirectory of the original transfer is assigned a UUID and this is recorded in the AIP's METS file.
    Given a processing configuration that assigns UUIDs to directories
    And remote directory <directory_path> contains a hierarchy of subfolders containing digital objects
    When a <type> transfer is initiated on directory <directory_path>
    And the user waits for the AIP to appear in archival storage
    Then the METS file includes the original directory structure
    And the UUIDs for the subfolders and digital objects are written to the METS file

    Examples: transfer sources
    | type       | directory_path                                                                                 |
    | Standard   | ~/archivematica-sampledata/TestTransfers/acceptance-tests/pid-binding/hierarchy-with-empty-dir |
    | Zipped bag | ~/archivematica-sampledata/SampleTransfers/BagTransfer.zip                                     |

# Possible further tests/ refinements:
# - test with compressed packages, verify that UUIDs can be generated for all
#   directories within one
# - test after SIP arrange
# - confirm sanitization of directory names is working
