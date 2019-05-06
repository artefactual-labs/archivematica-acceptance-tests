@black-box
Feature: Alma wants to be able to re-ingest an AIP and have the reingest recorded accurately in the AIP METS file.

  Scenario: Reingest without error
    Given a "SampleTransfers/DemoTransferCSV" AIP has been reingested
    When the reingest has been processed
    Then the AIP can be successfully stored
    And there is a reingestion event for each original object in the AIP METS
    And there is a fileSec for deleted files for objects that were re-normalized
    And there is a current and a superseded techMD for each original object
