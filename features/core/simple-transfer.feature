@am172
Feature: Transfer files into Archivematica.
  Archivematica users want to move digital files from Archivematica's transfer 
  storage space and prepare them for Ingest as Submission Information Packages (SIP)

@textfile
Scenario Outline: The Archivematica user wants to transfer a text file.
  Given the user has selected “standard” as the Transfer Type value.
  When the user has entered a Transfer Name.
  And the user adds the “~/testTransfers/small” directory to the transfer.
  And the user selects the “Start transfer” option.
  And the user selects the “Approve transfer” option.
  When the processing config decision “Assign UUIDs to directories” is set to “Yes”.
  And the processing config decision “Send transfer to quarantine” is set to “No”.
  And the processing config decision “Remove from quarantine after (days)” is set to null.
  And the processing config decision “Generate transfer structure report” is set to “Yes”.
  And the processing config decision “Select file format identification command (Transfer)” is set to 
    “Identify using Siegfried”
  And the processing config decision “Extract packages” is set to “Yes”.
  And the processing config decision “Delete packages after extraction” is set to “Yes”.
  And the processing config decision “Perform policy checks on originals: is set to “No”.
  And the processing config decision “Examine contents” is set to “Skip examine contents”
  Then the “Approve transfer” microservice will run.
  And the “Verify transfer compliance” microservice will run.
  And the “Rename with transfer UUID” microservice will run.
  And the “Include default Transfer processingMCP.xml” microservice will run.
  And the “Assign file UUIDs and checksums” microservice will run.
  And the “Reformat metadata files” microservice will run.
  And the “Verify transfer checksums” microservice will run.
  And the “Generate METS.xml document” microservice will run.
  And the “Quarantine” microservice will run.
  And the “Scan for viruses” microservice will run.
  And the “Generate transfer structure report” microservice will run.
  And the “Clean up names” microservice will run.
  And the “Identify file format” microservice will run.
  And the “Extract packages” microservice will run.
  And the “Update METS.xml document” microservice will run.
  And the “Characterize and extract metadata” microservice will run.
  And the “Validation” microservice will run.
  And the “Examine contents” microservice will run.
  And the “Complete transfer” microservice will run.
  And the “Create SIP from Transfer” option should be presented to the user as the next
    processing action.
