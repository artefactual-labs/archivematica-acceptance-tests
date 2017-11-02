Feature: Full AIP re-ingest
  Users want to be able to take an existing AIP and perform a full re-ingest on
  it. (To what end?)

  @full-reingest
  Scenario: Jeff creates an AIP, and then performs a metadata-only re-ingest on it, adds metadata to it, and confirms that her newly added metadata are in the modified METS file.
    Given a fully automated AIP creation default processing config
    When a transfer is initiated on directory ~/archivematica-sampledata/TestTransfers/acceptance-tests/easy
    And the user waits for the AIP to appear in archival storage
    And the user initiates a full re-ingest on the AIP
    And the user waits for the "Approve standard transfer" decision point to appear and chooses "Approve transfer" during transfer
