@am17 @preforma @picc @tcc
Feature: Transfer (i.e., pre-ingest) Conformance Check
  Archivists need to know whether or not mkv files which they are
  preserving are valid before they process them, because if they are
  invalid it might impact further preservation decisions.

  Scenario Outline: Isla wants to confirm that her file is a valid .mkv
    Given a processing configuration for conformance checks on originals
    And directory <transfer_path> contains files that are all <file_validity> .mkv
    When a transfer is initiated on directory <transfer_path>
    And the user waits for the "Validate formats" micro-service to complete during transfer
    Then the "Validate formats" micro-service output is "<microservice_output>" during transfer
    When the user waits for the "Store AIP (review)" decision point to appear during ingest
    Then all PREMIS implementation-check-type validation events have eventOutcome = <event_outcome>

    Examples: File Validity Possibilities
    | file_validity | microservice_output    | event_outcome | transfer_path          |
    | valid         | Completed successfully | pass          | preforma/all-valid     |
    | not valid     | Failed                 | fail          | preforma/none-valid    |
