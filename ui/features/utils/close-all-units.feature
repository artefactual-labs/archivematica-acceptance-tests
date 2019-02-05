@close-all-units
Feature: The user can close all units
  Archivematica users want to be able to close all units. Note that this is not
  really a test; it is a feature that is useful during the running and
  development of tests, i.e., the ability to close a bunch of units, i.e.,
  transfers or ingests. Note also that with Archivematica 1.7 this feature
  should no longer be needed because the dashboard will have "close all
  transfers" and "close all ingests" buttons.

  @close-all-transfers
  Scenario: Isla wants to close all transfers
  When the user closes all transfers

  @close-all-ingests
  Scenario: Isla wants to close all ingests
  When the user closes all ingests
