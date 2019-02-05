# Upgrading a Headless deploy of Archivematica

@headless-upgrade @unexecutable
Feature: Upgrade Headless Archivematica
  When upgrading, Archivematica users want to be able to decide whether or not
  to include Elasticsearch, and all related components.

  Scenario Outline: Tony wants to upgrade to a new version of Archivematica without Elasticsearch
    Given an Archivematica upgrade method <method>
    When Archivematica is upgraded without Elasticsearch using method <method>
    Then the upgraded Archivematica instance has indexing disabled
    And Elasticsearch is not installed

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
