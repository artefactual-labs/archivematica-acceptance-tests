Feature: Ingest policy check
  Archivists want to check that the files that are defined for access or
  preservation conform to a pre-defined policy/policies. The access and
  preservation derivatives may have been created by Archivematica through
  normalization or may have been predefined by the user prior to
  transfer.

  Scenario Outline: Isla has access derivatives and she needs to know whether they conform to her access policy
    Given MediaConch policy file <policy_file> is present in the local mediaconch-policies/ directory
    And directory <transfer_path> contains files that, when normalized, will all <do_files_conform> to <policy_file>
    And directory <transfer_path> contains a processing config that does normalization for access, etc.
    When the user uploads the policy file <policy_file>
    And the user ensures there is an FPR command that uses policy file <policy_file>
    And the user ensures there is an FPR rule with purpose <purpose> that validates Generic MKV files against policy file <policy_file>
    And the user edits the FPR rule to transcode .mkv files to .mkv for access
    And a transfer is initiated on directory <transfer_path>
    Then policy checks for access derivatives micro-service output is <microservice_output>
    # If you don't do a test like this, the above assertion may be vacuously true.
    And all policy check for access derivatives tasks indicate <event_outcome>

    Examples: Policy Check Outcomes
    | do_files_conform | microservice_output    | event_outcome  | verification_result | transfer_path                          | policy_file                       | purpose                                          |
    | conform          | Completed successfully | pass           | successful          | preforma/all-conform-policy-norm-acc   | NYULibraries_MKVFFV1-MODIFIED.xsl | Validation of Access Derivatives against a Policy |
    | not conform      | Failed                 | fail           | failed              | preforma/none-conform-policy-norm-acc  | NYULibraries_MKVFFV1-MODIFIED.xsl | Validation of Access Derivatives against a Policy |

  Scenario Outline: Isla has preservation derivatives and she needs to know whether they conform to her preservation policy
    Given MediaConch policy file <policy_file> is present in the local mediaconch-policies/ directory
    And directory <transfer_path> contains files that, when normalized, will all <do_files_conform> to <policy_file>
    And directory <transfer_path> contains a processing config that does normalization for preservation, etc.
    When the user uploads the policy file <policy_file>
    And the user ensures there is an FPR command that uses policy file <policy_file>
    And the user ensures there is an FPR rule with purpose <purpose> that validates Generic MKV files against policy file <policy_file>
    And a transfer is initiated on directory <transfer_path>
    Then policy checks for preservation derivatives micro-service output is <microservice_output>
    And all PREMIS policy-check-type validation events have eventOutcome = <event_outcome>
    # TODO:
    # And Archivematica outputs a <verification_result> verification in the normalization report

    Examples: Policy Check Outcomes
    | do_files_conform | microservice_output    | event_outcome  | verification_result | transfer_path                | policy_file                       | purpose                                                 |
    | conform          | Completed successfully | pass           | successful          | preforma/all-conform-policy  | NYULibraries_MKVFFV1-MODIFIED.xsl | Validation of Preservation Derivatives against a Policy |
    | not conform      | Failed                 | fail           | failed              | preforma/none-conform-policy | NYULibraries_MKVFFV1-MODIFIED.xsl | Validation of Preservation Derivatives against a Policy |

  Scenario Outline: Isla has manually normalized preservation derivatives and she needs to know whether they conform to her preservation policy
    Given MediaConch policy file <policy_file> is present in the local mediaconch-policies/ directory
    And directory <transfer_path>/manualNormalization/preservation/ contains a file manually normalized for preservation that will <do_files_conform> to <policy_file>
    And directory <transfer_path> contains a processing config that does normalization for preservation, etc.
    When the user uploads the policy file <policy_file>
    And the user ensures there is an FPR command that uses policy file <policy_file>
    And the user ensures there is an FPR rule with purpose <purpose> that validates Generic MKV files against policy file <policy_file>
    And a transfer is initiated on directory <transfer_path>
    Then policy checks for preservation derivatives micro-service output is <microservice_output>
    And all PREMIS policy-check-type validation events have eventOutcome = <event_outcome>
    # TODO:
    # And Archivematica outputs a <verification_result> verification in the normalization report

    Examples: Policy Check Outcomes
    | do_files_conform | microservice_output    | event_outcome  | verification_result | transfer_path                                                  | policy_file                       | purpose                                                 |
    | conform          | Completed successfully | pass           | successful          | preforma/manually-normalized-preservation-all-conform-policy   | NYULibraries_MKVFFV1-MODIFIED.xsl | Validation of Preservation Derivatives against a Policy |
    | not conform      | Failed                 | fail           | failed              | preforma/manually-normalized-preservation-none-conform-policy  | NYULibraries_MKVFFV1-MODIFIED.xsl | Validation of Preservation Derivatives against a Policy |

  Scenario Outline: Isla has manually normalized access derivatives and she needs to know whether they conform to her access policy
    Given MediaConch policy file <policy_file> is present in the local mediaconch-policies/ directory
    And directory <transfer_path>/manualNormalization/access/ contains a file manually normalized for access that will <do_files_conform> to <policy_file>
    And directory <transfer_path> contains a processing config that does normalization for access, etc.
    When the user uploads the policy file <policy_file>
    And the user ensures there is an FPR command that uses policy file <policy_file>
    And the user ensures there is an FPR rule with purpose <purpose> that validates Generic MKV files against policy file <policy_file>
    And a transfer is initiated on directory <transfer_path>
    Then policy checks for access derivatives micro-service output is <microservice_output>
    And all policy check for access derivatives tasks indicate <event_outcome>

    Examples: Policy Check Outcomes
    | do_files_conform | microservice_output    | event_outcome  | verification_result | transfer_path                                            | policy_file                       | purpose                                           |
    | conform          | Completed successfully | pass           | successful          | preforma/manually-normalized-access-all-conform-policy   | NYULibraries_MKVFFV1-MODIFIED.xsl | Validation of Access Derivatives against a Policy |
    | not conform      | Failed                 | fail           | failed              | preforma/manually-normalized-access-none-conform-policy  | NYULibraries_MKVFFV1-MODIFIED.xsl | Validation of Access Derivatives against a Policy |
