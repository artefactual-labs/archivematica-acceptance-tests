# Archivematica Automated Tests (AMAUAT): Black-box testing

These tests are a work in progress. They primarily test Archivematica by
using the Archivematica API.

### To run

Access the `black-box` directory and using python 2, either:

`$ python behave`

or

`$ python2 -m behave`

**NB.** There are some Unicode issues to iron out using Python 3. These exist
across AMAUAT and `amclient.py`.

### Directory Layout

From the Behave [documentation][#behave-1] an environment might looks as
follows:

```
features/
features/signup.feature
features/login.feature
features/account_details.feature
features/environment.py
features/steps/
features/steps/website.py
features/steps/utils.py
```

Hooks in `encironment.py` won't run for example if the file sits at the 'steps'
level.

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
``` python
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

You can then create a steps file in your steps directory and develop the
automated tests from there.

[//]: # (References)

[behave-1]: https://behave.readthedocs.io/en/latest/tutorial.html#features
