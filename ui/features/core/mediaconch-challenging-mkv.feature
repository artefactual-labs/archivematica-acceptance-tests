# How to run this test against a docker-compose deploy (see
# https://github.com/artefactual-labs/am)::
#
#     $ behave \
#           --tags=mediaconch-challenging-mkv \
#           --no-skipped \
#           -v \
#           -D am_version=1.7 \
#           -D am_url=http://127.0.0.1:62080/ \
#           -D am_username=test \
#           -D am_password=test \
#           -D am_api_key=test \
#           -D ss_url=http://127.0.0.1:62081/ \
#           -D ss_username=test \
#           -D ss_password=test \
#           -D ss_api_key=test \
#           -D home=archivematica \
#           -D driver_name=Firefox \
#
@mediaconch-challenging-mkv
Feature: MediaConch validation handles challenging MKV files
  Archivematica users want to be able to validate .mkv derivatives using
  MediaConch even when those files have been known to break validation in
  earlier versions of MediaConch. See
  https://github.com/artefactual/archivematica/issues/966.

  Scenario Outline: Isla wants to confirm that she can use MediaConch to validate an MKV preservation derivative known to have broken MediaConch validation in earlier versions
    Given a processing configuration for MediaConch challenging file testing
    And transfer path <transfer_path> which contains files that, when normalized to MKV, are known to have broken MediaConch v. 16.12 validation checks
    When a transfer is initiated on directory <transfer_path>
    And the user waits for the "Identify file format" micro-service to complete during transfer
    Then the "Identify file format" micro-service output is "Completed successfully" during transfer
    And all original files in the transfer are identified as PRONOM fmt/199 (MPEG-4 Media File)
    When the user waits for the "Validate preservation derivatives" micro-service to complete during ingest
    Then the "Validate preservation derivatives" micro-service output is "Completed successfully" during ingest
    When the user waits for the "Store AIP (review)" decision point to appear during ingest
    Then all PREMIS implementation-check-type validation events have eventOutcome = pass

    Examples: Transfer paths
    | transfer_path                                  |
    | ~/archivematica-sampledata/mc-challenging-file |
