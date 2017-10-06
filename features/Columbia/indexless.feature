Feature: Archivematica is deployed without Indexing feature
  When deploying Archivematica, users want to be able to decide whether or not
  to install ElasticSearch, and all related components.  Installing without 
  ElasticSearch allows an Archivematica deployment to consume less compute
  resources and requires less administrative oversight.  It is an important 
  step towards running a 'headless', completely automated Archivematica.

  Scenario: Tony wants to deploy a new Archivematica instance without Elasticsearch
    Given an Archivematica deployment method
    When Tony chooses not to include the Indexing Feature
    Then the deployment method provides an option to exclude Elasticsearch
    And the installation has Indexing disabled
    And Elasticsearch is not running
    And Elasticsearch is not installed.

#| method | repository | change |
#| manual | archivematica-docs | Installation instructions need to demonstrate how to deploy with and without ElasticSearch |
#| ansible | deploy-pub | singlenode-headless.yml script required - showing how to deploy without ES |

# indexing disabled = ElasticSearchDisabled configuration paramter is set
# Elasticsearch is not running = operating system command to verify elasticsearch is not running
# Elasticsearch is not installed = operating system command to verify package is not installed 

  Scenario: Dina wants to run a create an AIP without indexing it
    Given an Archivematica instance with Indexing disabled
    And a fully automated default processing config
    When a transfer is initiated on a <sample  directory>
    And the user waits for the "Store AIP (review)" decision point to appear during ingest
    Then the 'Index Transfer' microservice is not run
    And the 'Index AIP' microservice is not run
    And the AIP is identical to an <AIP> made from the same sample directory when Indexing is enabled.

# microservices are listed on the metadata page of transfer and ingest

| sample directory | AIP |
| ~/archivematica-sampledata/SampleTransfers/Images/Pictures | ~/archivematica-sampledata/SampleAIPs/Pictures.7z |
