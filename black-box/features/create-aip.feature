Feature: Archivematica generates AIPs from different types of transfer source

Scenario: Generate an AIP using a standard transfer workflow
Given the transfer ‘DemoTransfer’ is started with the automatedProcessingMCP processing configuration.
When the Transfer is COMPLETE
And the Ingest is COMPLETE
Then an AIP can be downloaded
And the AIP METS can be accessed and parsed by mets-reader-writer
