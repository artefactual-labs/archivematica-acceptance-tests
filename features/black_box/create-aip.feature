@black-box
Feature: Archivematica generates AIPs from different types of transfer source

Alma wants to be able to create AIPs from all of Archivematica's different transfer types and expects those AIPs to conform to a certain standard and consist of a number of properties that make them suitable for long-term preservation.

Background: The storage service is configured with a transfer source that can see the archivematica-sampledata repository.

  Scenario: Generate an AIP using a standard transfer workflow
    Given an AIP has been created and stored
    When the AIP is downloaded
    Then the AIP METS can be accessed and parsed by mets-reader-writer

  Scenario: Generate a valid AIP
    Given an AIP has been created and stored
    When the AIP is downloaded
    Then the AIP conforms to expected content and structure

  Scenario: AIP has all original files
    Given an AIP has been created and stored
    When the AIP is downloaded
    Then the AIP contains all files that were present in the transfer

  Scenario: AIP contains a README file
    Given an AIP has been created and stored
    When the AIP is downloaded
    Then the AIP contains a file called README.html

  Scenario: AIP contains a METS file
    Given an AIP has been created and stored
    When the AIP is downloaded
    Then the AIP contains a METS.xml file in the data directory

  Scenario: fileSec contains every object
    Given an AIP has been created and stored
    When the AIP is downloaded
    Then the fileSec of the AIP METS will record every file in the objects and metadata directories of the AIP

  Scenario: physical structMap is accurate
    Given an AIP has been created and stored
    When the AIP is downloaded
    Then the physical structMap of the AIP METS accurately reflects the physical layout of the AIP

  Scenario: Every object has a UUID
    Given an AIP has been created and stored
    When the AIP is downloaded
    Then every object in the AIP has been assigned a UUID in the AIP METS

  Scenario: Every object in objects and metadata has an amdSec
    Given an AIP has been created and stored
    When the AIP is downloaded
    Then every object in the objects and metadata directories has an amdSec

  Scenario: Every event records logged-in user, the organization and the software
    Given an AIP has been created and stored
    When the AIP is downloaded
    Then every PREMIS event recorded in the AIP METS records the logged-in user, the organization and the software as PREMIS agents
