"""Steps for the Bind PIDs Feature."""

from behave import then, given

from . import utils

# ==============================================================================
# Step Definitions
# ==============================================================================

# Givens
# ------------------------------------------------------------------------------

@given('default processing configured to bind PIDs')
def step_impl(context):
    context.execute_steps(
        'Given the processing config decision "Bind PIDs" is set to "Yes"\n')


@given('a Handle server client configured to create qualified PURLs')
def step_impl(context):
    """Configure the handle server settings in the dashboard so that PIDs can
    be minted and resolved (a.k.a. "bound").
    NOTE: this step requires user-supplied values for runtime-specific
    parameters like handle web service endpoint and web service key that must
    be passed in as behave userdata (i.e., -D) arguments.
    """
    nodice = 'no dice'
    # Runtime-specific parameters for the Handle configuration to test against
    # must be passed in by the user at test runtime, e.g., as
    # ``behave -D base_resolve_url='https://foobar.org'``, etc.
    base_resolve_url = getattr(context.am_user.amba, 'base_resolve_url', nodice)
    pid_xml_namespace = getattr(context.am_user.amba, 'pid_xml_namespace', nodice)
    context.am_user.amba.configure_handle(**{
        # More runtime-specific parameters:
        'pid_web_service_endpoint': getattr(
            context.am_user.amba, 'pid_web_service_endpoint', nodice),
        'pid_web_service_key': getattr(
            context.am_user.amba, 'pid_web_service_key', nodice),
        'handle_resolver_url': getattr(
            context.am_user.amba, 'handle_resolver_url', nodice),
        'naming_authority': getattr(
            context.am_user.amba, 'naming_authority', '12345'),
        # Baked in:
        'pid_request_verify_certs': False,
        'resolve_url_template_archive': (
            base_resolve_url + '/dip/{{ naming_authority }}/{{ pid }}'),
        'resolve_url_template_mets': (
            base_resolve_url + '/mets/{{ naming_authority }}/{{ pid }}'),
        'resolve_url_template_file': (
            base_resolve_url + '/access/{{ naming_authority }}/{{ pid }}'),
        'resolve_url_template_file_access': (
            base_resolve_url + '/access/{{ naming_authority }}/{{ pid }}'),
        'resolve_url_template_file_preservation': (
            base_resolve_url + '/preservation/{{ naming_authority }}/{{ pid }}'),
        'resolve_url_template_file_original': (
            base_resolve_url + '/original/{{ naming_authority }}/{{ pid }}'),
        'pid_request_body_template': '''<?xml version='1.0' encoding='UTF-8'?>
        <soapenv:Envelope
            xmlns:soapenv='http://schemas.xmlsoap.org/soap/envelope/'
            xmlns:pid='{pid_xml_namespace}'>
            <soapenv:Body>
                <pid:UpsertPidRequest>
                    <pid:na>{{{{ naming_authority }}}}</pid:na>
                    <pid:handle>
                        <pid:pid>{{{{ naming_authority }}}}/{{{{ pid }}}}</pid:pid>
                        <pid:locAtt>
                            <pid:location weight='1' href='{{{{ base_resolve_url }}}}'/>
                            {{% for qrurl in qualified_resolve_urls %}}
                                <pid:location
                                    weight='0'
                                    href='{{{{ qrurl.url }}}}'
                                    view='{{{{ qrurl.qualifier }}}}'/>
                            {{% endfor %}}
                        </pid:locAtt>
                    </pid:handle>
                </pid:UpsertPidRequest>
            </soapenv:Body>
        </soapenv:Envelope>'''.format(pid_xml_namespace=pid_xml_namespace)
    })


@given('a Handle server client configured to use the accession number as the'
       ' PID for the AIP')
def step_impl(context):
    context.am_user.amba.configure_handle(
        handle_archive_pid_source='Accession number')


# Whens
# ------------------------------------------------------------------------------


# Thens
# ------------------------------------------------------------------------------

@then('the AIP METS file documents PIDs, PURLs, and UUIDs for all files,'
      ' directories and the package itself')
def step_impl(context):
    accession_no = getattr(context.scenario, 'accession_no', None)
    mets = utils.get_mets_from_scenario(context)
    context.am_user.ammetsa.validate_mets_for_pids(mets, accession_no=accession_no)
