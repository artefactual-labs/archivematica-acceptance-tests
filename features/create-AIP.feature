@create-AIP @am16
Feature: Create Basic AIP with Simple Automated Workflow ddfd
  Some institutions want to be able to begin preservation (or evaluation of Archivematica) 
  with the minimum set up possible, using as much default behaviour as possible, 
  and with as little user intervention as possible.  

@simpleconfig
Background: Configuration of simple automation (using standard config options, but not Automation tools) 
  Given that the user has ensured that the default processing config is in its default state
  And the processing config decision "Select file format identification command (Transfer)" is set to "Identify using Fido"
  And the processing config decision "Create SIP(s)" is set to "Create single SIP and continue processing"
  And the processing config decision "Select file format identification command (Ingest)" is set to "Identify using Fido"
  And the processing config decision "Normalize" is set to "Do not normalize"
  And the processing config decision "Approve normalization" is set to "Yes"
  And the processing config decision "Select file format identification command (Submission documentation & metadata)" is set to "Identify using Fido"
    
  @stp 
  Scenario: Straight Through Processing of new AIP	
  Given research data sets have been copied to the transfer location for preservation 
    # this is a new step - but could be 'empty' for now
  When a transfer is initiated on directory <transfer_path>
  And the user waits for the "Store AIP (review)" decision point to appear and chooses "Store AIP" during ingest
  And the user waits for the "Store AIP location" decision point to appear and chooses "Store AIP in standard Archivematica Directory" during ingest
  And the user waits for the AIP to appear in archival storage
  And the user downloads the AIP
  And the user decompresses the AIP
  Then in the METS file there are/is <ingest_number> PREMIS event(s) of type ingestion
  
  Examples: File Validity Possibilities
  | transfer_path | ingest_number          | 
  | valid         | Completed successfully | 
  | not valid     | Failed                 | 
  
  # To Do: 

  # 1) create config steps (below) so that they are no longer required as a user action:
      # And the processing config decision "Store AIP" is set to "Yes"
      # And the processing config decision "Store AIP location:" is set to "Store AIP in standard Archivematica Directory" 
      
  # 2) create a better "then" steps to define what successful creation of an AIP is for this scenario. I used the METS file count  
      # because the step has already been written, but it doesn't fit well. here is what I would prefer to see 
      # 
  
  # 2) in future we should move background steps to a feature file, then define a higher level step for config
      # (e.g. 'given system is configured for simple automation') that can be used in 'functional' features like this one 
  

  
    	# Test Data will not trigger errors or human decisions (e.g. no virus and therefore no quarantine required)	 	
   
   
