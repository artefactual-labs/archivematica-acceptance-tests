@am16
Feature: Metadata-only AIP re-ingest
  Users want to be able to take an existing AIP and perform a metadata-only
  re-ingest on it so that they can add metadata to it and confirm that those
  metadata are in the re-ingested AIP's METS file.

  @mo-aip-reingest
  Scenario: Isla creates an AIP, and then performs a metadata-only re-ingest on it, adds metadata to it, and confirms that her newly added metadata are in the modified METS file.
    Given that the user has ensured that the default processing config is in its default state
    And the reminder to add metadata is enabled
    When a transfer is initiated on directory ~/archivematica-sampledata/SampleTransfers/BagTransfer
    And the user waits for the "Select file format identification command" decision point to appear and chooses "Identify using Fido" during transfer
    And the user waits for the "Create SIP(s)" decision point to appear and chooses "Create single SIP and continue processing" during transfer
    And the user waits for the "Normalize" decision point to appear and chooses "Normalize for preservation" during ingest
    And the user waits for the "Approve normalization (review)" decision point to appear and chooses "Approve" during ingest
    And the user waits for the "Reminder: add metadata if desired" decision point to appear and chooses "Continue" during ingest
    And the user waits for the "Select file format identification command|Process submission documentation" decision point to appear and chooses "Identify using Fido" during ingest
    And the user waits for the "Store AIP (review)" decision point to appear during ingest
    Then in the METS file the metsHdr element has a CREATEDATE attribute but no LASTMODDATE attribute
    And in the METS file the metsHdr element has no dmdSec element as a next sibling
    When the user chooses "Store AIP" at decision point "Store AIP (review)" during ingest
    And the user waits for the "Store AIP location" decision point to appear and chooses "Store AIP in standard Archivematica Directory" during ingest
    And the user waits for the AIP to appear in archival storage
    And the user initiates a metadata-only re-ingest on the AIP
    And the user waits for the "Approve AIP reingest" decision point to appear and chooses "Approve AIP reingest" during ingest
    And the user waits for the "Normalize" decision point to appear and chooses "Do not normalize" during ingest
    And the user waits for the "Reminder: add metadata if desired" decision point to appear during ingest
    And the user adds metadata
    And the user chooses "Continue" at decision point "Reminder: add metadata if desired" during ingest
    And the user waits for the "Select file format identification command|Process submission documentation" decision point to appear and chooses "Identify using Fido" during ingest
    And the user waits for the "Store AIP (review)" decision point to appear during ingest
    Then in the METS file the metsHdr element has a CREATEDATE attribute and a LASTMODDATE attribute
    And in the METS file the metsHdr element has one dmdSec element as a next sibling
    And in the METS file the dmdSec element contains the metadata added

