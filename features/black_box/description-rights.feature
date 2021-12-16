@black-box @black-box-metadata
Feature: Alma wants to ensure the AIP METS contains metadata from description and rights CSVs

  Background: metadata.csv and rights.csv are two reserved files that can be associated with a transfer these files contain information that should be transcribed to metadata elements in the METS file in the resulting AIP

  Scenario Outline: Descriptive and rights metadata are listed in the AIP METS and submission documentation is listed correctly
    Given a "standard" transfer type located in "<sample_transfer_path>"
    When the AIP is downloaded
    Then the AIP METS can be accessed and parsed by mets-reader-writer
    And there are <original_object_count> original objects in the AIP METS with a DMDSEC containing DC metadata
    And there are <directory_count> directories in the AIP METS with a DMDSEC containing DC metadata
    And there are <original_object_rights_count> objects in the AIP METS with a rightsMD section containing PREMIS:RIGHTS
    And there are <rights_entries_count> PREMIS:RIGHTS entries
    And there are <submission_documents_count> submission documents listed in the AIP METS as submission documentation

    Examples: sample transfers
      | sample_transfer_path            | original_object_count | directory_count | original_object_rights_count | rights_entries_count | submission_documents_count |
      | SampleTransfers/DemoTransferCSV | 7                     | 1               | 2                            | 8                    | 1                          |
      | SampleTransfers/CSVmultiLevel   | 4                     | 1               | 0                            | 0                    | 0                          |
      | TestTransfers/rightsTransfer    | 0                     | 0               | 2                            | 4                    | 0                          |
