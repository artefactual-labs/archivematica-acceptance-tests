Feature: AIP Encryption
  Archivematica users and administrators want to be able to store AIPs
  encrypted. One motivation for this is that multiple copies of AIPs may be
  stored in locations where their owners do not have complete control over who
  may have access to them.

  # Note: these tests will fail when they need to set up the encrypted space
  # because the space will not be connected to the pipeline for some reason.
  @aip-encrypt @compressed
  Scenario: Richard wants to create a space on his Archivematica Storage Service that encrypts all AIPs stored in that space. He also wants to confirm that the AIPs stored in that space are encrypted both by trying to open them without the key and by reading the AIP's pointer file. Finally, he wants to be able to download the AIPS via the Archivematica interface and have them be decrypted prior to download.
    Given the user has ensured that there is a storage service space with attributes Access protocol: GPG encryption on Local Filesystem; Path: /; Staging path: /var/archivematica/storage_service_encrypted; GnuPG Private Key: Archivematica Storage Service GPG Key;
    And the user has ensured that there is a location in the GPG Space with attributes Purpose: AIP Storage; Relative path: var/archivematica/sharedDirectory/www/AIPsStoreEncrypted; Description: Store AIP Encrypted in standard Archivematica Directory;
    And that the user has ensured that the default processing config is in its default state
    When a transfer is initiated on directory ~/archivematica-sampledata/SampleTransfers/BagTransfer
    And the user waits for the "Select file format identification command" decision point to appear and chooses "Identify using Fido" during transfer
    And the user waits for the "Create SIP(s)" decision point to appear and chooses "Create single SIP and continue processing" during transfer
    And the user waits for the "Normalize" decision point to appear and chooses "Normalize for preservation" during ingest
    And the user waits for the "Approve normalization (review)" decision point to appear and chooses "Approve" during ingest
    And the user waits for the "Select file format identification command|Process submission documentation" decision point to appear and chooses "Identify using Fido" during ingest
    And the user waits for the "Store AIP (review)" decision point to appear and chooses "Store AIP" during ingest
    And the user waits for the "Store AIP location" decision point to appear and chooses "Store AIP Encrypted in standard Archivematica Directory" during ingest
    And the user waits for the AIP to appear in archival storage
    And the user downloads the AIP pointer file
    Then the pointer file contains a PREMIS:EVENT element for the encryption event
    And the pointer file contains a mets:transformFile element for the encryption event
    And the AIP on disk is encrypted
    When the user downloads the AIP
    Then the downloaded AIP is not encrypted

  @aip-encrypt @uncompressed
  Scenario: Richard wants to ensure that he can encrypt uncompressed AIPs.
    Given the user has ensured that there is a storage service space with attributes Access protocol: GPG encryption on Local Filesystem; Path: /; Staging path: /var/archivematica/storage_service_encrypted; GnuPG Private Key: Archivematica Storage Service GPG Key;
    And the user has ensured that there is a location in the GPG Space with attributes Purpose: AIP Storage; Relative path: var/archivematica/sharedDirectory/www/AIPsStoreEncrypted; Description: Store AIP Encrypted in standard Archivematica Directory;
    And that the user has ensured that the default processing config is in its default state
    And the processing config decision "Select compression algorithm" is set to "Uncompressed"
    When a transfer is initiated on directory ~/archivematica-sampledata/SampleTransfers/BagTransfer
    And the user waits for the "Select file format identification command" decision point to appear and chooses "Identify using Fido" during transfer
    And the user waits for the "Create SIP(s)" decision point to appear and chooses "Create single SIP and continue processing" during transfer
    And the user waits for the "Normalize" decision point to appear and chooses "Normalize for preservation" during ingest
    And the user waits for the "Approve normalization (review)" decision point to appear and chooses "Approve" during ingest
    And the user waits for the "Select file format identification command|Process submission documentation" decision point to appear and chooses "Identify using Fido" during ingest
    And the user waits for the "Store AIP (review)" decision point to appear and chooses "Store AIP" during ingest
    And the user waits for the "Store AIP location" decision point to appear and chooses "Store AIP Encrypted in standard Archivematica Directory" during ingest
    And the user waits for the AIP to appear in archival storage
    Then the uncompressed AIP on disk at /var/archivematica/sharedDirectory/www/AIPsStoreEncrypted/ is encrypted
    When the user downloads the AIP
    Then the downloaded uncompressed AIP is an unencrypted tarfile

