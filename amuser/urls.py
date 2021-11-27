# -*- coding: utf-8 -*-

"""URLS used across the AMAUAT suite plus getters to help retrieve those values
consistently in tests.
"""

AM_URLS = (
    ("get_admin_general_url", "{}administration/general/"),
    ("get_aip_in_archival_storage_url", "{}archival-storage/{}/"),
    ("get_archival_storage_url", "{}archival-storage/"),
    ("get_create_command_url", "{}fpr/fpcommand/create/"),
    ("get_create_rule_url", "{}fpr/fprule/create/"),
    (
        "get_edit_default_processing_config_url",
        "{}administration/processing/edit/default/",
    ),
    (
        "get_reset_default_processing_config_url",
        "{}administration/processing/reset/default/",
    ),
    ("get_handle_config_url", "{}administration/handle/"),
    ("get_ingest_url", "{}ingest/"),
    ("get_installer_welcome_url", "{}installer/welcome/"),
    ("get_login_url", "{}administration/accounts/login/"),
    ("get_metadata_add_url", "{}ingest/{}/metadata/add/"),
    ("get_normalization_report_url", "{}ingest/normalization-report/{}/"),
    ("get_normalization_rules_url", "{}fpr/fprule/normalization/"),
    ("get_policies_url", "{}administration/policies/"),
    ("get_preservation_planning_url", "{}fpr/format/"),
    ("get_rules_url", "{}fpr/fprule/"),
    ("get_storage_setup_url", "{}installer/storagesetup/"),
    ("get_tasks_url", "{}tasks/{}/"),
    ("get_transfer_backlog_url", "{}backlog/"),
    ("get_appraisal_url", "{}appraisal/"),
    ("get_transfer_url", "{}transfer/"),
    ("get_validation_commands_url", "{}fpr/fpcommand/validation/"),
    ("get_aip_preview_url", "{}ingest/preview/aip/{}"),
)

SS_URLS = (
    ("get_create_gpg_key_url", "{}administration/keys/create/"),
    ("get_default_ss_user_edit_url", "{}administration/users/1/edit/"),
    ("get_gpg_keys_url", "{}administration/keys/"),
    ("get_import_gpg_key_url", "{}administration/keys/import/"),
    ("get_location_url", "{}locations/{}/"),
    ("get_locations_url", "{}locations/"),
    ("get_locations_create_url", "{}spaces/{}/location_create/"),
    ("get_packages_url", "{}packages/"),
    ("get_space_url", "{}spaces/{}/"),
    ("get_space_edit_url", "{}spaces/{}/edit/"),
    ("get_spaces_url", "{}spaces/"),
    ("get_spaces_create_url", "{}spaces/create/"),
    ("get_ss_login_url", "{}login/"),
    ("get_ss_package_delete_request_url", "{}packages/package_delete_request/"),
    ("get_ss_users_url", "{}administration/users/"),
)
