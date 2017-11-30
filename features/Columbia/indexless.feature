@wip @indexing-disabled
Feature: Archivematica is deployed without Indexing feature
  When deploying Archivematica, users want to be able to decide whether or not
  to install Elasticsearch, and all related components.  Installing without
  Elasticsearch allows an Archivematica deployment to consume less compute
  resources and requires less administrative oversight.  It is an important
  step towards running a 'headless', completely automated Archivematica.

  @deploy
  Scenario Outline: Tony wants to deploy a new Archivematica instance without Elasticsearch
    Given Archivematica deployment method <method> which provides an option to exclude Elasticsearch
    When Archivematica is deployed without Elasticsearch using method <method>
    Then the installation has Indexing disabled
    And Elasticsearch is not running
    And Elasticsearch is not installed

    Examples: Deployment methods
    | method          |
    # Installation instructions need to demonstrate how to deploy with and
    # without Elasticsearch. See
    # https://github.com/artefactual/archivematica-docs.
    # | manual          |
    # singlenode-headless.yml script required, which can deploy AM without
    # ES. See https://github.com/artefactual/deploy-pub.
    # | ansible         |
    # Makefile/docker-compose.yml modifications needed so that AM can be
    # deployed without ES. See https://github.com/artefactual-labs/am.
    | docker-compose  |

    # Notes on the above scenario outline:
    # 1. "has Indexing disabled" means that the AM GUI indicates that this AM
    #    instance has been deployed with Elasticsearch indexing disabled.
    # 2. "Elasticsearch is not running" means that an operating system command
    #    has been issued from the tests (feature) which verifies that
    #    Elasticsearch is not running.
    # 3. "Elasticsearch is not installed" means that an operating system
    #    command has been issued from the tests (feature) which verifies that
    #    Elasticsearch is not installed.

  Scenario Outline: Dina wants to create an AIP without indexing it
    Given an Archivematica instance with Indexing disabled
    And local indexed AIP at <indexed_AIP> created from <transfer_path> with Indexing enabled
    And a fully automated default processing config
    When a transfer is initiated on directory <transfer_path>
    And the user waits for the "Index Transfer" micro-service to complete during transfer
    Then the "Index Transfer" micro-service output indicates that no indexing has occurred
    When the user waits for the "Index AIP" micro-service to complete during ingest
    Then the "Index AIP" micro-service output indicates that no indexing has occurred
    When the user queries the API until the AIP has been stored
    And the user downloads the AIP from the storage service
    Then the AIP is identical in all relevant repects to local indexed AIP at <indexed_AIP>

    Examples: Transfer paths and resulting AIPs
    | transfer_path                                              | indexed_AIP          |
    | ~/archivematica-sampledata/SampleTransfers/Images/pictures | etc/aips/pictures.7z |

  Scenario Outline: Dina wants to interact with an Archivematica instance with indexing disabled and wants to have a good user experience
    Given an Archivematica instance with Indexing disabled
    And the default processing config is in its default state
    When the user navigates to the Archivematica instance
    Then the Backlog tab is not displayed in the navigation bar
    And the Appraisal tab is not displayed in the navigation bar
    And the Archival storage tab is not displayed in the navigation bar
    When the user navigates to the Ingest tab
    Then the SIP Arrange pane is not displayed
    When the user edits the default processing configuration
    Then "Create SIP(s)" does not have a "Send to backlog" option
    When a transfer is initiated on directory <transfer_path>
    And the user waits for the "Create SIP(s)" decision point to appear during transfer
    Then the "Create SIP(s)" decision point does not have a "Send to backlog" option

    Examples: Transfer paths
    | transfer_path                                          |
    | ~/archivematica-sampledata/SampleTransfers/BagTransfer |
