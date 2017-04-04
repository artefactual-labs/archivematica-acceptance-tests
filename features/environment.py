import archivematicaselenium

# Change these to match your test environment
# These may also be overridden as Behave userdata options
# (https://pythonhosted.org/behave/new_and_noteworthy_v1.2.5.html#index-7),
# i.e., ``behave -D am_username=demo -D am_password=secret``
AM_USERNAME = "test"
AM_PASSWORD = "testtest"
AM_URL = "http://192.168.168.192/"
AM_API_KEY = None
SS_USERNAME = "test"
SS_PASSWORD = "test"
SS_URL = "http://192.168.168.192:8000/"
SS_API_KEY = None
# Path relative to /home where transfer sources live.
TRANSFER_SOURCE_PATH = 'vagrant/archivematica-sampledata/TestTransfers/acceptance-tests'
HOME = 'vagrant'
DRIVER_NAME = 'Chrome'


def get_am_sel_cli(userdata):
    """Instantiate an ArchivematicaSelenium."""
    return archivematicaselenium.ArchivematicaSelenium(
        userdata.get('am_username', AM_USERNAME),
        userdata.get('am_password', AM_PASSWORD),
        userdata.get('am_url', AM_URL),
        userdata.get('am_api_key', AM_API_KEY),
        userdata.get('ss_username', SS_USERNAME),
        userdata.get('ss_password', SS_PASSWORD),
        userdata.get('ss_url', SS_URL),
        userdata.get('ss_api_key', SS_API_KEY),
        userdata.get('driver_name', DRIVER_NAME),
    )


def before_scenario(context, scenario):
    """Instantiate an Archivematica Selenium browser instance. The
    ArchivematicaSelenium instance creates many drivers/browsers. If we don't
    destroy then in between scenarios, we end up with too many and it causes
    the tests to fail. That is why we are using ``before_scenario`` here and
    not ``before_all``.
    """
    userdata = context.config.userdata
    context.am_sel_cli = get_am_sel_cli(userdata)
    context.am_sel_cli.set_up()
    context.TRANSFER_SOURCE_PATH = userdata.get(
        'transfer_source_path', TRANSFER_SOURCE_PATH)
    context.HOME = userdata.get('home', HOME)


def after_scenario(context, scenario):
    """Close all browser windows/Selenium drivers."""
    # In the following scenario, we've created a weird FPR rule. Here we put
    # things back as they were: make access .mov files normalize to .mp4
    if scenario.name == ('Isla wants to confirm that normalization to .mkv for'
            ' access is successful'):
        context.am_sel_cli.change_normalization_rule_command(
            'Access Generic MOV',
            'Transcoding to mp4 with ffmpeg')
    context.am_sel_cli.tear_down()
