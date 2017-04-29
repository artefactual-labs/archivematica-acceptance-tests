@preforma @dev
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
    And the user waits for the "Validate preservation derivatives" micro-service to complete during ingest
    Then the "Validate preservation derivatives" micro-service output is "<microservice_output>" during ingest
    When the user waits for the "Approve normalization (review)" decision point to appear during ingest
    Then all preservation conformance checks in the normalization report have value <validation_result>
    When the user chooses "Approve" at decision point "Approve normalization (review)" during ingest
    And the user waits for the "Select file format identification command|Process submission documentation" decision point to appear and chooses "Identify using Fido" during ingest
    And the user waits for the "Store AIP (review)" decision point to appear during ingest
    Then all PREMIS implementation-check-type validation events have eventOutcome = <event_outcome>

    # Note: with recent Pronom update, the .mov file no longer has a default
    # preservation (to .mkv) role because it is now "Apple ProRes" fmt/797 and
    # not "Generic MOV"
    Examples: Normalized for Preservation File Validity Possibilities
    | file_validity | microservice_output    | validation_result | event_outcome | transfer_path                       |
    | valid         | Completed successfully | Passed            | pass          | preforma/when-normalized-all-valid  |
    # The following row must remain uncommented until we can find a video file that, when normalized to .mkv, no longer conforms to the mkv spec, according to MediaConch
    #| not valid     | Failed                 | Failed            | fail          | preforma/when-normalized-none-valid |

  @pncc @access
  Scenario Outline: Isla wants to confirm that normalization to .mkv for access is successful
    Given that the user has ensured that the default processing config is in its default state
    And directory <transfer_path> contains files that will all be normalized to <file_validity> .mkv
    When the user edits the FPR rule to transcode .mov files to .mkv for access
    And a transfer is initiated on directory <transfer_path>
    And the user waits for the "Select file format identification command" decision point to appear and chooses "Identify using Fido" during transfer
    And the user waits for the "Create SIP(s)" decision point to appear and chooses "Create single SIP and continue processing" during transfer
    And the user waits for the "Normalize" decision point to appear and chooses "Normalize for access" during ingest
    And the user waits for the "Validate access derivatives" micro-service to complete during ingest
    Then the "Validate access derivatives" micro-service output is "<microservice_output>" during ingest
    When the user waits for the "Approve normalization (review)" decision point to appear during ingest
    Then all access conformance checks in the normalization report have value <validation_result>

    Examples: Normalized for Access File Validity Possibilities
    | file_validity | microservice_output    | validation_result | event_outcome | transfer_path                              |
    | valid         | Completed successfully | Passed            | pass          | preforma/when-normalized-access-all-valid  |
