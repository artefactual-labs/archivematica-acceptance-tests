@black-box
Feature: Alma wants to ensure that PREMIS events are recorded for all preservation events that occur during Transfer

  Scenario Outline: The minimum set of PREMIS events are recorded for a transfer
    Given a "<sample_transfer_path>" AIP has been created and stored
    When the AIP is downloaded
    Then there is a virus scanning event for each original object in the AIP METS
    And there is a message digest calculation event for each original object in the AIP METS
    And there is a file format identification event for each original object in the AIP METS
    And there is an ingestion event for each original object in the AIP METS
    And there are <validated_objects_count> original objects in the AIP METS with a validation event

    Examples: sample transfers
      | sample_transfer_path            | validated_objects_count |
      | SampleTransfers/DemoTransferCSV | 2                       |
      | TestTransfers/badNames          | 0                       |
