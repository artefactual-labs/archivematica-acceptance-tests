# AIP Encryption via Mirror Locations feature.
#
# How to Run this test on a Vagrant/Ansible deploy. (Note that this
# configuration assumes that the server user is archivematica and has the
# password 'vagrant'. This means you have to run `su; passwd archivematica`
# from the VM and set the password to 'vagrant'.)::
#
#     $ behave --tags=aip-encrypt-mirror \
#       --no-skipped \
#       -D am_version=1.7 \
#       -D driver_name=Firefox \
#       -D server_user=archivematica
#
# How to run this test against a docker-compose deploy (see
# https://github.com/artefactual-labs/am)::
#
#     $ behave --tags=aip-encrypt-mirror \
#       --no-skipped \
#       -D am_version=1.7 \
#       -D driver_name=Firefox \
#       -D am_username=test \
#       -D am_password=test \
#       -D am_url=http://127.0.0.1:62080/ \
#       -D am_api_key=test \
#       -D ss_username=test \
#       -D ss_password=test \
#       -D ss_url=http://127.0.0.1:62081/ \
#       -D home=archivematica \
#       -D docker_compose_path=/path/to/compose/dir

@aip-encrypt-mirror @am17
Feature: AIP Encryption via Mirror Locations
  Archivematica users want to be able to store AIPs unencrypted with encrypted
  replicas in mirror locations. This allows easy access to unencrypted AIPs
  as well as the ability to make redundant copies of encrypted replicas
  off-site.

  @compressed
  Scenario: Richard wants to create an AIP with an encrypted replica.
    Given there is a standard GPG-encrypted space in the storage service
    And there is a standard GPG-encrypted Replicator location in the storage service
    And the default AIP Storage location has the GPG-encrypted Replicator location as its replicator
    And the default processing config is in its default state
    When a transfer is initiated on directory ~/archivematica-sampledata/SampleTransfers/BagTransfer
    And standard AIP-creation decisions are made
    And the user waits for the "Store AIP location" decision point to appear and chooses "Store AIP in standard Archivematica Directory" during ingest
    And the user waits for the AIP to appear in archival storage
    And the user searches for the AIP UUID in the Storage Service
    Then the master AIP and its replica are returned by the search
    When the user downloads the master AIP pointer file
    And the user downloads the replica AIP pointer file
    Then the master AIP pointer file contains a(n) replication PREMIS:EVENT
    And the replica AIP pointer file contains a(n) creation PREMIS:EVENT
    And the replica AIP pointer file contains a(n) validation PREMIS:EVENT
    And the master AIP pointer file contains a PREMIS:OBJECT with a derivation relationship pointing to the replica AIP and the replication PREMIS:EVENT
    And the replica AIP pointer file contains a PREMIS:OBJECT with a derivation relationship pointing to the master AIP and the replication PREMIS:EVENT
    And the replica AIP pointer file contains a mets:transformFile element for the encryption event
    And the replica AIP pointer file contains a(n) encryption PREMIS:EVENT
    And the master AIP on disk is not encrypted
    And the replica AIP on disk is encrypted
    When the user downloads the replica AIP
    And the user downloads the master AIP
    Then the downloaded replica AIP is not encrypted
    And the master and replica AIPs are byte-for-byte identical
