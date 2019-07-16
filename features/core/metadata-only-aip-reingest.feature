# behave \
#     --tags=mo-aip-reingest \
#     --no-skipped \
#     -v \
#     -D am_username=test \
#     -D am_password=test \
#     -D am_url=http://127.0.0.1:62080/ \
#     -D am_version=1.7 \
#     -D am_api_key=test \
#     -D ss_username=test \
#     -D ss_password=test \
#     -D ss_url=http://127.0.0.1:62081/ \
#     -D ss_api_key=test \
#     -D home=archivematica \
#     -D driver_name=Firefox
# behave --tags=mo-aip-reingest --no-skipped -v -D am_username=test -D am_password=test -D am_url=http://127.0.0.1:62080/ -D am_version=1.7 -D am_api_key=test -D ss_username=test -D ss_password=test -D ss_url=http://127.0.0.1:62081/ -D ss_api_key=test -D home=archivematica -D driver_name=Firefox

@mo-aip-reingest
Feature: Metadata-only AIP re-ingest
  Users want to be able to take an existing AIP and perform a metadata-only
  re-ingest on it so that they can add metadata to it and confirm that those
  metadata are in the re-ingested AIP's METS file.

  Scenario: Isla creates an AIP, and then performs a metadata-only re-ingest on it, adds metadata to it, and confirms that her newly added metadata are in the modified METS file.
    Given that the user has ensured that the default processing config is in its default state
    And the reminder to add metadata is enabled
    When a transfer is initiated on directory ~/archivematica-sampledata/SampleTransfers/Images/pictures
    And the user waits for the "Assign UUIDs to directories?" decision point to appear and chooses "No" during transfer
    And the user waits for the "Do you want to perform file format identification?" decision point to appear and chooses "Yes" during transfer
    And the user waits for the "Perform policy checks on originals?" decision point to appear and chooses "No" during transfer
    And the user waits for the "Create SIP(s)" decision point to appear and chooses "Create single SIP and continue processing" during transfer
    And the user waits for the "Normalize" decision point to appear and chooses "Normalize for preservation" during ingest
    And the user waits for the "Approve normalization (review)" decision point to appear and chooses "Approve" during ingest
    And the user waits for the "Perform policy checks on preservation derivatives?" decision point to appear and chooses "No" during ingest
    And the user waits for the "Perform policy checks on access derivatives?" decision point to appear and chooses "No" during ingest
    And the user waits for the "Reminder: add metadata if desired" decision point to appear and chooses "Continue" during ingest
    And the user waits for the "Do you want to perform file format identification?|Process submission documentation" decision point to appear and chooses "Yes" during ingest
    And the user waits for the "Bind PIDs?" decision point to appear and chooses "No" during ingest
    And the user waits for the "Document empty directories?" decision point to appear and chooses "No" during ingest
    And the user waits for the "Store AIP (review)" decision point to appear and chooses "Store AIP" during ingest
    And the user waits for the "Store AIP location" decision point to appear and chooses "Default Location" during ingest
    And the user waits for the AIP to appear in archival storage
    Then in the METS file the metsHdr element has a CREATEDATE attribute but no LASTMODDATE attribute
    And in the METS file the metsHdr element has one dmdSec next sibling element(s)
    When the user initiates a metadata-only re-ingest on the AIP
    When the user waits for the "Approve AIP reingest" decision point to appear and chooses "Approve AIP reingest" during ingest
    And the user waits for the "Normalize" decision point to appear and chooses "Do not normalize" during ingest
    And the user waits for the "Perform policy checks on preservation derivatives?" decision point to appear and chooses "No" during ingest
    And the user waits for the "Perform policy checks on access derivatives?" decision point to appear and chooses "No" during ingest
    And the user waits for the "Reminder: add metadata if desired" decision point to appear during ingest
    And the user adds metadata
    And the user chooses "Continue" at decision point "Reminder: add metadata if desired" during ingest
    And the user waits for the "Do you want to perform file format identification?|Process submission documentation" decision point to appear and chooses "Yes" during ingest
    And the user waits for the "Bind PIDs?" decision point to appear and chooses "No" during ingest
    And the user waits for the "Document empty directories?" decision point to appear and chooses "No" during ingest
    And the user waits for the "Store AIP (review)" decision point to appear and chooses "Store AIP" during ingest
    And the user waits for the "Store AIP location" decision point to appear and chooses "Default Location" during ingest
    And the user waits for the AIP to appear in archival storage
    Then in the METS file the metsHdr element has a CREATEDATE attribute and a LASTMODDATE attribute
    And in the METS file the metsHdr element has two dmdSec next sibling element(s)
    And in the METS file the dmdSec element contains the metadata added

