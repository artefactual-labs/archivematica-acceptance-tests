"""Steps for the METS-related functionality."""

import json

from behave import then

from features.steps import utils

# ==============================================================================
# Step Definitions
# ==============================================================================

# Thens
# ------------------------------------------------------------------------------


@then(
    "in the METS file there are/is {count} PREMIS event(s) of type"
    " {event_type} with properties {properties}"
)
def step_impl(context, count, event_type, properties):
    mets = utils.get_mets_from_scenario(context)
    events = []
    properties = json.loads(properties)
    for premis_evt_el in mets.findall(
        ".//premis:event", context.am_user.mets.mets_nsmap
    ):
        premis_evt_type_el = premis_evt_el.find(
            "premis:eventType", context.am_user.mets.mets_nsmap
        )
        if premis_evt_type_el.text == event_type:
            events.append(premis_evt_el)
            utils.assert_premis_event(event_type, premis_evt_el, context)
            utils.assert_premis_properties(premis_evt_el, context, properties)
    assert len(events) == int(count), (
        f"We expected to find {count} events of type {event_type} matching"
        f" properties `{str(properties)}` but in fact we only found"
        f" {len(events)}."
    )


@then("in the METS file there are/is {count} PREMIS event(s) of type {event_type}")
def step_impl(context, count, event_type):
    mets = utils.get_mets_from_scenario(context)
    events = []
    for premis_evt_el in mets.findall(
        ".//premis:event", context.am_user.mets.mets_nsmap
    ):
        premis_evt_type_el = premis_evt_el.find(
            "premis:eventType", context.am_user.mets.mets_nsmap
        )
        if premis_evt_type_el.text == event_type:
            events.append(premis_evt_el)
            utils.assert_premis_event(event_type, premis_evt_el, context)
    assert len(events) == int(count)


@then(
    "in the METS file the metsHdr element has a CREATEDATE attribute"
    " {conj_quant} LASTMODDATE attribute"
)
def step_impl(context, conj_quant):
    """``conj_quant`` is 'but no' or 'and a', a conjunction followed by a
    quantifier, of course.
    """
    mets = utils.get_mets_from_scenario(context, api=True)
    mets_hdr_els = mets.findall(".//mets:metsHdr", context.am_user.mets.mets_nsmap)
    assert len(mets_hdr_els) == 1
    mets_hdr_el = mets_hdr_els[0]
    assert mets_hdr_el.get("CREATEDATE")
    if conj_quant == "but no":
        assert mets_hdr_el.get("LASTMODDATE") is None
    else:
        assert mets_hdr_el.get("LASTMODDATE") is not None, (
            "<mets:metsHdr>"
            " element is lacking a LASTMODDATE attribute:"
            f" {mets_hdr_el.attrib}"
        )
        # TODO: assert that value is ISO datetime


@then("in the METS file the metsHdr element has {quant} dmdSec next sibling element(s)")
def step_impl(context, quant):
    mets = utils.get_mets_from_scenario(context, api=True)
    mets_dmd_sec_els = mets.findall(".//mets:dmdSec", context.am_user.mets.mets_nsmap)
    try:
        assert len(mets_dmd_sec_els) == int(
            quant
        ), f"Expected {int(quant)} dmdSec element(s), got {len(mets_dmd_sec_els)}"
    except ValueError:
        raise utils.ArchivematicaStepsError(
            f"Unable to recognize the quantifier {quant} when checking for dmdSec"
            " elements in the METS file"
        )


@then("in the METS file the dmdSec element contains the metadata added")
def step_impl(context):
    mets = utils.get_mets_from_scenario(context, api=True)
    dublincore_el = mets.find(
        ".//mets:dmdSec/mets:mdWrap/mets:xmlData/dcterms:dublincore",
        context.am_user.mets.mets_nsmap,
    )
    assert dublincore_el
    for attr in context.am_user.browser.metadata_attrs:
        dc_el = dublincore_el.find(f"dc:{attr}", context.am_user.mets.mets_nsmap)
        assert dc_el is not None
        assert dc_el.text == context.am_user.browser.dummy_val
