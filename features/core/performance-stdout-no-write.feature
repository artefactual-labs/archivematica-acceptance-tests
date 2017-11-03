@performance-no-stdout
Feature: Performance increase: stop saving stdout/stderr
  Archivematica's developers want to test whether preventing client scripts
  from sending their stdout and stderr to MCPServer to be saved to the database
  will result in a significant performance increase.

  Scenario: Molly Lou Melon creates an AIP on an Archivematica instance A that saves stdout/err and on one that does not, B. Molly expects that the processing time of the AIP on B will be significantly less than that of the AIP on A.
    Given Archivematica instance A that passes client script output streams to MCPServer
    And Archivematica instance B that does not pass client script output streams to MCPServer
    When an AIP is created on Archivematica instance A
    And the runtime of the client scripts run are summed as RT-CS-A
    When an AIP is created on Archivematica instance B
    And the runtime of the client scripts run are summed as RT-CS-B
    Then RT-CS-B is 50 percent RT-CS-A or less

    # Metrics of performance increase:
    # - increase in number of files processed simultaneously (JGC thinks unlikely)
    # - decrease in total processing time (JGC thinks unlikely)
    # - increase in size of the largest file that can be processed (JGC thinks yes)
