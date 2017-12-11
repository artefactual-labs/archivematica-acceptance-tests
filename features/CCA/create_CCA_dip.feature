# Create CCA Dissemination Information Package feature file
#
# The following feature requires an instance of Archivematica 1.6 and the
# Storage Service 0.8 with an AIP already ingested.
#
# To pass this test, Behave requires some parameters passed as user data:
#
#   $ behave \
#     --tags=create_CCA_dip \
#     --no-skipped \
#     -D aip_uuid=<UUID> \
#     -D transfer_name=<TRANSFER_NAME>
#     -D output_dir=/path/to/output_dir
#     -D files_csv=/path/to/files.csv
#
# Example of files_csv file:
#
#   filename,lastmodified
#   "./image.png",1510647651
#   "./folder1/file 1.txt",1510647659
#   "./folder2/file 2.txt",
#
# Use a relative path to the objects folder for the filename and an Unix
# epoch time for the lastmodified date. If a last modified date should not
# be checked, because the date is missing in the FITS section of the METS
# file or for other reasons, leave that one empty. One way of getting this
# information is by navigating to the transfer objects folder and executing:
#
#   find -type f -print0 | xargs -0 stat --format '"%n",%Y'

@am16 @create_CCA_dip @automation-tools
Feature: Create CCA Dissemination Information Package
  The Canadian Centre for Architecture provides archived architectural drawings and other
  complex born-digital objects to its researchers.
  The CCA would like to provide these in Dissemination Information Packages (DIPs) that
  are easy for researchers to load into appropriate software and include any and all
  dependent digital objects.

  Scenario: Creating DIP with automation tools
    Given Tim has configured the automation-tools DIP creation bash script with all the required parameters
    And he has created that AIP using the current version of Archivematica (1.6.x)
    When he executes the DIP creation script
    Then the script retrieves the AIP and creates a new DIP named with the original Transfer name appended with the AIP UUID and “_DIP”
    And the DIP METS XML file that describes the contents of the DIP
    And the DIP objects directory contains one zip container with all objects from the original transfer
    And each DIP object file has its original filename and last modified date from the original transfer
    And the DIP zip file includes a copy of the submissionDocumentation from the original Transfer
      And a copy of the AIP METS file generated during ingest
    And the DIP is stored locally in the output directory specified in the script parameters
