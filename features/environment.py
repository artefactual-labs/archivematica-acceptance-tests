import amuser
import utils


# Change these to match your test environment
# These may also be overridden as Behave userdata options
# (https://pythonhosted.org/behave/new_and_noteworthy_v1.2.5.html#index-7),
# i.e., ``behave -D am_username=demo -D am_password=secret``
AM_USERNAME = "test"
AM_PASSWORD = "testtest"
AM_URL = "http://192.168.168.192/"
AM_VERSION = '1.6'
AM_API_KEY = None
SS_USERNAME = "test"
SS_PASSWORD = "test"
SS_URL = "http://192.168.168.192:8000/"
SS_API_KEY = None
# Path relative to /home where transfer sources live.
TRANSFER_SOURCE_PATH = 'vagrant/archivematica-sampledata/TestTransfers/acceptance-tests'
HOME = ''
DRIVER_NAME = 'Chrome'
AUTOMATION_TOOLS_PATH = '/etc/archivematica/automation-tools'
# Set these constants if the AM client should be able to gain SSH access to the
# server where AM is being served. This is needed in order to scp server files
# to local, which some tests need. If SSH access is not possible, set
# ``SSH_ACCESSIBLE`` to ``False``.
SSH_ACCESSIBLE = True
SSH_REQUIRES_PASSWORD = True
SSH_IDENTITY_FILE = None
SERVER_USER = 'vagrant'
SERVER_PASSWORD = 'vagrant'


def get_am_user(userdata):
    """Instantiate an ArchivematicaUser."""
    userdata.update({
        'am_username': userdata.get('am_username', AM_USERNAME),
        'am_password': userdata.get('am_password', AM_PASSWORD),
        'am_url': userdata.get('am_url', AM_URL),
        'alt_am_url': userdata.get('alt_am_url', AM_URL),
        'am_version': userdata.get('am_version', AM_VERSION),
        'am_api_key': userdata.get('am_api_key', AM_API_KEY),
        'ss_username': userdata.get('ss_username', SS_USERNAME),
        'ss_password': userdata.get('ss_password', SS_PASSWORD),
        'ss_url': userdata.get('ss_url', SS_URL),
        'ss_api_key': userdata.get('ss_api_key', SS_API_KEY),
        'driver_name': userdata.get('driver_name', DRIVER_NAME),
        'ssh_accessible': bool(
            userdata.get('ssh_accessible', SSH_ACCESSIBLE)),
        'ssh_requires_password': bool(
            userdata.get('ssh_requires_password', SSH_REQUIRES_PASSWORD)),
        'server_user': userdata.get('server_user', SERVER_USER),
        'server_password': userdata.get('server_password', SERVER_PASSWORD),
        'ssh_identity_file': userdata.get(
            'ssh_identity_file', SSH_IDENTITY_FILE)
    })
    return amuser.ArchivematicaUser(**userdata)


def before_scenario(context, scenario):
    """Instantiate an ``ArchivematicaUser`` instance. The ``ArchivematicaUser``
    instance creates many drivers/browsers. If we don't destroy then in between
    scenarios, we end up with too many and it causes the tests to fail. That is
    why we are using ``before_scenario`` here and not ``before_all``.
    """
    userdata = context.config.userdata
    context.am_user = get_am_user(userdata)
    context.utils = utils
    context.am_user.browser.set_up()
    context.TRANSFER_SOURCE_PATH = userdata.get(
        'transfer_source_path', TRANSFER_SOURCE_PATH)
    context.HOME = userdata.get('home', HOME)
    context.AUTOMATION_TOOLS_PATH = userdata.get(
        'automation_tools_path', AUTOMATION_TOOLS_PATH)


def after_scenario(context, scenario):
    """Close all browser windows/Selenium drivers."""
    # In the following scenario, we've created a weird FPR rule. Here we put
    # things back as they were: make access .mov files normalize to .mp4
    if scenario.name == ('Isla wants to confirm that normalization to .mkv for'
                         ' access is successful'):
        context.am_user.browser.change_normalization_rule_command(
            'Access Generic MOV',
            'Transcoding to mp4 with ffmpeg')
    if scenario.name == (
            'Joel creates an AIP on an Archivematica instance that saves'
            ' stdout/err and on one that does not. He expects that the'
            ' processing time of the AIP on the first instance will be less'
            ' than that of the AIP on the second one.'):
        context.am_user.docker.recreate_archivematica(capture_output=True)
    context.am_user.browser.tear_down()
