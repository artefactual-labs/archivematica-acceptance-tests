Feature: Create CCA Dissemination Information Package
  The Canadian Centre for Architecture provides archived architectural drawings and other
  complex born-digital objects to its researchers. 
  The CCA would like to provide these in Dissemination Information Packages (DIPs) that 
  are easy for researchers to load into appropriate software and include any and all
  dependent digital objects.

Scenario: Creating DIP with script parameters 

Given Tim has created an AIP using current version of Archivematica (1.6.x)
    # with the standard structure as described in    
    # ...archivematica-1.6/user-manual/archival-storage/aip-structure/

When Tim initiates the create_dip.py script 
  And provides the UUID of the source AIP (aip_uuid) 
  And provides the environment variables (ss_url, ss_user, ss_api_key, directory)

Then the DIP Creation script will retrieve the AIP
  And creates a new DIP named with the original Transfer name appended with “-DIP”
  And creates a DIP-METS.xml file that describes the contents of the DIP
  And creates an objects directory containing one zip container with all objects from the   original transfer
  And ensures each object has it's original directory or file name in their original order
  And updates the 'last modified date' to reflect the value captured during Transfer
  And includes a copy of the submissionDocumentation included in the original Transfer
  And includes a copy of the AIP METS file generated during ingest
  And stores the DIP (locally... where?)
