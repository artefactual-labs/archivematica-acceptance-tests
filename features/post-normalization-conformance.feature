Feature: Post-normalization conformance check
  Archivists need to verify that the preservation and access copies that
  Archivematica has created through normalization are in conformance with the
  .mkv specification so that they know they are placing derivatives in
  storage/repositories which are reliable.

  Scenario Outline: Isla wants to confirm that normalization to .mkv for preservation is successful
    Given directory <transfer_path> contains files that will all be normalized to <file_validity> .mkv
    And directory <transfer_path> contains a processing config that does normalization for preservation, etc.
    When a transfer is initiated on directory <transfer_path>
    Then validate preservation derivatives micro-service output is <microservice_output>
    And all preservation conformance checks in the normalization report have value <validation_result>
    And all PREMIS implementation-check-type validation events have eventOutcome = <event_outcome>

    Examples: Normalized for Preservation File Validity Possibilities
    | file_validity | microservice_output    | validation_result | event_outcome | transfer_path                       |
    | valid         | Completed successfully | Passed            | pass          | preforma/when-normalized-all-valid  |
    | not valid     | Failed                 | Failed            | fail          | preforma/when-normalized-none-valid |

  Scenario Outline: Isla wants to confirm that normalization to .mkv for access is successful
    Given directory <transfer_path> contains files that will all be normalized to <file_validity> .mkv
    And directory <transfer_path> contains a processing config that does normalization for access, etc.
    When the user edits the FPR rule to transcode .mov files to .mkv for access
    And a transfer is initiated on directory <transfer_path>
    Then validate access derivatives micro-service output is <microservice_output>
    And all access conformance checks in the normalization report have value <validation_result>

    Examples: Normalized for Access File Validity Possibilities
    | file_validity | microservice_output    | validation_result | event_outcome | transfer_path                              |
    | valid         | Completed successfully | Passed            | pass          | preforma/when-normalized-access-all-valid  |
