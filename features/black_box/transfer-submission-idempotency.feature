# Requires Archivematica 1.19 and amclient 1.7 or later.
#
# Run with:
#
#   make behave BEHAVE_ARGS="--tags=transfer-submission-idempotency"

@black-box @transfer-submission-idempotency
Feature: Transfer submission retries are idempotent
  Alma wants repeated transfer submission requests to identify the original
  transfer instead of creating duplicate preservation work.

  @same-key-retry
  Scenario: Retry a transfer submission with the same idempotency key
    Given a "standard" transfer located in "TestTransfers/small" is ready for idempotent submission
    When the transfer is submitted twice with the same idempotency key
    Then both transfer submissions are accepted with the same UUID
    When the idempotency key is reused with a different transfer name
    Then the changed transfer submission is rejected with status 422
    And the original idempotent transfer and ingest complete successfully
