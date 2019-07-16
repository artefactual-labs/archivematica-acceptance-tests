"""Archivematica METS Ability.

This module contains the ``ArchivematicaMETSAbility`` class, which represents an
Archivematica user's ability to interact with METS XML files.
"""

import os

from . import base
from . import constants as c
from . import utils


class ArchivematicaMETSAbility(base.Base):
    """Represents an Archivematica user's ability to interact with METS XML
    files.
    """

    mets_nsmap = c.METS_NSMAP

    @staticmethod
    def get_premis_events(mets):
        """Return all PREMIS events in ``mets`` (lxml.etree parse) as a list of
        dicts.
        """
        result = []
        for premis_event_el in mets.findall(".//premis3:event", c.METS_NSMAP):
            result.append(
                {
                    "event_type": premis_event_el.find(
                        "premis3:eventType", c.METS_NSMAP
                    ).text,
                    "event_detail": premis_event_el.find(
                        "premis3:eventDetailInformation/premis3:eventDetail",
                        c.METS_NSMAP,
                    ).text,
                    "event_outcome": premis_event_el.find(
                        "premis3:eventOutcomeInformation/premis3:eventOutcome",
                        c.METS_NSMAP,
                    ).text,
                    "event_outcome_detail_note": premis_event_el.find(
                        "premis3:eventOutcomeInformation"
                        "/premis3:eventOutcomeDetail"
                        "/premis3:eventOutcomeDetailNote",
                        c.METS_NSMAP,
                    ).text,
                }
            )
        return result

    @staticmethod
    def validate_mets_for_pids(mets_doc, accession_no=None):
        """Validate that the METS XML file represented by ``lxml.Element`` instance
        ``mets_doc`` has PIDs and PURLs for all files, directories and for the AIP
        itself. If ``accession_no`` is provided, assert that the PID for the AIP
        directory is the accession number.
        """
        entities = _get_mets_entities(mets_doc, ns=c.METS_NSMAP)
        for entity in entities:
            if entity["name"] == "objects":
                continue
            # All entities have an id, i.e., DMDID or ADMID
            assert entity.get(
                "id"
            ), "Unable to find a DMDID/ADMID for entity" " {}".format(entity["path"])
            purls = []
            # All entities should have the following types of identifier
            for idfr_type in ("UUID", "hdl", "URI"):
                try:
                    idfr = [x for x in entity["identifiers"] if x[0] == idfr_type][0][1]
                except IndexError:
                    idfr = None
                assert idfr, (
                    "Unable to find an identifier of type {} for entity"
                    " {}".format(idfr_type, entity["path"])
                )
                if idfr_type == "UUID":
                    assert utils.is_uuid(idfr), "Identifier {} is not a" " UUID".format(
                        idfr
                    )
                elif idfr_type == "hdl":
                    assert utils.is_hdl(
                        idfr, entity["type"], accession_no
                    ), "Identifier {} is not a hdl".format(idfr)
                else:
                    purls.append(idfr)
            assert utils.all_urls_resolve(
                purls
            ), "At least one PURL does not resolve in\n  {}".format("\n  ".join(purls))

    @staticmethod
    def assert_empty_dir_documented_identified(mets_doc, empty_dir_rel_path):
        """Make assertions that confirm that the empty directory
        ``empty_dir_rel_path`` is documented in the METS XML document
        ``mets_doc`` and that it has the expected identifiers: PID, PURL, and
        UUID.
        """
        ns = c.METS_NSMAP
        norm_struct = mets_doc.xpath(
            "mets:structMap[@LABEL='Normative Directory Structure']", namespaces=ns
        )[0]
        assert norm_struct is not None
        objects_div_el = norm_struct.xpath(
            "mets:div[@TYPE='Directory']"
            "/mets:div[@TYPE='Directory' and @LABEL='objects']",
            namespaces=ns,
        )[0]
        assert objects_div_el is not None
        xpath = []
        for dir_ in empty_dir_rel_path.split("/"):
            xpath.append("mets:div[@TYPE='Directory' and @LABEL='{}']".format(dir_))
        xpath = "/".join(xpath)
        empty_dir_div_el = objects_div_el.xpath(xpath, namespaces=ns)[0]
        assert empty_dir_div_el is not None
        dmdid = empty_dir_div_el.get("DMDID")
        assert dmdid is not None
        dmd_sec_el = mets_doc.xpath(
            "mets:dmdSec[@ID='{}']".format(dmdid), namespaces=ns
        )[0]
        assert dmd_sec_el is not None
        identifiers = []
        for obj_idfr_el in dmd_sec_el.findall(
            "mets:mdWrap/" "mets:xmlData/" "premis3:object/" "premis3:objectIdentifier",
            ns,
        ):
            identifiers.append(
                (
                    obj_idfr_el.find("premis3:objectIdentifierType", ns).text,
                    obj_idfr_el.find("premis3:objectIdentifierValue", ns).text,
                )
            )
        uuid_id = [ival for itype, ival in identifiers if itype == "UUID"][0]
        hdl_id = [ival for itype, ival in identifiers if itype == "hdl"][0]
        uri_id = [ival for itype, ival in identifiers if itype == "URI"][0]
        assert uuid_id
        assert hdl_id
        assert uri_id


def _add_entity_identifiers(entity, doc, ns):
    """Find all of the identifiers for ``entity`` (a dict representing a file
    or directory) in the lxml ``Element`` instance ``doc`` (which represents a
    METS.xml file) and add them as a list value for the ``'identifiers'`` key
    of ``entity``.
    """
    e_type = entity["type"]
    e_id = entity["id"]
    identifiers = []
    if e_id is None:
        return entity
    elif e_type == "file":
        amd_sec_el = doc.xpath("mets:amdSec[@ID='{}']".format(e_id), namespaces=ns)[0]
        obj_idfr_els = amd_sec_el.findall(
            ".//mets:mdWrap/"
            "mets:xmlData/"
            "premis3:object/"
            "premis3:objectIdentifier",
            ns,
        )
        for obj_idfr_el in obj_idfr_els:
            identifiers.append(
                (
                    obj_idfr_el.find("premis3:objectIdentifierType", ns).text,
                    obj_idfr_el.find("premis3:objectIdentifierValue", ns).text,
                )
            )
    else:
        dmd_sec_el = doc.xpath("mets:dmdSec[@ID='{}']".format(e_id), namespaces=ns)[0]
        for obj_idfr_el in dmd_sec_el.findall(
            "mets:mdWrap/" "mets:xmlData/" "premis3:object/" "premis3:objectIdentifier",
            ns,
        ):
            identifiers.append(
                (
                    obj_idfr_el.find("premis3:objectIdentifierType", ns).text,
                    obj_idfr_el.find("premis3:objectIdentifierValue", ns).text,
                )
            )
    entity["identifiers"] = identifiers
    return entity


def _get_mets_entities(doc, root_el=None, entities=None, path="", ns=None):
    """Find all entities (i.e., files and directories) in the physical
    structmap of ``doc`` and return them as a list of dicts having a crucial
    ``identifiers`` key which references a list of the entity's identifiers,
    i.e. its UUID and potentially also its hdl (PID) and URI (PURL).
    """
    if not entities:
        entities = []
    if root_el is None:
        root_el = doc.xpath("mets:structMap[@TYPE='physical']", namespaces=ns)[0]
    for dir_el in root_el.xpath("mets:div[@TYPE='Directory']", namespaces=ns):
        dir_name = dir_el.get("LABEL")
        dir_path = os.path.join(path, dir_name)
        parent_is_structmap = root_el.get("ID") == "structMap_1"
        is_subm_docm = (
            root_el.get("LABEL") == "objects" and dir_name == "submissionDocumentation"
        )
        is_objects = parent_is_structmap and dir_name == "objects"
        if not (is_objects or is_subm_docm):
            entities.append(
                {
                    "type": parent_is_structmap and "aip" or "directory",
                    "id": dir_el.get("DMDID"),
                    "name": dir_name,
                    "path": dir_path,
                }
            )
        if not is_subm_docm:
            entities = _get_mets_entities(
                doc, dir_el, entities=entities, path=dir_path, ns=ns
            )
    for file_el in root_el.xpath("mets:div[@TYPE='Item']", namespaces=ns):
        file_name = file_el.get("LABEL")
        file_id = file_el.find("mets:fptr", ns).get("FILEID")
        file_id = doc.xpath("//mets:file[@ID='{}']".format(file_id), namespaces=ns)[
            0
        ].get("ADMID")
        entities.append(
            {
                "type": "file",
                "id": file_id,
                "name": file_name,
                "path": os.path.join(path, file_name),
            }
        )
    for entity in entities:
        entity = _add_entity_identifiers(entity, doc, ns)
    return entities
