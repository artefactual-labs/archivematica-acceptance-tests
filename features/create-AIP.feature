Feature: Create Basic AIP with Automated Workflow 
  Some institutions want to be able to begin preservation (or evaluation of Archivematica) 
  with the minimum set up possible, using as much default behaviour as possible, 
  and with as little user intervention as possible.  

  @create-AIP @standard # I am just guessing we need this, but not clear what these are for
  Scenario: Minimal User Input Required
 	# Test Data will not trigger errors or human decisions (e.g. no virus and therefore no quarantine required)	 		
  Given that the user has ensured that the default processing config is in its default state
  	# to make this more JISC like, we might want to start with something like: 
  	# Given that a research data set has been copied to the transfer source location
  And the processing config decision "Select file format identification command (Transfer)" is set to "Identify using Fido"
  And the processing config decision "Create SIP(s)" is set to "Create single SIP and continue processing"
  And the processing config decision "Select file format identification command (Ingest)" is set to "Identify using Fido"
  And the processing config decision "Normalize" is set to "Do not normalize"
  And the processing config decision "Approve normalization" is set to "Yes"
  And the processing config decision "Select file format identification command (Submission documentation & metadata)" is set to "Identify using Fido"
  When a transfer is initiated on directory ~/archivematica-sampledata/SampleTransfers/BagTransfer
  	# could consider creating a ResearchData directory and putting in a real dataset?
  	# ultimately JISC want a highly automated workflow... I want to figure out how we can 
  	# automate a transfer once a dataset is dropped in a transfer source location
  And the user waits for the "Store AIP (review)" decision point to appear during ingest
  	# could we set the config do this automatically? e.g. 
  	# And the processing config decision "Store AIP" is set to "Yes"
  	# And the processing config decision "Store AIP location:" is set to "Store AIP in standard Archivematica Directory" 
  Then an AIP is created 
  And the AIP is stored in ....
  And the AIP has a METS file  
  
    # there are many other 'quality checks' we could make... including checking for PREMIS events
    # the above would be enough for now though
  
  	#in the METS file there are/is 7 PREMIS event(s) of type ingestion
  	#And in the METS file there are/is 7 PREMIS event(s) of type message digest calculation with properties {"eventDetail": [["contains", "program=\"python\""], ["contains", "module=\"hashlib.sha256()\""]], "eventOutcomeInformation/eventOutcomeDetail/eventOutcomeDetailNote": [["regex", "^[a-f0-9]+$"]]}
  	#And in the METS file there are/is 7 PREMIS event(s) of type virus check with properties {"eventDetail": [["contains",  "program=\"Clam AV\""]], "eventOutcomeInformation/eventOutcome": [["equals", "Pass"]]}

   #other ideas: perhaps use Scenario Outline so we can provide locations for multiple transfers
   # then we could indicate how many PREMIS events should be created for each