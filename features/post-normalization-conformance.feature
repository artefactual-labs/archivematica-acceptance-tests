Feature: Post-normalization conformance check
  Archivists need to verify that the preservation and access copies that
  Archivematica has created through normalization are in conformance with the
  .mkv specification so that they know they are placing derivatives in
  storage/repositories which are reliable.

  @pncc @preservation
  Scenario Outline: Isla wants to confirm that normalization to .mkv for preservation is successful
    Given that the user has ensured that the default processing config is in its default state
    And directory <transfer_path> contains files that will all be normalized to <file_validity> .mkv
    When a transfer is initiated on directory <transfer_path>
    And the user waits for the "Select file format identification command" decision point to appear and chooses "Identify using Fido" during transfer
    And the user waits for the "Create SIP(s)" decision point to appear and chooses "Create single SIP and continue processing" during transfer
    And the user waits for the "Normalize" decision point to appear and chooses "Normalize for preservation" during ingest
    Then validate preservation derivatives micro-service output is <microservice_output>
    When the user waits for the "Approve normalization (review)" decision point to appear during ingest
    Then all preservation conformance checks in the normalization report have value <validation_result>
    When the user chooses "Approve" at decision point "Approve normalization (review)" during ingest
    And the user waits for the "Select file format identification command|Process submission documentation" decision point to appear and chooses "Identify using Fido" during ingest
    And the user waits for the "Store AIP (review)" decision point to appear during ingest
    Then all PREMIS implementation-check-type validation events have eventOutcome = <event_outcome>

    Examples: Normalized for Preservation File Validity Possibilities
    | file_validity | microservice_output    | validation_result | event_outcome | transfer_path                                        |
    | valid         | Completed successfully | Passed            | pass          | acceptance-tests/preforma/when-normalized-all-valid  |
    | not valid     | Failed                 | Failed            | fail          | acceptance-tests/preforma/when-normalized-none-valid |

  @pncc @access
  Scenario Outline: Isla wants to confirm that normalization to .mkv for access is successful
    Given that the user has ensured that the default processing config is in its default state
    And directory <transfer_path> contains files that will all be normalized to <file_validity> .mkv
    #And directory <transfer_path> contains a processing config that does normalization for access, etc.
    When the user edits the FPR rule to transcode .mov files to .mkv for access
    And a transfer is initiated on directory <transfer_path>
    And the user waits for the "Select file format identification command" decision point to appear and chooses "Identify using Fido" during transfer
    And the user waits for the "Create SIP(s)" decision point to appear and chooses "Create single SIP and continue processing" during transfer
    And the user waits for the "Normalize" decision point to appear and chooses "Normalize for access" during ingest
    Then validate access derivatives micro-service output is <microservice_output>
    When the user waits for the "Approve normalization (review)" decision point to appear during ingest
    Then all access conformance checks in the normalization report have value <validation_result>

    Examples: Normalized for Access File Validity Possibilities
    | file_validity | microservice_output    | validation_result | event_outcome | transfer_path                                               |
    | valid         | Completed successfully | Passed            | pass          | acceptance-tests/preforma/when-normalized-access-all-valid  |
