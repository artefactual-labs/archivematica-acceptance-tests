# To run::
#     $ behave --tags=uuids-dirs --no-skipped -D driver_name=Firefox -D am_version=1.7
@uuids-dirs @dev
Feature: UUIDs for Directories
  Sometimes Archivematica users want to be able to treat the directories in a
  transfer as intellectual entities. They want to be able to assign identifiers
  (UUIDs) to them and, ultimately, be able to assign persistent identifiers
  (PIDs) to them, such as handles or DOIs.

    Scenario Outline: Lucien wants to create an AIP where each subdirectory of the original transfer is assigned a UUID and this is recorded in the AIP's METS file.
    Given a processing configuration that assigns UUIDs to directories
    And remote directory <directory_path> contains a hierarchy of subfolders containing digital objects
    When a <type> transfer is initiated on directory <directory_path>
    And the user waits for the "Store AIP (review)" decision point to appear during ingest
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
