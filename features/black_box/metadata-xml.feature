@metadata-xml
Feature: Roco wants to ensure that metadata XML files are validated and recorded in the AIP METS

Background: The MCPClient service has been configured to validate metadata XML files and the storage service has a transfer source location with sample transfers that contain source-metadata.csv files that can be used to test ingest, reingest and indexing of AIPs.

  Scenario: Initial ingest
    Given a "unzipped bag" transfer type located in "SampleTransfers/MetadataXMLValidation/small_initial_ingest"
    When the AIP is downloaded
    Then the "Generate METS.xml document" ingest job completes successfully
    And every metadata XML file in source-metadata.csv that has been validated has a PREMIS event with metadata validation details and pass outcome
    And every metadata XML file in source-metadata.csv has a dmdSec with STATUS "original" that has a mdWrap with the specified OTHERMDTYPE which wraps the XML content
    And the AIP can be found in the Archival storage tab by searching the contents of its latest metadata files

  Scenario: Update
    Given a "unzipped bag" transfer type located in "SampleTransfers/MetadataXMLValidation/small_initial_ingest"
    And a processing configuration for metadata only reingests
    When the AIP is downloaded
    And a "METADATA" reingest is started using the "default" processing configuration
    And the "SampleTransfers/MetadataXMLValidation/small_mdupdate_update-only/data/metadata/slub-rights.xml" metadata file is added
    And the "SampleTransfers/MetadataXMLValidation/small_mdupdate_update-only/data/metadata/mods.xml" metadata file is added
    And the "SampleTransfers/MetadataXMLValidation/small_mdupdate_update-only/data/metadata/lido.xml" metadata file is added
    And the "SampleTransfers/MetadataXMLValidation/small_mdupdate_update-only/data/metadata/dc.xml" metadata file is added
    And the "SampleTransfers/MetadataXMLValidation/small_mdupdate_update-only/data/metadata/marc21.xml" metadata file is added
    And the "SampleTransfers/MetadataXMLValidation/small_mdupdate_update-only/data/metadata/metadata.txt.xml" metadata file is added
    And the "SampleTransfers/MetadataXMLValidation/small_mdupdate_update-only/data/metadata/bag-info.xml" metadata file is added
    And the "SampleTransfers/MetadataXMLValidation/small_mdupdate_update-only/data/metadata/source-metadata.csv" metadata file is added
    And the "SampleTransfers/MetadataXMLValidation/small_mdupdate_update-only/data/metadata/custom_dir/" metadata file is added
    And the reingest is approved
    And the reingest has been processed
    Then the "Generate METS.xml document" ingest job completes successfully
    And every metadata XML file in source-metadata.csv that has been validated has a PREMIS event with metadata validation details and pass outcome
    And every existing metadata XML file in the reingested source-metadata.csv has two dmdSecs with the same GROUPID, one with the original XML content which has been superseded by a new one that contains the updated XML content
    And every new metadata XML file in the reingested source-metadata.csv has a dmdSec with STATUS "update" that has a mdWrap with the specified OTHERMDTYPE which wraps the XML content
    And the AIP can be found in the Archival storage tab by searching the contents of its latest metadata files

  Scenario: Addition
    Given a "unzipped bag" transfer type located in "SampleTransfers/MetadataXMLValidation/small_initial_ingest"
    And a processing configuration for metadata only reingests
    When the AIP is downloaded
    And a "METADATA" reingest is started using the "default" processing configuration
    And the "SampleTransfers/MetadataXMLValidation/small_mdupdate_addition-only-1/data/metadata/source-metadata.csv" metadata file is added
    And the "SampleTransfers/MetadataXMLValidation/small_mdupdate_addition-only-1/data/metadata/custom_dir/" metadata file is added
    And the reingest is approved
    And the reingest has been processed
    Then the "Generate METS.xml document" ingest job completes successfully
    And every metadata XML file in source-metadata.csv that has been validated has a PREMIS event with metadata validation details and pass outcome
    And every metadata XML file in source-metadata.csv has a dmdSec with STATUS "update" that has a mdWrap with the specified OTHERMDTYPE which wraps the XML content
    And the AIP can be found in the Archival storage tab by searching the contents of its latest metadata files

  Scenario: Deletion
    Given a "unzipped bag" transfer type located in "SampleTransfers/MetadataXMLValidation/small_initial_ingest"
    And a processing configuration for metadata only reingests
    When the AIP is downloaded
    And a "METADATA" reingest is started using the "default" processing configuration
    And the "SampleTransfers/MetadataXMLValidation/small_mdupdate_deletion-only/data/metadata/source-metadata.csv" metadata file is added
    And the reingest is approved
    And the reingest has been processed
    Then the "Generate METS.xml document" ingest job completes successfully
    And every deleted metadata XML file in the reingested source-metadata.csv has a dmdSec with STATUS "deleted" that has a mdWrap with the specified OTHERMDTYPE which wraps the original XML content
    And the AIP can not be found in the Archival storage tab by searching the original contents of the deleted metadata files

  Scenario: All-in-one
    Given a "unzipped bag" transfer type located in "SampleTransfers/MetadataXMLValidation/small_initial_ingest"
    And a processing configuration for metadata only reingests
    When the AIP is downloaded
    And a "METADATA" reingest is started using the "default" processing configuration
    And the "SampleTransfers/MetadataXMLValidation/small_mdupdate_all-in-one/data/metadata/slub-rights.xml" metadata file is added
    And the "SampleTransfers/MetadataXMLValidation/small_mdupdate_all-in-one/data/metadata/mods.xml" metadata file is added
    And the "SampleTransfers/MetadataXMLValidation/small_mdupdate_all-in-one/data/metadata/lido.xml" metadata file is added
    And the "SampleTransfers/MetadataXMLValidation/small_mdupdate_all-in-one/data/metadata/marc21.xml" metadata file is added
    And the "SampleTransfers/MetadataXMLValidation/small_mdupdate_all-in-one/data/metadata/metadata.txt.xml" metadata file is added
    And the "SampleTransfers/MetadataXMLValidation/small_mdupdate_all-in-one/data/metadata/bag-info.xml" metadata file is added
    And the "SampleTransfers/MetadataXMLValidation/small_mdupdate_all-in-one/data/metadata/swb-katalog.marc21.xml" metadata file is added
    And the "SampleTransfers/MetadataXMLValidation/small_mdupdate_all-in-one/data/metadata/source-metadata.csv" metadata file is added
    And the "SampleTransfers/MetadataXMLValidation/small_mdupdate_all-in-one/data/metadata/custom_dir/" metadata file is added
    And the reingest is approved
    And the reingest has been processed
    Then the "Generate METS.xml document" ingest job completes successfully
    And every metadata XML file in source-metadata.csv that has been validated has a PREMIS event with metadata validation details and pass outcome
    And every existing metadata XML file in the reingested source-metadata.csv has two dmdSecs with the same GROUPID, one with the original XML content which has been superseded by a new one that contains the updated XML content
    And every new metadata XML file in the reingested source-metadata.csv has a dmdSec with STATUS "update" that has a mdWrap with the specified OTHERMDTYPE which wraps the XML content
    And every deleted metadata XML file in the reingested source-metadata.csv has a dmdSec with STATUS "deleted" that has a mdWrap with the specified OTHERMDTYPE which wraps the original XML content
    And the AIP can be found in the Archival storage tab by searching the contents of its latest metadata files
    And the AIP can not be found in the Archival storage tab by searching the original contents of the deleted metadata files

  Scenario: Multiple re-ingests
    Given a "unzipped bag" transfer type located in "SampleTransfers/MetadataXMLValidation/small_initial_ingest"
    And a processing configuration for metadata only reingests
    When the AIP is downloaded
    Then the "Generate METS.xml document" ingest job completes successfully
    And every metadata XML file in source-metadata.csv that has been validated has a PREMIS event with metadata validation details and pass outcome
    And every metadata XML file in source-metadata.csv has a dmdSec with STATUS "original" that has a mdWrap with the specified OTHERMDTYPE which wraps the XML content
    And the AIP can be found in the Archival storage tab by searching the contents of its latest metadata files
    #
    # First reingest
    #
    When a "METADATA" reingest is started using the "default" processing configuration
    And the "SampleTransfers/MetadataXMLValidation/small_mdupdate_addition-only-1/data/metadata/source-metadata.csv" metadata file is added
    And the "SampleTransfers/MetadataXMLValidation/small_mdupdate_addition-only-1/data/metadata/custom_dir/" metadata file is added
    And the reingest is approved
    And the reingest has been processed
    Then the "Generate METS.xml document" ingest job completes successfully
    And every metadata XML file in source-metadata.csv that has been validated has a PREMIS event with metadata validation details and pass outcome
    And every metadata XML file in source-metadata.csv has a dmdSec with STATUS "update" that has a mdWrap with the specified OTHERMDTYPE which wraps the XML content
    And the AIP can be found in the Archival storage tab by searching the contents of its latest metadata files
    #
    # Second reingest
    #
    When a "METADATA" reingest is started using the "default" processing configuration
    And the "SampleTransfers/MetadataXMLValidation/small_mdupdate_addition-only-2/data/metadata/source-metadata.csv" metadata file is added
    And the "SampleTransfers/MetadataXMLValidation/small_mdupdate_addition-only-2/data/metadata/swb-katalog.marc21.xml" metadata file is added
    And the reingest is approved
    And the reingest has been processed
    Then the "Generate METS.xml document" ingest job completes successfully
    And every metadata XML file in source-metadata.csv that has been validated has a PREMIS event with metadata validation details and pass outcome
    And every metadata XML file in source-metadata.csv has a dmdSec with STATUS "update" that has a mdWrap with the specified OTHERMDTYPE which wraps the XML content
    And the AIP can be found in the Archival storage tab by searching the contents of its latest metadata files
