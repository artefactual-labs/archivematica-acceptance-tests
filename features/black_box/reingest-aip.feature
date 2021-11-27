@black-box @black-box-reingest
Feature: Alma wants to be able to re-ingest an AIP and have the reingest recorded accurately in the AIP METS file.

  Scenario: Reingest without error
    Given a "standard" transfer type located in "SampleTransfers/DemoTransferCSV"
    When a "FULL" reingest is started using the "automated" processing configuration
    And the reingest is approved
    And the reingest has been processed
    Then the AIP can be successfully stored
    And there is a reingestion event for each original object in the AIP METS
    And there is a fileSec for deleted files for objects that were re-normalized
    And there is a current and a superseded techMD for each original object

  Scenario: Reingest unzipped bag transfer
    Given a "unzipped bag" transfer type located in "SampleTransfers/UnzippedBag"
    When a "FULL" reingest is started using the "automated" processing configuration
    And the reingest is approved
    And the reingest has been processed
    Then the AIP can be successfully stored
    And there is a reingestion event for each original object in the AIP METS
    And there is a fileSec for deleted files for objects that were re-normalized
    And there is a current and a superseded techMD for each original object
    And there is a sourceMD containing a BagIt mdWrap in the reingested AIP METS
