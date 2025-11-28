@cpp @cpp-001
Feature: Checksum Generation and Recording (CPP-001).

  Scenario:
    Given a "standard" transfer type located in "TestTransfers/CPP/test"
    When the AIP is downloaded
    Then the AIP bag manifest file contains checksums for all files present in AIP payload
    And the checksum documents from the transfer persist to the AIP
