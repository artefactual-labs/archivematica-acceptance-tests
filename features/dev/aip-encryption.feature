@aip-encrypt @dev
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
    And the user waits for the "Select file format identification command" decision point to appear and chooses "Identify using Fido" during transfer
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
