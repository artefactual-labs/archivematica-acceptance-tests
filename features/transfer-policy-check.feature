Feature: Transfer policy check
  Archivists want to check that the original files they transfer conform to 
  a pre-defined policy/policies before proceeding with further digital
  preservation actions.
  
  Scenario outline: Isla has started a transfer of files and needs to know if they conform to her policy for original files.
    Given MediaConch policy file <policy_file> is present in the local mediaconch-policies/ directory
    And directory <transfer_path> contains files that will all <do_files_conform> to <policy_file>
    When the user uploads the policy file <policy_file>
    And the user ensures there is an FPR command that uses policy file <policy_file>
    And the user ensures there is an FPR rule with purpose <purpose> that validates Generic MKV files against policy file <policy_file>
    And a transfer is initiated on directory <transfer_path>
    And Processing Configuration has been set to Check for policies = yes
    Then policy checks for originals micro-service output is <microservice_output>
    # If you don't do a test like this, the above assertion may be vacuously true.
    And all policy check for originals tasks indicate <event_outcome>
    And Archivematica writes full MediaConch output to log files stored in AIP

 Examples: Policy Check Outcomes
    | do_files_conform | microservice_output    | event_outcome  | verification_result | transfer_path                          | policy_file                       | purpose                                          |
    | conform          | Completed successfully | pass           | successful          | preforma/all-conform-policy-norm-org   | NYULibraries_MKVFFV1-MODIFIED.xsl | Validation of Original File against a Policy |
    | not conform      | Failed                 | fail           | failed              | preforma/none-conform-policy-norm-org  | NYULibraries_MKVFFV1-MODIFIED.xsl | Validation of Original File against a Policy |
