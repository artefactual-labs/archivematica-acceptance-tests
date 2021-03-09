@black-box
Feature: Alma wants to ensure that virus scanning in Archivematica works correctly to ensure transfers pass when they have no viruses, and transfers fail when they contain viruses.

  Scenario: Virus checks for a transfer pass
    Given a "standard" transfer type located in "SampleTransfers/DemoTransferCSV"
    When the transfer compliance is verified
    Then the "Scan for viruses in directories" job completes successfully

  Scenario: Virus checks for a transfer fail
    Given a "standard" transfer type located in "TestTransfers/virusTests"
    When the transfer compliance is verified
    Then the "Scan for viruses in directories" job fails
    And the "Failed transfer" microservice is executed
