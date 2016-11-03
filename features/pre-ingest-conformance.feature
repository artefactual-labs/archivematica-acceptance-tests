Feature: Pre-ingest conformance check
  Archivists need to know whether or not mkv files which they are
  preserving are valid before they process them, because if they are
  invalid it might impact further preservation decisions.

  Scenario Outline: Isla wants to confirm that her file is a valid .mkv
    Given directory <transfer_path> contains files that are all <file_validity> .mkv
    When a transfer is initiated on directory <transfer_path>
    Then validation micro-service output is <microservice_output>
    And Archivematica <am_action>
    And all PREMIS implementation-check-type validation events have eventOutcome = <event_outcome>

    Examples: File Validity Possibilities
    | file_validity | microservice_output    | am_action            | event_outcome | transfer_path                           |
    | valid         | Completed successfully | continues processing | pass          | acceptance-tests/preforma/all-valid     |
    | not valid     | Failed                 | continues processing | fail          | acceptance-tests/preforma/none-valid    |
