@black-box
Feature: Alma wants to ensure that JHOVE validation in Archivematica works correctly when files are validated, and that transfers fail when they contain unvalidated files.

  Scenario: Validation for a transfer fail
    Given a "standard" transfer type located in "SampleTransfers/JHOVEModulesValidation"
    When the transfer compliance is verified
    Then the "Identify file format" microservice completes successfully
    And the "Validate formats" job fails
    And 16 "Validate formats" tasks were executed
    And 8 "Validate formats" tasks failed
    And 8 "Validate formats" were successful
