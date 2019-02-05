# Upload CCA Dissemination Information Package feature file
#
# The following feature has been created to determine how the automation-tools
# dips.atom_upload.py (called through etc/atom_upload_script.sh) should work.
#
# The scenario included in this feature has not been automated yet.

@am16 @upload_CCA_dip @automation-tools @non-executable
Feature: Upload CCA Dissemination Information Package
  The create_CCA_dip feature creates a CCA specific Dissemination Information Package.
  This feature allows that DIP to be uploaded from the local file system to an
  ATOM repository.

 Scenario: Upload DIP with automation tools
   Given Tim has created a DIP using the create_CCA_Dip script
   And configured the automation-tools DIP upload script with all the required parameters
   And that the local machine can connect to the ATOM repository using rsync
   When Tim initiates the DIP upload script providing the DIP location and ATOM parameters
   Then the DIP Upload Script retrieves the DIP from the local filesystem
   And the DIP is uploaded to the instance of ATOM indicated in the parameters
   And the DIP can be accessed in ATOM
