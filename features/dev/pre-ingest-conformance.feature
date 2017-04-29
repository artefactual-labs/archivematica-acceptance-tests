@preforma
Feature: Pre-ingest conformance check
  Archivists need to know whether or not mkv files which they are
  preserving are valid before they process them, because if they are
  invalid it might impact further preservation decisions.

  @picc
  Scenario Outline: Isla wants to confirm that her file is a valid .mkv
    Given that the user has ensured that the default processing config is in its default state
    And directory <transfer_path> contains files that are all <file_validity> .mkv
    When a transfer is initiated on directory <transfer_path>
    And the user waits for the "Select file format identification command" decision point to appear and chooses "Identify using Fido" during transfer
    And the user waits for the "Validate formats" micro-service to complete during transfer
    Then the "Validate formats" micro-service output is "<microservice_output>" during transfer
    When the user waits for the "Create SIP(s)" decision point to appear and chooses "Create single SIP and continue processing" during transfer
    And the user waits for the "Normalize" decision point to appear and chooses "Do not normalize" during ingest
    And the user waits for the "Select file format identification command|Process submission documentation" decision point to appear and chooses "Identify using Fido" during ingest
    And the user waits for the "Store AIP (review)" decision point to appear during ingest
    Then all PREMIS implementation-check-type validation events have eventOutcome = <event_outcome>

    Examples: File Validity Possibilities
    | file_validity | microservice_output    | event_outcome | transfer_path          |
    | valid         | Completed successfully | pass          | preforma/all-valid     |
    | not valid     | Failed                 | fail          | preforma/none-valid    |
