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
    Given automated processing with all decision points resolved
    When a transfer is initiated on directory SampleTransfers/Images/pictures
    And the user waits for the AIP to appear in archival storage
    Then in the METS file the metsHdr element has a CREATEDATE attribute but no LASTMODDATE attribute
    And in the METS file the metsHdr element has one dmdSec next sibling element(s)
    And automated processing with all decision points resolved
    And the processing config decision "Normalize" is set to "Do not normalize"
    And the processing config decision "Reminder: add metadata if desired" is set to "None"
    When the user initiates a metadata-only re-ingest on the AIP
    When the user waits for the "Approve AIP reingest" decision point to appear and chooses "Approve AIP reingest" during ingest
    And the user waits for the "Reminder: add metadata if desired" decision point to appear during ingest
    And the user adds metadata
    And the user chooses "Continue" at decision point "Reminder: add metadata if desired" during ingest
    And the user waits for the AIP to appear in archival storage
    Then in the METS file the metsHdr element has a CREATEDATE attribute and a LASTMODDATE attribute
    And in the METS file the metsHdr element has two dmdSec next sibling element(s)
    And in the METS file the dmdSec element contains the metadata added
