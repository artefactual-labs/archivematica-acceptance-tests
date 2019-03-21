@black-box
Feature: Alma wants to ensure that PREMIS events are recorded for all preservation events that occur during Transfer

  Scenario: PREMIS event for virus scanning
    Given an AIP has been created and stored
    When the AIP is downloaded
    Then there is a virus scanning event for each original object in the AIP METS

  Scenario: PREMIS event for message digest calculation
    Given an AIP has been created and stored
    When the AIP is downloaded
    Then there is a message digest calculation event for each original object in the AIP METS

  Scenario: PREMIS event for file format identification
    Given an AIP has been created and stored
    When the AIP is downloaded
    Then there is a file format identification event for each original object in the AIP METS

  Scenario: PREMIS event for ingestion
    Given an AIP has been created and stored
    When the AIP is downloaded
    Then there is an ingestion event for each original object in the AIP METS
