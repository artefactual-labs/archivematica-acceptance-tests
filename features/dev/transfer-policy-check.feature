@preforma
Feature: Transfer policy check
  Archivists want to check that the original files they transfer conform to a
  pre-defined policy/policies before proceeding with further digital
  preservation actions.

  @tpc
  Scenario Outline: Isla has started a transfer of files and needs to know if they conform to her policy for original files.
    Given that the user has ensured that the default processing config is in its default state
    And the processing config decision "Perform policy checks on originals" is set to "Yes"
    And MediaConch policy file <policy_file> is present in the local etc/mediaconch-policies/ directory
    And directory <transfer_path> contains files that all do <do_files_conform> to <policy_file>
    When the user uploads the policy file <policy_file>
    And the user ensures there is an FPR command that uses policy file <policy_file>
    And the user ensures there is an FPR rule with purpose <purpose> that validates Generic MKV files against policy file <policy_file>
    And a transfer is initiated on directory <transfer_path>
    And the user waits for the "Select file format identification command" decision point to appear and chooses "Identify using Fido" during transfer
    And the user waits for the "Policy checks for originals" micro-service to complete during transfer
    Then the "Policy checks for originals" micro-service output is "<microservice_output>" during transfer
    And all policy check for originals tasks indicate <event_outcome>
    When the user waits for the "Create SIP(s)" decision point to appear and chooses "Create single SIP and continue processing" during transfer
    And the user waits for the "Normalize" decision point to appear and chooses "Do not normalize" during ingest
    And the user waits for the "Select file format identification command|Process submission documentation" decision point to appear and chooses "Identify using Fido" during ingest
    And the user waits for the "Store AIP (review)" decision point to appear and chooses "Store AIP" during ingest
    And the user waits for the "Store AIP location" decision point to appear and chooses "Store AIP in standard Archivematica Directory" during ingest
    And the user waits for the AIP to appear in archival storage
    And the user downloads the AIP
    And the user decompresses the AIP
    # TODO: where does the transfer policy check policy end up?
    #Then the submissionDocumentation directory of the AIP contains a copy of the MediaConch policy file <policy_file>
    Then the transfer logs directory of the AIP contains a MediaConch policy check output file for each policy file tested against <policy_file>

 Examples: Policy Check Outcomes
    | do_files_conform | microservice_output    | event_outcome  | verification_result | transfer_path                          | policy_file                       | purpose                                  |
    | conform          | Completed successfully | pass           | successful          | preforma/all-conform-policy-originals  | NYULibraries_MKVFFV1-MODIFIED.xsl | Validation of Originals against a Policy |
    | not conform      | Failed                 | fail           | failed              | preforma/none-conform-policy-originals | NYULibraries_MKVFFV1-MODIFIED.xsl | Validation of Originals against a Policy |
