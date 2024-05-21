# To run this feature against a Docker Compose-based Archivematica deploy::
#
#     $ behave --tags=man-norm \
#           --no-skipped \
#           -D am_username=test \
#           -D am_password=test \
#           -D am_url=http://127.0.0.1:62080/ \
#           -D am_version=1.7 \
#           -D am_api_key=test \
#           -D ss_username=test \
#           -D ss_password=test \
#           -D ss_url=http://127.0.0.1:62081/ \
#           -D ss_api_key=test \
#           -D home=archivematica \
#           -D driver_name=Firefox \

@man-norm
Feature: Archivematica recognizes manually normalized files
  Archivematica users want to be able to manually normalize their own files and
  make sure that Archivematica correctly recognizes and documents the
  relationship betweeen the originals and the manually normalized files.

  Scenario Outline: Isla wants to create an AIP from a transfer containing manually normalized files, some of which have paths that are prefixes of other manually normalized files.
    Given a processing configuration for testing manual normalization
    And transfer source <transfer_path> which contains a manually normalized file whose path is a prefix of another manually normalized file
    When a transfer is initiated on directory <transfer_path>
    And the user waits for the "Normalize for preservation" micro-service to complete during ingest
    Then the "Normalize for preservation" micro-service output is "Completed successfully" during ingest
    And all preservation tasks recognize the manually normalized derivatives
    When the user waits for the "Relate manual normalized preservation files to the original files" micro-service to complete during ingest
    Then the "Relate manual normalized preservation files to the original files" micro-service output is "Completed successfully" during ingest
    And each manually normalized file is matched to an original
    When the user waits for the "Generate METS.xml document|Generate AIP METS" micro-service to complete during ingest
    Then the "Generate METS.xml document|Generate AIP METS" micro-service output is "Completed successfully" during ingest

    Examples: Transfer paths
    | transfer_path                                       |
    | TestTransfers/acceptance-tests/manual-normalization |
    | TestTransfers/manualNormalization                   |
