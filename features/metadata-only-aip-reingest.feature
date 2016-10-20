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

    # And the user has ensured that a non-reingested AIP exists in archival storage. This implies the following, if not.
    # And the user initiates a transfer vagrant/archivematica-sampledata/SampleTransfers/BagTransfer
    # And the user makes the following choices at Transfer decision points:
    # "Job: Approve standard transfer" "Approve transfer" "Reject transfer"
    # "Job: Select file format identification command" "Identify using Fido" "Skip File identification" "Identify using Siegfried" "Identify by File Extension"
    # "Job: Create SIP(s)" "Create single SIP and continue processing" "Send to backlog" "Reject transfer"
    # And the user makes the following choices at Ingest decision points:
    # "Job: Normalize" "Normalize for preservation"
    # "Job: Approve normalization" "Approve" "Reject" "Redo"
    # "Job: Reminder: add metadata if desired" "- Continue"
    # "Job: Select file format identification command" "Identify using Fido" "Skip File identification" "Identify using Siegfried" "Identify by File Extension"
    # "Job: Store AIP" NOTE: clicking on "review" and analyzing the METS XML is already (partially, at least) accomplished
    # Ensure AIP has not been reingested and is lacking metadata. On initial creation we can click the "review" link
    #   - has <mets:metsHdr CREATEDATE="2016-10-20T16:31:07"/> with NO "LASTMODDATE" attribute
    #   - has no <mets:dmdSec as a next sibling after <mets:metsHdr>
    # "Job: Store AIP" "Store AIP"
    # "Job: Store AIP location" "- Store AIP in standard Archivematica Directory"
    # Checking Archival Storage (http://192.168.168.192/archival-storage/)
    # - Use requests to download AIP to temp dir: href="/archival-storage/download/aip/90903160-2add-4a65-9741-049a34462d2d/"
    ## And the user ensures that a target AIP already exists in Archival storage

    # When user initiates a metadata re-ingest (using the default processing config)
    ## When the user selects metadata-only AIP re-ingest
    # $('a[href="#tab-reingest"]').click()
    # $('input#id_reingest-reingest_type_1').click()
    # $('button[name=submit-reingest-form]').click()
    # Assert:
    # $('div.alert-success').text()
    # "Package 90903160-2add-4a65-9741-049a34462d2d sent to pipeline Foxtrot (a02f176a-fde3-4de0-b76a-141ba01f66c4) for re-ingest"

    ## Then Archivematica displays "Job: approve AIP re-ingest" in the Ingest tab
    # http://192.168.168.192/ingest/
    # "Job: Approve AIP reingest"

    ## When the user approves AIP re-ingest
    # "Job: Approve AIP reingest" "Approve AIP reingest"

    # And the user chooses "Do not normalize" at "Job: Normalize"

    ## Then Archivematica displays "Job: Reminder: add metadata if desired" in the Ingest tab

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

