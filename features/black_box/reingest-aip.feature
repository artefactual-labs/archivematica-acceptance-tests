@black-box
Feature: Alma wants to be able to re-ingest an AIP and have the reingest recorded accurately in the AIP METS file.

  Scenario: Reingest without error
    Given an AIP has been reingested
    When the reingest processing is complete
    Then the AIP can be successfully stored

  Scenario: METS contains reingestion events
    Given an AIP has been reingested
    When the reingest processing is complete
    Then there is a reingestion event for each original object in the AIP METS

  Scenario: METS contains deleted files
    Given an AIP has been reingested
    When the reingest processing is complete
    Then there is a fileSec for deleted files for objects that were re-normalized

  Scenario: METS contains superseded techMDs
    Given an AIP has been reingested
    When the reingest processing is complete
    Then there is a current and a superseded techMD for each original object
