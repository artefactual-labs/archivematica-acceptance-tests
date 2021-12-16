@metadata-xml
Feature: Roco wants to ensure that metadata XML files are validated and recorded in the AIP METS

Background: The MCPClient service has been configured to validate metadata XML files and the storage service has a transfer source location with sample transfers that contain source-metadata.csv files that can be used to test ingest, reingest and indexing of AIPs.

  Scenario: Metadata XML files present in the source-metadata.csv file are recorded in the AIP METS on first ingest
    Given a "unzipped bag" transfer type located in "SampleTransfers/MetadataXMLValidation/small"
    When the AIP is downloaded
    Then the "Generate METS.xml document" ingest job completes successfully
    And the AIP METS can be accessed and parsed by mets-reader-writer
    And the AIP conforms to expected content and structure
    And the AIP contains all files that were present in the transfer
    And the AIP contains a file called README.html in the data directory
    And the AIP contains the METS file in the data directory
    And the fileSec of the AIP METS will record every file in the objects and metadata directories of the AIP
    And the physical structMap of the AIP METS accurately reflects the physical layout of the AIP
    And every object in the AIP has been assigned a UUID in the AIP METS
    And every object in the objects and metadata directories has an amdSec
    And every PREMIS event recorded in the AIP METS records the logged-in user, the organization and the software as PREMIS agents
    And every metadata XML file in source-metadata.csv has a dmdSec with STATUS original that has a mdWrap with the specified OTHERMDTYPE which wraps the XML content

  Scenario: Metadata XML information from source-metadata.csv recorded in the AIP METS on first ingest can be updated through metadata only reingest
    Given a "unzipped bag" transfer type located in "SampleTransfers/MetadataXMLValidation/small"
    And a processing configuration for metadata only reingests
    When the AIP is downloaded
    And a "METADATA" reingest is started using the "default" processing configuration
    And the "SampleTransfers/MetadataXMLValidation/small_mdupdate/data/metadata/slub-rights.xml" metadata file is added
    And the "SampleTransfers/MetadataXMLValidation/small_mdupdate/data/metadata/mods.xml" metadata file is added
    And the "SampleTransfers/MetadataXMLValidation/small_mdupdate/data/metadata/lido.xml" metadata file is added
    And the "SampleTransfers/MetadataXMLValidation/small_mdupdate/data/metadata/dc.xml" metadata file is added
    And the "SampleTransfers/MetadataXMLValidation/small_mdupdate/data/metadata/marc21.xml" metadata file is added
    And the "SampleTransfers/MetadataXMLValidation/small_mdupdate/data/metadata/metadata.txt.xml" metadata file is added
    And the "SampleTransfers/MetadataXMLValidation/small_mdupdate/data/metadata/bag-info.xml" metadata file is added
    And the "SampleTransfers/MetadataXMLValidation/small_mdupdate/data/metadata/source-metadata.csv" metadata file is added
    And the "SampleTransfers/MetadataXMLValidation/small_mdupdate/data/metadata/custom_dir/" metadata file is added
    And the reingest is approved
    And the reingest has been processed
    Then the AIP can be successfully stored
    And the "Reingest AIP" ingest microservice completes successfully
    And the "Generate METS.xml document" ingest job completes successfully
    And every existing metadata XML file in the reingested source-metadata.csv has two dmdSecs with the same GROUPID, one with the original XML content which has been superseded by a new one that contains the updated XML content
    And every new metadata XML file in the reingested source-metadata.csv has a dmdSec with STATUS update that has a mdWrap with the specified OTHERMDTYPE which wraps the XML content
