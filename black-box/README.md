# Archivematica Automated Tests (AMAUAT): Black-box testing

These tests are a work in progress. They primarily test Archivematica by
using the Archivematica API.

### Generating Steps Files

Create your feature, e.g.
```
Feature: Archivematica generates AIPs from different types of transfer source

Scenario: Generate an AIP using a standard transfer workflow
Given the transfer ‘DemoTransfer’ is started with the automatedProcessingMCP processing configuration.
When the Transfer is COMPLETE
And the Ingest is COMPLETE
Then an AIP can be downloaded
And the AIP METS can be accessed and parsed by mets-reader-writer
```

And run the feature from the root of the `black-box` directory:
```
$ behave features/create-aip.feature
```

An outline for a steps implementation will be created by Behave:
```
You can implement step definitions for undefined steps with these snippets:

@given(u'the transfer ‘DemoTransfer’ is started with the automatedProcessingMCP processing configuration.')
def step_impl(context):
    raise NotImplementedError(u'STEP: Given the transfer ‘DemoTransfer’ is started with the automatedProcessingMCP processing configuration.')


@when(u'the Transfer is COMPLETE')
def step_impl(context):
    raise NotImplementedError(u'STEP: When the Transfer is COMPLETE')


@when(u'the Ingest is COMPLETE')
def step_impl(context):
    raise NotImplementedError(u'STEP: When the Ingest is COMPLETE')


@then(u'an AIP can be downloaded')
def step_impl(context):
    raise NotImplementedError(u'STEP: Then an AIP can be downloaded')


@then(u'the AIP METS can be accessed and parsed by mets-reader-writer')
def step_impl(context):
    raise NotImplementedError(u'STEP: Then the AIP METS can be accessed and parsed by mets-reader-writer')
```
