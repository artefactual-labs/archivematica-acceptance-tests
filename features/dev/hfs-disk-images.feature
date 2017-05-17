# WARNING: this feature file assumes that ucla/ and nypl/ directories
# containing specific HFS disk images are in the AM home directory. This needs
# to be fixed by putting the appropriate transfers in the
# archivematica-sampledata repository.

@hfs-disk-images @dev
Feature: HFS disk images are identified, characterized and extracted correctly
  Users of Archivematica want to be able to ingest disk images containing HFS
  file systems and ensure that they are identified, characterized, and
  extracted correctly.

  @img-ext
  Scenario: Shira wants to confirm that a correct AIP is created when a .img HFS disk image is ingested
  Given that the processing config is set up for HFS disk image transfers
  When a transfer is initiated on directory ~/ucla/227_026
  And the user waits for the "Identify file format" micro-service to complete during transfer
  Then the "Identify file format" micro-service output is "Completed successfully" during transfer
  And all files are identified as "HFS Disk Image"
  When the user waits for the "Extract contents from compressed archives" micro-service to complete during transfer
  Then the "Extract contents from compressed archives" micro-service output is "Completed successfully" during transfer
  And hfsexplorer was the extraction tool used
  When the user waits for the "Characterize and extract metadata" micro-service to complete during transfer
  Then the "Characterize and extract metadata" micro-service output is "Completed successfully" during transfer
  And one file was characterized as an HFS disk image using DFXML
  When the user waits for the "Store AIP (review)" decision point to appear during ingest
  Then in the METS file there are/is 1 PREMIS event(s) such that they are of type format identification and have properties {"eventDetail": [["contains", "program=\"Siegfried\""]], "eventOutcomeInformation/eventOutcomeDetail/eventOutcomeDetailNote": [["equals", "archivematica-fmt/6"]]}
  Then in the METS file there are/is 7 PREMIS event(s) such that they are of type unpacking and have properties {"eventDetail": [["contains", "program=\"hfsexplorer\""]]}
  # TODO: make assertion about dfxml in the METS file (requires new steps)

  @001-ext
  Scenario: Susan wants to confirm that a correct AIP is created when a .001 HFS disk image is ingested
  Given that the processing config is set up for HFS disk image transfers
  When a transfer is initiated on directory ~/nypl/M1126-0001
  And the user waits for the "Identify file format" micro-service to complete during transfer
  Then the "Identify file format" micro-service output is "Completed successfully" during transfer
  And all files are identified as "Raw Disk Image"
  When the user waits for the "Extract contents from compressed archives" micro-service to complete during transfer
  Then the "Extract contents from compressed archives" micro-service output is "Completed successfully" during transfer
  And hfsexplorer was the extraction tool used
  When the user waits for the "Characterize and extract metadata" micro-service to complete during transfer
  Then the "Characterize and extract metadata" micro-service output is "Completed successfully" during transfer
  And one file was characterized as an HFS disk image using DFXML
  When the user waits for the "Store AIP (review)" decision point to appear during ingest
  Then in the METS file there are/is 1 PREMIS event(s) such that they are of type format identification and have properties {"eventDetail": [["contains", "program=\"Siegfried\""]], "eventOutcomeInformation/eventOutcomeDetail/eventOutcomeDetailNote": [["equals", "archivematica-fmt/6"]]}
  Then in the METS file there are/is 7 PREMIS event(s) such that they are of type unpacking and have properties {"eventDetail": [["contains", "program=\"hfsexplorer\""]]}
