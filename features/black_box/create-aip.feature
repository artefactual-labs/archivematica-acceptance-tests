@black-box
Feature: Archivematica generates AIPs from different types of transfer source

Alma wants to be able to create AIPs from all of Archivematica's different transfer types and expects those AIPs to conform to a certain standard and consist of a number of properties that make them suitable for long-term preservation.

Background: The storage service is configured with a transfer source that can see the archivematica-sampledata repository.

  Scenario: Generate an AIP using a standard transfer workflow
    Given a "standard" transfer type located in "amauat-automated-acceptance-tests/standard-transfer/DemoTransferCSV"
    When the AIP is downloaded
    Then the AIP METS can be accessed and parsed by mets-reader-writer
    And the AIP conforms to expected content and structure
    And the AIP contains all files that were present in the transfer
    And the AIP contains a file called README.html in the data directory
    And the AIP contains a file called METS.xml in the data directory
    And the fileSec of the AIP METS will record every file in the objects and metadata directories of the AIP
    And the physical structMap of the AIP METS accurately reflects the physical layout of the AIP
    And every object in the AIP has been assigned a UUID in the AIP METS
    And every object in the objects and metadata directories has an amdSec
    And every PREMIS event recorded in the AIP METS records the logged-in user, the organization and the software as PREMIS agents

  Scenario: Generate an AIP using an unzipped bag transfer workflow
    Given a "unzipped bag" transfer type located in "amauat-automated-acceptance-tests/bagit/BagTransfer"
    When the transfer is approved
    Then the "Verify bag, and restructure for compliance" job completes successfully
    And there is a sourceMD containing a BagIt mdWrap in the AIP METS

  Scenario: Generate an AIP using a Dataverse workflow
    Given a "dataverse" transfer type located in "amauat-automated-acceptance-tests/Dataverse/NDSAStaffingReport"
    When the AIP is downloaded
    Then the "Set convert Dataverse structure flag" job completes successfully
    And the "Set parse Dataverse METS flag" job completes successfully
    And the "Convert Dataverse structure" job completes successfully
    And the "Parse Dataverse METS XML" job completes successfully
    And the METS file contains a dmdSec with DDI metadata
