# Default values
# =========================================================================

DEFAULT_AM_USERNAME = "test"
DEFAULT_AM_PASSWORD = "testtest"
DEFAULT_AM_URL = "http://192.168.168.192/"
DEFAULT_AM_VERSION = "1.6"
DEFAULT_SS_USERNAME = "test"
DEFAULT_SS_PASSWORD = "test"
DEFAULT_SS_URL = "http://192.168.168.192:8000/"
DEFAULT_AM_API_KEY = None
DEFAULT_SS_API_KEY = None
DEFAULT_DRIVER_NAME = "Chrome"  # 'Firefox' should also work.
DUMMY_VAL = "Archivematica Acceptance Test"
METADATA_ATTRS = ("title", "creator")
JOB_OUTPUTS_COMPLETE = ("Failed", "Completed successfully", "Awaiting decision")
TMP_DIR_NAME = ".amsc-tmp"
PERM_DIR_NAME = "data"


# CSS classes and selectors
# =========================================================================

# CSS class of the "Add" links in the AM file explorer.
CLASS_ADD_TRANSFER_FOLDER = "backbone-file-explorer-directory_entry_actions"
# CSS selector for the <div> holding an entire transfer.
SELECTOR_TRANSFER_DIV = "div.sip"
# CSS selector for the <div> holding the gear icon, the roport icon, etc.
SELECTOR_TRANSFER_ACTIONS = "div.job-detail-actions"
SELECTOR_INPUT_TRANSFER_NAME = 'input[ng-model="vm.transfer.name"]'
SELECTOR_INPUT_TRANSFER_TYPE = 'select[ng-model="vm.transfer.type"]'
SELECTOR_INPUT_TRANSFER_ACCESSION = 'input[ng-model="vm.transfer.accession"]'
SELECTOR_DIV_TRANSFER_SOURCE_BROWSE = "div.transfer-tree-container"
SELECTOR_BUTTON_ADD_DIR_TO_TRANSFER = "button.pull-right[type=submit]"
SELECTOR_BUTTON_BROWSE_TRANSFER_SOURCES = 'button[data-target="#transfer_browse_tree"]'
SELECTOR_BUTTON_START_TRANSFER = 'button[ng-click="vm.transfer.start()"]'
SELECTOR_SS_LOGIN_BUTTON = "input[value=login]"
SELECTOR_SS_LOGIN_BUTTON_1_7 = 'input[value="Log in"]'
SELECTOR_DFLT_SS_REG = "input[name=use_default]"
SELECTOR_DFLT_SS_REG_1_7 = "input[type=submit]"


# XPATHS
# =========================================================================

# This is used to join folder-matching XPaths. So that
# 'vagrant/archivematica-sampledata' can be matched by getting an XPath
# that matches each folder name and joins them according to the DOM
# structure of the file browser.
XPATH_TREEITEM_NEXT_SIBLING = "/following-sibling::treeitem/ul/li/"


# UUIDs
# =========================================================================

# UUIDs for various "Approve transfer" options
APPROVE_STANDARD_TRANSFER_UUID = "6953950b-c101-4f4c-a0c3-0cd0684afe5e"
APPROVE_ZIPPED_BAGIT_TRANSFER_UUID = "167dc382-4ab1-4051-8e22-e7f1c1bf3e6f"


def varvn(varname, vn):
    """Return global var/constant named ``varname`` for version ``vn``, if it
    exists, else return global ``varname``. E.g.,
    ``varvn('SELECTOR_SS_LOGIN_BUTTON', '1.7')`` will return
    ``SELECTOR_SS_LOGIN_BUTTON_1_7`` if it exists, else
    `SELECTOR_SS_LOGIN_BUTTON``.
    """
    return globals().get(
        "{}_{}".format(varname, vn.replace(".", "_")),
        globals().get(varname, "There is no var {}".format(varname)),
    )


# A map from each micro-service name (i.e., description) to the tuple of
# micro-service groups that it belongs to.
MICRO_SERVICES2GROUPS = {
    "Add processed structMap to METS.xml document": ("Update METS.xml document",),
    "Approve AIP reingest": ("Reingest AIP",),
    "Approve normalization": ("Normalize",),
    "Approve normalization (review)": ("Normalize",),
    "Approve normalization Review": ("Normalize",),
    "Approve standard transfer": ("Approve transfer",),
    "Assign checksums and file sizes to metadata": ("Process metadata directory",),
    "Assign checksums and file sizes to objects": ("Assign file UUIDs and checksums",),
    "Assign checksums and file sizes to submissionDocumentation": (
        "Process submission documentation",
    ),
    "Assign file UUIDs to metadata": ("Process metadata directory",),
    "Assign file UUIDs to objects": ("Assign file UUIDs and checksums",),
    "Assign file UUIDs to submission documentation": (
        "Process submission documentation",
    ),
    "Assign UUIDs to directories?": ("Assign file UUIDs and checksums",),
    "Attempt restructure for compliance": ("Verify transfer compliance",),
    "Bind PIDs?": ("Bind PIDs",),
    "Characterize and extract metadata": ("Characterize and extract metadata",),
    "Characterize and extract metadata on metadata files": (
        "Process metadata directory",
    ),
    "Characterize and extract metadata on submission documentation": (
        "Process submission documentation",
    ),
    "Check for Access directory": ("Normalize",),
    "Check for Service directory": ("Normalize",),
    "Check for manual normalized files": ("Process manually normalized files",),
    "Check for specialized processing": ("Examine contents",),
    "Check for submission documentation": ("Process submission documentation",),
    "Check if AIP is a file or directory": ("Prepare AIP",),
    "Check if DIP should be generated": ("Prepare AIP",),
    "Check if SIP is from Maildir Transfer": ("Rename SIP directory with SIP UUID",),
    "Check transfer directory for objects": ("Create SIP from Transfer",),
    "Compress AIP": ("Prepare AIP",),
    "Copy submission documentation": ("Prepare AIP",),
    "Copy transfer submission documentation": ("Process submission documentation",),
    "Copy transfers metadata and logs": ("Process metadata directory",),
    "Create AIP Pointer File": ("Prepare AIP",),
    "Create SIP from transfer objects": ("Create SIP from Transfer",),
    "Create SIP(s)": ("Create SIP from Transfer",),
    "Create thumbnails directory": ("Normalize",),
    "Create transfer metadata XML": ("Complete transfer",),
    "Designate to process as a standard transfer": ("Quarantine",),
    "Determine if transfer contains packages": ("Extract packages",),
    "Determine which files to identify": ("Identify file format",),
    "Do you want to perform file format identification?": (
        "Identify file format",
        "Process submission documentation",
    ),
    "Document empty directories?": ("Generate AIP METS",),
    "Examine contents?": ("Examine contents",),
    "Find type to process as": ("Quarantine",),
    "Generate METS.xml document": ("Generate METS.xml document", "Generate AIP METS"),
    "Generate transfer structure report": ("Generate transfer structure report",),
    "Grant normalization options for no pre-existing DIP": ("Normalize",),
    "Identify file format": (
        "Identify file format",
        "Normalize",
        "Process submission documentation",
    ),
    "Identify file format of metadata files": ("Process metadata directory",),
    "Identify manually normalized files": ("Normalize",),
    "Index AIP": ("Store AIP",),
    "Include default SIP processingMCP.xml": ("Include default SIP processingMCP.xml",),
    "Include default Transfer processingMCP.xml": (
        "Include default Transfer processingMCP.xml",
    ),
    "Load Dublin Core metadata from disk": ("Clean up names",),
    "Load labels from metadata/file_labels.csv": ("Characterize and extract metadata",),
    "Load options to create SIPs": ("Create SIP from Transfer",),
    "Move metadata to objects directory": ("Process metadata directory",),
    "Move submission documentation into objects directory": (
        "Process submission documentation",
    ),
    "Move to SIP creation directory for completed transfers": (
        "Create SIP from Transfer",
        "Complete transfer",
    ),
    "Move to approve normalization directory": ("Normalize",),
    "Move to compressionAIPDecisions directory": ("Prepare AIP",),
    "Move to examine contents": ("Examine contents",),
    "Move to extract packages": ("Extract packages",),
    "Move to generate transfer tree": ("Generate transfer structure report",),
    "Move to metadata reminder": ("Add final metadata",),
    "Move to processing directory": (
        "Verify transfer compliance",
        "Generate transfer structure report",
        "Scan for viruses",
        "Create SIP from Transfer",
        "Verify SIP compliance",
        "Normalize",
    ),
    "Move to select file ID tool": ("Identify file format", "Normalize"),
    "Move to the store AIP approval directory": ("Store AIP",),
    "Move to workFlowDecisions-quarantineSIP directory": ("Quarantine",),
    "Normalization report": ("Normalize",),
    "Normalize": ("Normalize",),
    "Normalize for preservation": ("Normalize",),
    "Normalize for thumbnails": ("Normalize",),
    "Perform policy checks on access derivatives?": ("Policy checks for derivatives",),
    "Perform policy checks on originals?": ("Validation",),
    "Perform policy checks on preservation derivatives?": (
        "Policy checks for derivatives",
    ),
    "Policy checks for access derivatives": ("Policy checks for derivatives",),
    "Policy checks for originals": ("Validation",),
    "Policy checks for preservation derivatives": ("Policy checks for derivatives",),
    "Prepare AIP": ("Prepare AIP",),
    "Process JSON metadata": ("Process metadata directory",),
    "Process transfer JSON metadata": ("Reformat metadata files",),
    "Relate manual normalized preservation files to the original files": (
        "Process manually normalized files",
    ),
    "Reminder: add metadata if desired": ("Add final metadata",),
    "Remove cache files": ("Remove cache files",),
    "Remove empty manual normalization directories": ("Process metadata directory",),
    "Remove files without linking information (failed normalization"
    " artifacts etc.)": ("Process submission documentation", "Normalize"),
    "Remove from quarantine": ("Quarantine",),
    "Remove hidden files and directories": ("Verify transfer compliance",),
    "Remove the processing directory": ("Store AIP",),
    "Remove unneeded files": ("Verify transfer compliance",),
    "Removed bagged files": ("Prepare AIP",),
    "Rename SIP directory with SIP UUID": ("Rename SIP directory with SIP UUID",),
    "Rename with transfer UUID": ("Rename with transfer UUID",),
    "Resume after normalization file identification tool selected.": ("Normalize",),
    "Retrieve AIP Storage Locations": ("Store AIP",),
    "Sanitize SIP name": ("Clean up names",),
    "Sanitize Transfer name": ("Clean up names",),
    "Sanitize file and directory names in metadata": ("Process metadata directory",),
    "Sanitize file and directory names in submission documentation": (
        "Process submission documentation",
    ),
    "Sanitize object's file and directory names": ("Clean up names",),
    "Scan for viruses": ("Scan for viruses",),
    "Scan for viruses in metadata": ("Process metadata directory",),
    "Scan for viruses in submission documentation": (
        "Process submission documentation",
    ),
    "Select compression algorithm": ("Prepare AIP",),
    "Select compression level": ("Prepare AIP",),
    "Select pre-normalize file format identification command": ("Normalize",),
    "Serialize Dublin Core metadata to disk": ("Create SIP from Transfer",),
    "Set bag file permissions": ("Prepare AIP",),
    "Set file permissions": (
        "Assign file UUIDs and checksums",
        "Normalize",
        "Add final metadata",
        "Clean up names",
        "Verify transfer compliance",
        "Verify SIP compliance",
        "Prepare AIP",
    ),
    "Set remove preservation and access normalized files to renormalize link.": (
        "Normalize",
    ),
    "Set transfer type: Standard": ("Verify transfer compliance",),
    "Store AIP": ("Store AIP",),
    "Store AIP (review)": ("Store AIP",),
    "Store AIP Review": ("Store AIP",),
    "Store AIP location": ("Store AIP",),
    "Transcribe": ("Transcribe SIP contents",),
    "Transcribe SIP contents": ("Transcribe SIP contents",),
    "Upload DIP": ("Upload DIP",),
    "Validate formats": ("Validation",),
    "Validate access derivatives": ("Normalize",),
    "Validate preservation derivatives": ("Normalize",),
    "Verify SIP compliance": ("Verify SIP compliance",),
    "Verify checksums generated on ingest": ("Verify checksums",),
    "Verify metadata directory checksums": ("Verify transfer checksums",),
    "Verify mets_structmap.xml compliance": (
        "Verify transfer compliance",
        "Verify transfer compliance",
    ),
    "Verify transfer compliance": ("Verify transfer compliance",),
    "Workflow decision - send transfer to quarantine": ("Quarantine",),
}

# The following JavaScript run in the browser console will create an object
# mapping all (run) micro-service names to their micro-service group names.
JS_SNIPPET_GET_MICRO_SERVICES2GROUPS = """
    var map_ = {};
    $('div.sip').first().find('div.microservicegroup').each(function(){
        var group = $(this).find(
            'span.microservice-group-name').text().replace(
            'Micro-service: ', '');
        var children = $(this).children();
        if (!$(children[1]).is(':visible')) { children[0].click() }
        $(children[1]).find('div.job').each(function(){
            var ms = $(this).find(
                'div.job-detail-microservice span[title]').text();
            if (map_.hasOwnProperty(ms)) {
                console.log(
                    ms + ' is a DUPLICATE!: ' + group + ' and ' + map_[ms]);
            } else {
                map_[ms] = group;
            }
        });
    });
    console.log(JSON.stringify(map_, undefined, 2));"""


# Maps processing config decision labels to the HTML ids of the
# <select>/<input> elements that control those decisions in the processing
# config edit interface.
PC_DECISION2ID = {
    "Assign UUIDs to directories": "id_bd899573-694e-4d33-8c9b-df0af802437d",
    "Document empty directories": "id_d0dfa5fc-e3c2-4638-9eda-f96eea1070e0",
    "Bind PIDs": "id_05357876-a095-4c11-86b5-a7fff01af668",
    "Send transfer to quarantine": "id_755b4177-c587-41a7-8c52-015277568302",
    "Perform policy checks on access derivatives": "id_8ce07e94-6130-4987-96f0-2399ad45c5c2",
    "Perform policy checks on preservation derivatives": "id_153c5f41-3cfb-47ba-9150-2dd44ebc27df",
    "Perform policy checks on originals": "id_70fc7040-d4fb-4d19-a0e6-792387ca1006",
    "Remove from quarantine after (days)": "id_19adb668-b19a-4fcb-8938-f49d7485eaf3",
    "Generate transfer structure report": "id_56eebd45-5600-4768-a8c2-ec0114555a3d",
    "Select file format identification command (Transfer)": "id_f09847c2-ee51-429a-9478-a860477f6b8d",
    "Extract packages": "id_dec97e3c-5598-4b99-b26e-f87a435a6b7f",
    "Delete packages after extraction": "id_f19926dd-8fb5-4c79-8ade-c83f61f55b40",
    "Examine contents": "id_accea2bf-ba74-4a3a-bb97-614775c74459",
    "Create SIP(s)": "id_bb194013-597c-4e4a-8493-b36d190f8717",
    "Select file format identification command (Ingest)": "id_7a024896-c4f7-4808-a240-44c87c762bc5",
    "Normalize": "id_cb8e5706-e73f-472f-ad9b-d1236af8095f",
    "Approve normalization": "id_de909a42-c5b5-46e1-9985-c031b50e9d30",
    "Reminder: add metadata if desired": "id_eeb23509-57e2-4529-8857-9d62525db048",
    "Transcribe files (OCR)": "id_7079be6d-3a25-41e6-a481-cee5f352fe6e",
    "Select file format identification command "
    "(Submission documentation & metadata)": "id_087d27be-c719-47d8-9bbb-9a7d8b609c44",
    "Select compression algorithm": "id_01d64f58-8295-4b7b-9cab-8f1b153a504f",
    "Select compression level": "id_01c651cb-c174-4ba4-b985-1d87a44d6754",
    "Store AIP": "id_2d32235c-02d4-4686-88a6-96f4d6c7b1c3",
    "Store AIP location": "id_b320ce81-9982-408a-9502-097d0daa48fa",
    "Store DIP": "id_5e58066d-e113-4383-b20b-f301ed4d751c",
    "Store DIP location": "id_cd844b6e-ab3c-4bc6-b34f-7103f88715de",
    "Upload DIP": "id_92879a29-45bf-4f0b-ac43-e64474f0f2f9",
    "Generate thumbnails": "id_498f7a6d-1b8c-431a-aa5d-83f14f3c5e65",
}

# Namespace map for parsing METS XML.
METS_NSMAP = {
    "mets": "http://www.loc.gov/METS/",
    "premis": "info:lc/xmlns/premis-v2",
    "premis3": "http://www.loc.gov/premis/v3",
    "dc": "http://purl.org/dc/elements/1.1/",
    "dcterms": "http://purl.org/dc/terms/",
    "xlink": "http://www.w3.org/1999/xlink",
}


# Waits and Timeouts
# =========================================================================
#
# Note that there is redundancy between this and the configuration in
# features/environment.py. These values are specified here also so that
# ``ArchivematicaUser`` can technically remain independent of its use within a
# ``behave`` feature-running context. The proper way to customize these values
# when using ``behave`` is to use Behave "user data" flags, e.g.,
# ``behave -D nihilistic_wait=30``.

WAIT_FACTOR = 4

# Generable, reusable wait times, in seconds
NIHILISTIC_WAIT = WAIT_FACTOR * 20
APATHETIC_WAIT = WAIT_FACTOR * 10
PESSIMISTIC_WAIT = WAIT_FACTOR * 5
MEDIUM_WAIT = WAIT_FACTOR * 3
OPTIMISTIC_WAIT = WAIT_FACTOR * 1
QUICK_WAIT = WAIT_FACTOR * 0.5
MICRO_WAIT = WAIT_FACTOR * 0.25

# Use-case-specific maximum attempt counters
MAX_CLICK_TRANSFER_DIRECTORY_ATTEMPTS = 5
MAX_CLICK_AIP_DIRECTORY_ATTEMPTS = 5
MAX_NAVIGATE_AIP_ARCHIVAL_STORAGE_ATTEMPTS = 10
MAX_DOWNLOAD_AIP_ATTEMPTS = 20
MAX_CHECK_AIP_STORED_ATTEMPTS = 60
MAX_CHECK_METS_LOADED_ATTEMPTS = 60
MAX_SEARCH_AIP_ARCHIVAL_STORAGE_ATTEMPTS = 120
MAX_SEARCH_DIP_BACKLOG_ATTEMPTS = 120
MAX_CHECK_TRANSFER_APPEARED_ATTEMPTS = 1000
MAX_CHECK_FOR_MS_GROUP_ATTEMPTS = 7200
