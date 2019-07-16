# Infinite AIPs Feature File
# ==============================================================================

# Example behave command to run this feature::
#
#     $ behave \
#           --tags=infinite-aips \
#           --no-skipped \
#           --no-logcapture \
#           -D runtime_supplied_transfer_path='TestTransfers/small' \
#           -D driver_name=Firefox \
#           -D am_url=http://127.0.0.1:62080/ \
#           -D am_password=test \
#           -D am_version=1.7 \
#           -D home=archivematica
#

@infinite-aips
Feature: Infinite AIPs
  Archivematica's developers want to automate the process of creating (large) AIPs
  until something breaks. This feature will help the developers to add features
  that make Archivematica more resilient when system resource and service
  limits are reached.

  Scenario: Joel creates an AIP from a runtime-supplied transfer source path repeatedly until something goes wrong.
    Given a default processing config that creates and stores an AIP
    When a transfer is initiated on the runtime-supplied directory
    And the user waits for the AIP to appear in archival storage
    # The following is a recursive step that calls the above two and then itself
    And the user creates the same AIP all over again
