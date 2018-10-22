# Infinite AIPs Feature File
# ==============================================================================
#
# Example behave command to run this feature. Note that we are setting
# ``max_check_aip_stored_attempts`` to 86400 so that we can poll the SS API for
# up to a day waiting for an AIP to be created::
#
#     $ behave \
#           --tags=infinite-aips \
#           --tags=decision.id.not-norm \
#           --no-skipped \
#           --no-logcapture \
#           -D runtime_supplied_transfer_path='~/archivematica-sampledata/TestTransfers/small' \
#           -D driver_name=Firefox \
#           -D am_url=http://127.0.0.1:62080/ \
#           -D am_password=test \
#           -D ss_url=http://127.0.0.1:62081/ \
#           -D ss_password=test \
#           -D ss_api_key=test \
#           -D am_version=1.7 \
#           -D home=archivematica \
#           -D max_check_aip_stored_attempts=86400

@infinite-aips
Feature: Infinite AIPs
  Archivematica's developers want to automate the process of creating (large) AIPs
  until something breaks. This feature will help the developers to add features
  that make Archivematica more resilient when system resource and service
  limits are reached.

  @decision.id.<id>
  Scenario Outline: Joel creates an AIP from a runtime-supplied transfer source path repeatedly until something goes wrong.
    Given a default processing config that creates and stores an AIP
    And the processing config decision "Normalize" is set to "<decision>"
    When a transfer is initiated on the runtime-supplied directory
    And the user queries the API until the AIP has been stored
    # The following is a recursive step that calls the above two and then itself
    And the user creates the same AIP all over again

    Examples: Normalization decisions
    | id        | decision                   |
    | not-norm  | Do not normalize           |
    | norm-pres | Normalize for preservation |
