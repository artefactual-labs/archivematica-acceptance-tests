# TODO: make tests possible without specific processing configs by having a
# "When the user chooses <decision> at choice point <choice>". For one thing,
# it allows tests that use the existing archivematica-sample-data transfer
# sources.

Feature: Metadata-only AIP re-ingest
  Users want to be able to take an existing AIP and perform a metadata-only
  re-ingest on it so that they can add metadata to it and confirm that those
  metadata are in the re-ingested AIP's METS file.

  @testing
  Scenario: Isla creates an AIP, and then performs a metadata-only re-ingest on it, adds metadata to it, and confirms that her newly added metadata are in the modified METS file.
    Given that the user has ensured that the default processing config is in its default state
    And the reminder to add metadata is enabled
    When a transfer is initiated on directory archivematica-sampledata/SampleTransfers/BagTransfer
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

    ## When the user adds metadata and continues processing
    # Click on "show metadata" report icon FOR THE SIP being reingested:
    # - Within this "div.sip-row#sip-row-<SIP_UUID>", find this: $('a.btn_show_metadata') and click it
    # Or just go to this URL: http://192.168.168.192/ingest/90903160-2add-4a65-9741-049a34462d2d/
    # Or just go straight to this URL: http://192.168.168.192/ingest/90903160-2add-4a65-9741-049a34462d2d/metadata/add/
    # Add something distinctive in a subset of the fields in the form:
    # $("input#id_title").val('hi')
    # $("input#id_creator").val('hi')
    # $('input[value=Save]').click()
    # http://192.168.168.192/ingest/
    # "Job: Reminder: add metadata if desired" "- Continue"
    # "Job: Select file format identification command" "Identify using Fido" "Skip File identification" "Identify using Siegfried" "Identify by File Extension"

    # Confirm that the new metadata is in the AIP METS file
    # - click "review"
    # - Confirm that the values we put in the metadata (e.g., for title, creator) are in the METS file, cf below
    # - Confirm that mets:metsHdr has LASTMODDATE attr with a value; it didn't before
    # <mets:mets xmlns:mets="http://www.loc.gov/METS/" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.loc.gov/METS/ http://www.loc.gov/standards/mets/version18/mets.xsd">
    #   <mets:metsHdr CREATEDATE="2016-10-20T16:31:07" LASTMODDATE="2016-10-20T18:14:51"/>
    #   <mets:dmdSec ID="dmdSec_589200" CREATED="2016-10-20T18:14:51" STATUS="original">
    #     <mets:mdWrap MDTYPE="DC">
    #       <mets:xmlData>
    #         <dcterms:dublincore xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xsi:schemaLocation="http://purl.org/dc/terms/ http://dublincore.org/schemas/xmls/qdc/2008/02/11/dcterms.xsd">
    #           <dc:title>Broccoli</dc:title>
    #           <dc:creator>Bizin</dc:creator>
    #           <dc:type>Archival Information Package</dc:type>
    #
    ## Then Archivematica adds new or updated metadata to AIP METS file
    ## And Archivematica adds LASTMODDATE attribute to metsHdr in AIP METS file

