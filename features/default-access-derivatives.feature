Feature: Normalization for access uses originals as as derivatives on error
  Users of Archivematica want original files to be used as the default for
  access derivatives when running a normalization command results in an error
  AND an access derivative is NOT created.

  @default-access-derivative
  Scenario: Tim wants to confirm that access derivatives are created for all of the .tif files in a particular transfer, even if the normalization command returns an error
  Given that normalization to .jpg of file ~/archivematica-sampledata/TestTransfers/tifsGoodAndBad/goodtif.tif will succeed
  And that normalization to .jpg of file ~/archivematica-sampledata/TestTransfers/tifsGoodAndBad/badtif.tif will error but still create a .jpg
  And that normalization to .jpg of file ~/archivematica-sampledata/TestTransfers/tifsGoodAndBad/badtif.tif will error and not create a .jpg
  And that the user has ensured that the default processing config is in its default state
  And the processing config decision "Select file format identification command (Transfer)" is set to "Identify using Siegfried"
  And the processing config decision "Create SIP(s)" is set to "Create single SIP and continue processing"
  And the processing config decision "Select file format identification command (Ingest)" is set to "Identify using Siegfried"
  And the processing config decision "Normalize" is set to "Normalize for access"
  And the processing config decision "Select file format identification command (Submission documentation & metadata)" is set to "Identify using Siegfried"
  When a transfer is initiated on directory ~/archivematica-sampledata/TestTransfers/tifsGoodAndBad
  # And the user waits for the "Store AIP (review)" decision point to appear during ingest
  And the user waits for the "Approve normalization (review)" decision point to appear during ingest
