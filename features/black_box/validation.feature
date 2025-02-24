@black-box
Feature: Alma wants to ensure that JHOVE validation in Archivematica works correctly when files are validated, and that transfers fail when they contain unvalidated files.

  Scenario: Validation for a transfer fail
    Given a "standard" transfer type located in "SampleTransfers/JHOVEModulesValidation"
    When the transfer compliance is verified
    Then the "Identify file format" microservice completes successfully
    And the "Validate formats" job fails
    And 17 "Validate formats" transfer tasks were executed
    And 8 "Validate formats" transfer tasks failed
    And 9 "Validate formats" transfer tasks succeeded
    And the "Validation" microservice is executed
    And 1 AIFF file is failed
    And 1 AIFF file is succeeded
    And 1 GIF file is failed
    And 1 GIF file is succeeded
    And 1 JP2 file is failed
    And 1 JP2 file is succeeded
    And 1 JPG file is failed
    And 1 JPG file is succeeded
    And 1 PDF file is failed
    And 1 PDF file is succeeded
    And 1 TIF file is failed
    And 1 TIF file is succeeded
    And 1 WARC file is failed
    And 1 WARC file is succeeded
    And 1 WAV file is failed
    And 1 WAV file is succeeded
    And the AIP can be successfully stored
    And there are 16 original objects in the AIP METS with a validation event

    
