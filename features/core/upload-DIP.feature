@am16 @upload_CCA_dip @automation-tools @wip
Feature: Upload CCA Dissemination Information Package
  The create_CCA_dip feature creates a CCA specific Dissemination Information Package. 
  This feature allows that DIP to be uploaded from the local file system to an 
  ATOM repository.  

  # The following scenario requires some parameters passed as user data:
  #
  #   tbc -- placeholder to list and describe parameters
  #   Location of DIP on local file system
  #   ATOM Url
  #   ATOM username
  #   ATOM password
 
 Scenario: Upload DIP with automation tools
   Given Tim has created a DIP using the create_CCA_Dip script
   And configured the automation-tools DIP upload script with all the required parameters
   And that the local machine can connect to the ATOM repository using rsync 

   When Tim initiates the DIP upload script providing the DIP location and ATOM parameters
    
   Then the DIP Upload Script retrieves the DIP from the local filesystem
   And the DIP is uploaded to the instance of ATOM indicated in the parameters
   And the DIP can be accessed in ATOM
    
# we mention the script parameters in the Given step and the "when" step - should this 
# just be done once? I am not sure exactly how the parameters will be provided so 
# wasn't sure which step it should go in.
