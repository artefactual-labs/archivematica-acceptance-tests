@create-AIP @am16
Feature: Create Basic AIP with Simple Automated Workflow ddfd
  Some institutions want to be able to begin preservation (or evaluation of Archivematica) 
  with the minimum set up possible. They will want to provide directories of files (or a data set) to be preserved, and 
  have an Archival Information Package (AIP) created using as much default Archivematica behaviour as possible, 
  and with as little user intervention as possible.  

  Background: Configuration of simple automation (using standard config options, but not Automation tools)
  Given that the user has ensured that the default processing config is in its default state
  And the processing config decision "Select file format identification command (Transfer)" is set to "Identify using Siegfried"
  And the processing config decision "Create SIP(s)" is set to "Create single SIP and continue processing"
  And the processing config decision "Select file format identification command (Ingest)" is set to "Identify using Siegfried"
  And the processing config decision "Normalize" is set to "Do not normalize"
  And the processing config decision "Approve normalization" is set to "Yes"
  And the processing config decision "Select file format identification command (Submission documentation & metadata)" is set to "Identify using Siegfried"

  @stp
  Scenario Outline: Straight Through Processing of new AIP
  # this is a new step - but could be 'empty' for now
  Given research data sets have been copied to the transfer location for preservation
  When a transfer is initiated on directory <transfer_path>
  And the user waits for the "Store AIP (review)" decision point to appear during ingest
  Then in the METS file there are/is <ingest_number> PREMIS event(s) of type ingestion
  When the user chooses "Store AIP" at decision point "Store AIP (review)" during ingest
  And the user waits for the "Store AIP location" decision point to appear and chooses "Store AIP in standard Archivematica Directory" during ingest
  And the user waits for the AIP to appear in archival storage
  And the user downloads the AIP
  And the user decompresses the AIP

  Examples: File Validity Possibilities
  | transfer_path                           | ingest_number          |
  | ~/ResearchData/10_17863/CAM_679         | 4                      |

  # To Do: 
  # 1) create config steps (below) so that they are no longer required as a user action:
      # And the processing config decision "Store AIP" is set to "Yes"
      # And the processing config decision "Store AIP location:" is set to "Store AIP in standard Archivematica Directory" 
      
  # 2) create a better "then" steps to define what successful creation of an AIP is for this scenario. I used the last 4 lines in  
      # this scenario because they already existed. I'd prefer something like below 
      # - wondering if we can create empty steps for these? (for now at least)
      # Then all containers in the transfer are unpacked
      # And all files in the transfer are scanned for viruses
      # And a message digest is created for each file
      # And an AIP is created
      # And the AIP has a METS metadata file
      # And the AIP is stored in archival storage
  
  # 3) add remaining 'examples' (we have identified 7 test data sets at this stage for RDSS)
  
  # 4) in future we should move background steps to a feature file, then define a higher level step for config
      # (e.g. 'given system is configured for simple automation') that can be used in 'functional' features like this one 
  
  # 5) start adding other scenarios - like; research data set contains a virus; add normalisation; etc. 
