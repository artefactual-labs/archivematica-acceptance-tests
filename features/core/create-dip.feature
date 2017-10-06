@dips
Feature: DIPs are created correctly
  Users of Archivematica want to be able to create Dissemination Information
  Packages (DIPs).

  @standard
  Scenario: Isla wants to create an AIP and a DIP.
  Given a default processing config that creates an AIP and a DIP
  When a transfer is initiated on directory ~/archivematica-sampledata/SampleTransfers/BagTransfer
  And the user waits for the "Store AIP (review)" decision point to appear during ingest
