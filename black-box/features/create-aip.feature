Feature: Archivematica generates AIPs from different types of transfer source

Alma wants to be able to create AIPs from all of Archivematica’s different transfer types and expects those AIPs to conform to a certain standard and consist of a number of properties that make them suitable for long-term preservation.

Background: The storage service is configured with a transfer source that can see the archivematica-sampledata repository.

Scenario: Generate an AIP using a standard transfer workflow
Given the transfer ‘DemoTransfer’ is started with the automatedProcessingMCP processing configuration.
When the Transfer is COMPLETE
And the Ingest is COMPLETE
Then an AIP can be downloaded
And the AIP METS can be accessed and parsed by mets-reader-writer
