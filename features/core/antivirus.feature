@wip @am17 @antivirus
Feature: Antivirus (AV) in Archivematica
Scenario Outline: Alma wants to unambiguously identify the existence or non-existence of viruses in files being transferred.
    Given the user has configured <Tool> antivirus.
    And they are transferring a file <File Size> in size that is <Clean or Contains Virus>
    And they have set a <Max Size Threshold> threshold.
    Then the virus scanner will return a result of <Result>.
    And <Number of Premis Events> PREMIS EVENTS will be recorded for that Event.
    When an EVENT is created 
    Then it will reflect an ourcome of <Result>. 

    # PREMIS 3.0 notes that recording an event for AV is good for management purposes
    # but there are a handful of tensions in this scenario. The scanner currently only 
	# scans a maximum of xM as its threshold. Beyond that if there is still a virus the
    # determination of there being a virus is technically 'undetermined', not PASS or FAIL. 

	# Rather than reporting a 'untruth' that the file was 'scanned' whatever the outcome
	# We want to make it as clear as possible with this feature that Alma will not see a
	# PREMIS event created if the configuration asks for an AIP to be created.  

    Examples: File Configurations (Without Viruses)
        # There are a handful of file configurations and PREMIS outcomes. Threshold is a custom
        # value and so can be any value. Threshold and file size are indicative of testing
        # small files (assumption, likely to contain viruses), larger files, and large files 
        # (assumption, less likely to contain viruses)

        # Limits below are at time of writing 2017-11-17 based on the understanding of various
        # limits of the Clamscan Antivirus suite. A 2GB limit is documented as a bug officially
        # here (closed forum): https://github.com/artefactual-labs/archivematica-acceptance-tests/issues/36#issuecomment-344803559 
        # and as part of the Archivematica Acceptance Tests repository:
        # here: https://github.com/artefactual-labs/archivematica-acceptance-tests/issues/36#issuecomment-344803559  
        # Users should keep in mind the matrix below and observe the impact of attempting to transfer files over 2GB
		# i.e. no PREMIS event will be created, and the file cannot be guaranteed to be malware free

        | Tool      | File Size | Clean or Contains Virus | Max Size Threshold | Result    | Number of Premis Events |  
        | Clamscan  | Any       | Clean                   | 0                  | OK        | 0                       | 
        | Clamscan  | <25M      | Clean                   | 25M                | OK        | 1                       | 
        | Clamscan  | >25M <2GB | Clean                   | 25M                | OK        | 0                       | 
        | Clamscan  | >=2GB     | Clean                   | 2GB                | OK        | 0                       |    
        | Clamdscan | Any       | Clean                   | 0                  | OK        | 0                       | 
        | Clamdscan | <25M      | Clean                   | 25M                | OK        | 1                       | 
        | Clamdscan | >25M <2GB | Clean                   | 25M                | OK        | 0                       | 
        | Clamdscan | >=2GB     | Clean                   | 2GB                | OK        | 0                       |    

    Examples: File Configurations (With Viruses)
        # There are a handful of file configurations and PREMIS outcomes. Threshold is a custom
        # value and so can be any value. Threshold and file size are indicative of testing
        # small files (assumption, likely to contain viruses), larger files, and large files 
        # (assumption, less likely to contain viruses)

        # Limits below are at time of writing 2017-11-17 based on the understanding of various
        # limits of the Clamscan Antivirus suite. A 2GB limit is documented as a bug officially
        # here (closed forum): https://github.com/artefactual-labs/archivematica-acceptance-tests/issues/36#issuecomment-344803559 
        # and as part of the Archivematica Acceptance Tests repository:
        # here: https://github.com/artefactual-labs/archivematica-acceptance-tests/issues/36#issuecomment-344803559  
        # Users should keep in mind the matrix below and observe the impact of attempting to transfer files over 2GB
		# i.e. no PREMIS event will be created, and the file cannot be guaranteed to be malware free

        | Tool      | File Size | Clean or Contains Virus | Max Size Threshold | Result    | Number of Premis Events |  
        | Clamscan  | Any       | Containing Virus        | 0                  | OK        | 0                       |
        | Clamscan  | <=25M     | Containing Virus        | 25M                | FOUND     | 1                       |
        | Clamscan  | >25M <2GB | Containing Virus        | 25M                | OK        | 0                       |
        | Clamscan  | >=2GB     | Containing Virus        | 2GB                | OK        | 0                       |
        | Clamdscan | Any       | Containing Virus        | 0                  | OK        | 0                       |    
        | Clamdscan | <=25M     | Containing Virus        | 25M                | FOUND     | 1                       |
        | Clamdscan | >25M <2GB | Containing Virus        | 25M                | OK        | 0                       |
        | Clamdscan | >=2GB     | Containing Virus        | 2GB                | OK        | 0                       |    

# Viruses are not always undesirable in a transfer, e.g. the Malware Museum, https://archive.org/details/malwaremuseum 
# Archivematica Use-case: https://groups.google.com/d/msg/archivematica/VNGduykpT00/-NuJtv-jBgAJ

@wip @future @antivirus
Scenario Outline: Alma wants to have the option of what to do when a virus is discovered during transfer
    Given a virus or viruses are discovered in an accession during transfer
    And the user has opted to <Handling Option> viruses
    Then the transfer is <Managed> 
    And the accession is <Progression Option>

    Examples: Place in workflow
        # There are two main points in the workflow Alma wants the option
        # 'Progressed to Ingest' is indicative of the creation of an AIP regardless of the virus
        
        | Handling Option | Managed                  | Progression Option   |
        | Manually Accept | Halted                   | Progressed to Ingest |
        | Manually Reject | Halted                   | Rejected             |
        | Reject          | Halted                   | Rejected             |
        | Accept          | Progressed Automatically | Progressed to Ingest |

