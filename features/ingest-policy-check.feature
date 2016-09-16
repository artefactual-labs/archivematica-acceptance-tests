Feature: Ingest policy check
  Archivists want to check that the files that are defined for access or
  preservation conform to a pre-defined policy/policies. The access and
  preservation derivatives may have been created by Archivematica through
  normalization or may have been predefined by the user prior to
  transfer.

  @wip
  Scenario Outline: Isla has preservation derivatives and she needs to know whether they conform to her preservation policy
    Given MediaConch policy file <policy_file> is present in the local mediaconch-policies/ directory
    And directory <transfer_path> contains files that, when normalized, will all <do_files_conform> to <policy_file>
    And directory <transfer_path> contains a processing config that does normalization for preservation, etc.
    When the user uploads the policy file <policy_file>
    And a transfer is initiated on directory <transfer_path>
    Then policy checks for preservation derivatives micro-service output is <microservice_output>
    And all PREMIS policy-check-type validation events have eventOutcome = <event_outcome>
    # TODO
    # And Archivematica outputs a <verification_result> verification in the normalization report

    Examples: Policy Check Outcomes
    | do_files_conform | microservice_output    | event_outcome  | verification_result | transfer_path       | policy_file                       |
    | conform          | Completed successfully | pass           | successful          | all-conform-policy  | NYULibraries_MKVFFV1-MODIFIED.xsl |
    | do not conform   | Failed                 | fail           | failed              | none-conform-policy | NYULibraries_MKVFFV1-MODIFIED.xsl |
