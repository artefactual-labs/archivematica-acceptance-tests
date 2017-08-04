@pid-binding @dev
Feature: Archivematica's entities can be assigned PIDs with specified resolution properties.
  Users of Archivematica want to be able to generate Persistent IDentifiers
  (PIDs)---in this case Handle System handles---for Files and SIP/DIPs (and
  possibly also Directories) processed by Archivematica. The PIDs are based on
  the UUIDs of the respective entity, i.e., "hdl:<NAMING_AUTHORITY>/<UUID>.
  Archivematica should document both the PIDs and the derivable PURLs as
  premis:objectIdentifierType in the MET file of the DIP/AIP. The user should
  be able to configure Archivematica so that the PID URL (PURL) of an
  Archivematica-processed entity will resolve to particular resolve URLs. In
  addition, it should be possible to set *qualified* PURLs (e.g., with GET
  query params appended) to resolve to distinct URLs (e.g., derivatives).
  # NOTE: The SOAP/HTTP API that this last feature is implemented against may
  # be highly idiosyncratic.

  @typical
  Scenario Outline: Lucien wants to create an AIP with a METS file that documents the binding of persistent identifiers to all of the AIP's original files and directories, and to the AIP itself.
    Given a fully automated default processing config
    And default processing configured to assign UUIDs to directories
    And default processing configured to bind PIDs
    And a Handle server client configured to create qualified PURLs
    And a Handle server client configured to use the accession number as the PID for the AIP
    When a transfer is initiated on directory <directory_path> with accession number <accession_no>
    And the user waits for the "Store AIP (review)" decision point to appear during ingest
    Then the AIP METS file documents PIDs, PURLs, and UUIDs for all files, directories and the package itself

    Examples: transfer sources
    | directory_path                                                                                 | accession_no |
    | ~/archivematica-sampledata/TestTransfers/acceptance-tests/pid-binding/hierarchy-with-empty-dir | 42           |
