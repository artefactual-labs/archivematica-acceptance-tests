# To run this feature against an indexless Docker compose-based Archivematica
# deploy::
#
#     $ behave -v --tags=indexless \
#           --tags=deploy.method.docker-compose,same-aip,gui
#           --no-skipped \
#           -D am_username=test \
#           -D am_password=test \
#           -D am_url=http://127.0.0.1:62080/ \
#           -D am_version=1.7 \
#           -D am_api_key=test \
#           -D ss_username=test \
#           -D ss_password=test \
#           -D ss_url=http://127.0.0.1:62081/ \
#           -D ss_api_key=test \
#           -D home=archivematica \
#           -D driver_name=Firefox \
#           -D docker_compose_path=/path/to/dir/containing/docker/compose/file

# To run this feature against an indexless Vagrant/Ansible (Ubuntu 14)
# Archivematica deploy::
#
#     $ behave -v --tags=indexless \
#           --tags=deploy.method.ansible,same-aip,gui \
#           --no-skipped \
#           -D am_username=test \
#           -D am_password=testtest \
#           -D am_url=http://192.168.168.192/ \
#           -D am_version=1.7 \
#           -D ss_username=test \
#           -D ss_password=test \
#           -D ss_url=http://192.168.168.192:8000/ \
#           -D home=vagrant \
#           -D driver_name=Firefox \
#           -D server_user=vagrant \
#           -D server_password=vagrant

@indexless @headless
Feature: Archivematica is deployed without Indexing feature
  When deploying Archivematica, users want to be able to decide whether or not
  to install Elasticsearch, and all related components. Installing without
  Elasticsearch allows an Archivematica deployment to consume less compute
  resources and requires less administrative oversight. It is an important
  step towards running a 'headless', completely automated Archivematica.

  @deploy @deploy.method.<method>
  Scenario Outline: Tony wants to deploy a new Archivematica instance without Elasticsearch
    Given Archivematica deployment method <method> which provides an option to exclude Elasticsearch
    When Archivematica is deployed without Elasticsearch using method <method>
    Then the installation has Indexing disabled
    And Elasticsearch is not installed

    # In order to run this scenario against an Archivematica instance deployed
    # with one of the methods below, use the appropriate parametrized behave
    # tag: e.g., to target a manually installed deploy add the tag
    # ``--tags=deploy.method.manual``.
    Examples: Deployment methods
    | method          |
    # A "manual" indexless installation is one that follows the instructions at
    # https://www.archivematica.org/en/docs/archivematica-1.7/admin-manual/installation/installation/#installation
    # and involves installation via packages, i.e., rpm or deb.
    | manual          |
    # An Ansible Archivematica headless deploy can be performed using the
    # playbooks/archivematica-xenia/singlenode-indexless.yml Ansible config file
    # of https://github.com/artefactual/deploy-pub.
    | ansible         |
    # See https://github.com/artefactual-labs/am/blob/master/compose/README.md
    # for how to deploy AM in "headless" mode.
    | docker-compose  |

    # Notes on the above scenario outline:
    # 1. The phrase "has Indexing disabled" means that the AM GUI (in
    #    particular, /administration/general/) indicates that this AM instance
    #    has been deployed with Elasticsearch indexing disabled.
    # 2. The phrase "Elasticsearch is not installed" means that an operating
    #    system command has been issued from the tests (feature) which verifies
    #    that Elasticsearch is not installed.

  @same-aip
  Scenario Outline: Dina wants to create an AIP without indexing it and be assured that it is equivalent to the same AIP created with indexing turned on.
    Given an Archivematica instance with Indexing disabled
    And local indexed AIP at <indexed_AIP> created from <transfer_path> with Indexing enabled
    And a default processing config that creates and stores an AIP
    When a transfer is initiated on directory <transfer_path>
    And the user waits for the "Index AIP" micro-service to complete during ingest
    Then the "Index AIP" micro-service output indicates that no indexing has occurred
    When the user queries the API until the AIP has been stored
    And the user downloads the AIP
    And the user decompresses the AIP
    And the user decompresses the local AIP at <indexed_AIP>
    Then the AIP is identical in all relevant repects to local indexed AIP at <indexed_AIP>

    Examples: Transfer paths and resulting AIPs
    | transfer_path                                              | indexed_AIP          |
    | ~/archivematica-sampledata/SampleTransfers/Images/pictures | etc/aips/pictures.7z |

  @gui
  Scenario Outline: Dina wants to interact with an Archivematica instance with indexing disabled and wants to have a good user experience
    Given an Archivematica instance with Indexing disabled
    And a default processing config that gets a transfer to the "Create SIP(s)" decision point
    When the user navigates to the Archivematica instance
    Then the Backlog tab is not displayed in the navigation bar
    And the Appraisal tab is not displayed in the navigation bar
    And the Archival storage tab is not displayed in the navigation bar
    When the user navigates to the Backlog tab
    Then a warning is displayed indicating that the Backlog tab is not operational
    When the user navigates to the Appraisal tab
    Then a warning is displayed indicating that the Appraisal tab is not operational
    When the user navigates to the Archival storage tab
    Then a warning is displayed indicating that the Archival storage tab is not operational
    When the user navigates to the Ingest tab
    Then the SIP Arrange pane is not displayed
    When processing config decision "Create SIP(s)" is inspected
    Then there is no "Send to backlog" option
    When a transfer is initiated on directory <transfer_path>
    And the user waits for the "Create SIP(s)" decision point to appear during transfer
    Then the "Create SIP(s)" decision point does not have a "Send to backlog" option

    Examples: Transfer paths
    | transfer_path                                          |
    | ~/archivematica-sampledata/SampleTransfers/BagTransfer |
