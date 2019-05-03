@black-box
Feature: Alma wants to ensure that PREMIS events are recorded for all preservation events that occur during Transfer

  Scenario: The minimum set of PREMIS events are recorded for a transfer
    Given an AIP has been created and stored
    When the AIP is downloaded
    Then there is a virus scanning event for each original object in the AIP METS
    And there is a message digest calculation event for each original object in the AIP METS
    And there is a file format identification event for each original object in the AIP METS
    And there is an ingestion event for each original object in the AIP METS
