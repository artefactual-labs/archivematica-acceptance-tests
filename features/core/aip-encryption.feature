@aip-encrypt @am17
Feature: AIP Encryption
  Archivematica users and administrators want to be able to store AIPs
  encrypted. One motivation for this is that multiple copies of AIPs may be
  stored in locations where their owners do not have complete control over who
  may have access to them.

  @compressed
  Scenario: Richard wants to create a space on his Archivematica Storage Service that encrypts all AIPs stored in that space. He also wants to confirm that the AIPs stored in that space are encrypted both by trying to open them without the key and by reading the AIP's pointer file. Finally, he wants to be able to download the AIPS via the Archivematica interface and have them be decrypted prior to download.
    Given there is a standard GPG-encrypted space in the storage service
    And there is a standard GPG-encrypted AIP Storage location in the storage service
    And the default processing config is in its default state
    When a transfer is initiated on directory ~/archivematica-sampledata/SampleTransfers/BagTransfer
    And standard AIP-creation decisions are made
    And the user waits for the "Store AIP location" decision point to appear and chooses "Store AIP Encrypted in standard Archivematica Directory" during ingest
    And the user waits for the AIP to appear in archival storage
    And the user downloads the AIP pointer file
    Then the pointer file contains a PREMIS:EVENT element for the encryption event
    And the pointer file contains a mets:transformFile element for the encryption event
    And the AIP on disk is encrypted
    When the user downloads the AIP
    Then the downloaded AIP is not encrypted

  @uncompressed
  Scenario: Richard wants to ensure that he can encrypt uncompressed AIPs.
    Given there is a standard GPG-encrypted space in the storage service
    And there is a standard GPG-encrypted AIP Storage location in the storage service
    And the default processing config is in its default state
    And the processing config decision "Select compression algorithm" is set to "Uncompressed"
    When a transfer is initiated on directory ~/archivematica-sampledata/SampleTransfers/BagTransfer
    And standard AIP-creation decisions are made
    And the user waits for the "Store AIP location" decision point to appear and chooses "Store AIP Encrypted in standard Archivematica Directory" during ingest
    And the user waits for the AIP to appear in archival storage
    Then the uncompressed AIP on disk at /var/archivematica/sharedDirectory/www/AIPsStoreEncrypted/ is encrypted
    When the user downloads the AIP
    Then the downloaded uncompressed AIP is an unencrypted tarfile

  @transfer-backlog
  Scenario: Richard wants to ensure that he can encrypt transfers in backlog.
    Given there is a standard GPG-encrypted space in the storage service
    And the user has disabled the default transfer backlog location
    And there is a standard GPG-encrypted Transfer Backlog location in the storage service
    And the default processing config is in its default state
    When a transfer is initiated on directory ~/archivematica-sampledata/SampleTransfers/BagTransfer
    And the user waits for the "Assign UUIDs to directories?" decision point to appear and chooses "No" during transfer
    And the user waits for the "Select file format identification command" decision point to appear and chooses "Identify using Fido" during transfer
    And the user waits for the "Perform policy checks on originals?" decision point to appear and chooses "No" during transfer
    And the user waits for the "Create SIP(s)" decision point to appear and chooses "Send to backlog" during transfer
    And the user waits for the DIP to appear in transfer backlog
    Then the transfer on disk is encrypted
    # TODO: implement the following steps. Spending time implementing these did
    # not seem justifiable at the present moment.
    # And the files of the encrypted transfer are browseable in the appraisal tab
    # And the files of the encrypted transfer are browseable in the ingest tab
    # And a SIP can be created from the encrypted transfer in backlog

  @allow-passphraseless-key-import
  Scenario: Richard wants to ensure that a passphrase-less GPG key can be imported into the storage service.
    When the user attempts to import GPG key aadams-passphraseless.key
    Then the user succeeds in importing the GPG key aadams

  @prohibit-passphrased-key-import
  Scenario: Richard wants to ensure that a GPG key with a passphrase cannot be imported into the storage service. Keys with passphrases would break the storage service's encryption functionality.
    When the user attempts to import GPG key bbingo-passphrased.key
    Then the user fails to import the GPG key bbingo because it requires a passphrase

  @allow-orphaned-key-delete
  Scenario: Richard wants to ensure that GPG deletion is never permitted if the key is associated to a space or if it is needed to decrypt an existing package. However, if all space associations are destroyed and all dependent packages deleted, then deletion of the (orphaned) key should be permitted.
    Given there is a standard GPG-encrypted space in the storage service
    And there is a standard GPG-encrypted AIP Storage location in the storage service
    And the default processing config is in its default state
    When the user creates a new GPG key and assigns it to the standard GPG-encrypted space
    And an encrypted AIP is created from the directory at ~/archivematica-sampledata/SampleTransfers/BagTransfer
    And the user attempts to delete the new GPG key
    Then the user is prevented from deleting the key because it is attached to a space
    When the user assigns a different GPG key to the standard GPG-encrypted space
    And the user attempts to delete the new GPG key
    Then the user is prevented from deleting the key because it is attached to a package
    When the AIP is deleted
    And the user attempts to delete the new GPG key
    Then the user succeeds in deleting the GPG key

  @reencrypt-different-key
  Scenario: Richard wants to confirm that he can re-encrypt an encrypted AIP with a new key. He has encrypted an AIP with GPG key A in space S. He later changed space S to use the more secure GPG key B. He wants to decrypt the AIPs encrypted with A and re-encrypt them with key B. Finally, he wants to delete the now unused key A from the storage service.
    Given an encrypted AIP in the standard GPG-encrypted space
    And the reminder to add metadata is enabled
    When the user creates a new GPG key and assigns it to the standard GPG-encrypted space
    And the user performs a metadata-only re-ingest on the AIP
    And the user downloads the AIP pointer file
    Then the AIP pointer file references the fingerprint of the new GPG key
