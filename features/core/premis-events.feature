@premis-events @am16
Feature: PREMIS events are recorded correctly
  Users of Archivematica want to be sure that the steps taken by
  Archivematica are recorded correctly in the resulting METS file according
  to the PREMIS specification.

  @standard
  Scenario: Isla wants to confirm that standard PREMIS events are created
  Given that the user has ensured that the default processing config is in its default state
  And the processing config decision "Select file format identification command (Transfer)" is set to "Identify using Fido"
  And the processing config decision "Create SIP(s)" is set to "Create single SIP and continue processing"
  And the processing config decision "Select file format identification command (Ingest)" is set to "Identify using Fido"
  And the processing config decision "Normalize" is set to "Do not normalize"
  And the processing config decision "Approve normalization" is set to "Yes"
  And the processing config decision "Select file format identification command (Submission documentation & metadata)" is set to "Identify using Fido"
  When a transfer is initiated on directory ~/archivematica-sampledata/SampleTransfers/BagTransfer
  And the user waits for the "Store AIP (review)" decision point to appear during ingest
  Then in the METS file there are/is 7 PREMIS event(s) of type ingestion
  And in the METS file there are/is 7 PREMIS event(s) of type message digest calculation with properties {"eventDetail": [["contains", "program=\"python\""], ["contains", "module=\"hashlib.sha256()\""]], "eventOutcomeInformation/eventOutcomeDetail/eventOutcomeDetailNote": [["regex", "^[a-f0-9]+$"]]}
  And in the METS file there are/is 7 PREMIS event(s) of type virus check with properties {"eventDetail": [["contains",  "program=\"Clam AV\""]], "eventOutcomeInformation/eventOutcome": [["equals", "Pass"]]}

  @package
  Scenario: Isla wants to confirm that an unpacking PREMIS event is created when a package is ingested
  Given that the user has ensured that the default processing config is in its default state
  And the processing config decision "Select file format identification command (Transfer)" is set to "Identify using Fido"
  And the processing config decision "Create SIP(s)" is set to "Create single SIP and continue processing"
  And the processing config decision "Select file format identification command (Ingest)" is set to "Identify using Fido"
  And the processing config decision "Normalize" is set to "Do not normalize"
  And the processing config decision "Approve normalization" is set to "Yes"
  And the processing config decision "Select file format identification command (Submission documentation & metadata)" is set to "Identify using Fido"
  When a transfer is initiated on directory ~/archivematica-sampledata/TestTransfers/Unicode
  And the user waits for the "Store AIP (review)" decision point to appear during ingest
  Then in the METS file there are/is 11 PREMIS event(s) of type unpacking

  @registration
  Scenario: Isla wants to confirm that a registration PREMIS event is created when an accession number is provided with a transfer
  Given that the user has ensured that the default processing config is in its default state
  And the processing config decision "Select file format identification command (Transfer)" is set to "Identify using Fido"
  And the processing config decision "Create SIP(s)" is set to "Create single SIP and continue processing"
  And the processing config decision "Select file format identification command (Ingest)" is set to "Identify using Fido"
  And the processing config decision "Normalize" is set to "Do not normalize"
  And the processing config decision "Approve normalization" is set to "Yes"
  And the processing config decision "Select file format identification command (Submission documentation & metadata)" is set to "Identify using Fido"
  When a transfer is initiated on directory ~/archivematica-sampledata/SampleTransfers/BagTransfer with accession number 1234-567
  And the user waits for the "Store AIP (review)" decision point to appear during ingest
  Then in the METS file there are/is 6 PREMIS event(s) of type registration with properties {"eventOutcomeInformation/eventOutcomeDetail/eventOutcomeDetailNote": [["equals", "accession#1234-567"]]}

  @quarantine
  Scenario: Isla wants to confirm that quarantine PREMIS events are created when files are put under quarantine
  Given that the user has ensured that the default processing config is in its default state
  And the processing config decision "Select file format identification command (Transfer)" is set to "Identify using Fido"
  And the processing config decision "Create SIP(s)" is set to "Create single SIP and continue processing"
  And the processing config decision "Select file format identification command (Ingest)" is set to "Identify using Fido"
  And the processing config decision "Normalize" is set to "Do not normalize"
  And the processing config decision "Approve normalization" is set to "Yes"
  And the processing config decision "Select file format identification command (Submission documentation & metadata)" is set to "Identify using Fido"
  And the processing config decision "Send transfer to quarantine" is set to "None"
  When a transfer is initiated on directory ~/archivematica-sampledata/SampleTransfers/BagTransfer
  And the user waits for the "Workflow decision - send transfer to quarantine" decision point to appear and chooses "Quarantine" during transfer
  And the user waits for the "Remove from quarantine" decision point to appear and chooses "Unquarantine" during transfer
  And the user waits for the "Store AIP (review)" decision point to appear during ingest
  Then in the METS file there are/is 6 PREMIS event(s) of type quarantine
  And in the METS file there are/is 6 PREMIS event(s) of type unquarantine

  @format-identification
  Scenario: Isla wants to confirm that quarantine PREMIS events are created when files are put under quarantine
  Given that the user has ensured that the default processing config is in its default state
  And the processing config decision "Select file format identification command (Transfer)" is set to "Identify using Siegfried"
  And the processing config decision "Create SIP(s)" is set to "Create single SIP and continue processing"
  And the processing config decision "Select file format identification command (Ingest)" is set to "Identify using Siegfried"
  And the processing config decision "Normalize" is set to "Do not normalize"
  And the processing config decision "Approve normalization" is set to "Yes"
  And the processing config decision "Select file format identification command (Submission documentation & metadata)" is set to "Identify using Siegfried"
  When a transfer is initiated on directory ~/archivematica-sampledata/SampleTransfers/BagTransfer
  And the user waits for the "Store AIP (review)" decision point to appear during ingest
  Then in the METS file there are/is 7 PREMIS event(s) of type format identification with properties {"eventDetail": [["contains", "program=\"Siegfried\"; version="]], "eventOutcomeInformation/eventOutcome": [["equals", "Positive"]], "eventOutcomeInformation/eventOutcomeDetail/eventOutcomeDetailNote": [["contains", "fmt"]]}

