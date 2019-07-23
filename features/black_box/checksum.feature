@black-box
Feature: Alma wants to verify checksums transmitted with a transfer to ensure that the transfer contents haven't been corrupted.

  Scenario: External metadata checksums are verified
    Given a "standard" transfer type located in "SampleTransfers/DemoTransferCSV"
    When the transfer compliance is verified
    Then the "Verify metadata directory checksums" job completes successfully

  Scenario: External metadata checksums are not verified
    Given a "standard" transfer type located in "TestTransfers/fixityCheckShouldFail"
    When the transfer compliance is verified
    Then the "Verify metadata directory checksums" job fails
    And the "Failed transfer" microservice is executed
