import os
from pathlib import Path

from behave import then
from behave.runner import Context

from features.steps import utils


@then(
    "the AIP bag manifest file contains checksums for all files present in AIP payload"
)
def step_impl(context: Context) -> None:
    assert utils.validate_bag(context.current_transfer["extracted_aip_dir"])


@then("the checksum documents from the transfer persist to the AIP")
def step_impl(context: Context) -> None:
    transfer_metadata_path = Path(context.current_transfer["transfer_path"], "metadata")
    transfer_metadata_path_browse_result = utils.browse_default_ts_location(
        context.api_clients_config, str(transfer_metadata_path)
    )
    if entries := transfer_metadata_path_browse_result.get("entries"):
        if transfer_checkum_files := set(entries).intersection(
            {
                str(Path("checksum").with_suffix(f"{os.extsep}{extension}"))
                for extension in ["md5", "sha1", "sha256", "sha512"]
            }
        ):
            aip_metadata_path = Path(
                context.current_transfer["extracted_aip_dir"],
                "data",
                "objects",
                "metadata",
                "transfers",
                f"{context.current_transfer['transfer_name']}-{context.current_transfer['transfer_uuid']}",
            )
            assert aip_metadata_path.is_dir(), (
                "AIP does not contain a metadata directory"
            )
            errors = []
            for checksum_file in transfer_checkum_files:
                if not Path(aip_metadata_path, str(checksum_file)).exists():
                    errors.append(
                        f"checksum file {checksum_file} is missing in the AIP"
                    )
            assert not errors, "\n".join(errors)
