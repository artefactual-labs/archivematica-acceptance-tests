import archivematicaselenium
import os
# Change these to match your test environment
AM_USERNAME = os.getenv('AM_USERNAME','test')
AM_PASSWORD = os.getenv('AM_PASSWORD','testtest')
AM_URL = os.getenv('AM_URL','http://192.168.168.192/')
#AM_URL = "http://138.68.4.177/"
# Note: the following are not yet used by ``ArchivematicaSelenium``
AM_API_KEY = None
SS_USERNAME = os.getenv('SS_USERNAME','test')
SS_PASSWORD = os.getenv('SS_PASSWORD','test')
SS_URL = os.getenv('SS_URL','http://192.168.168.192:8000/')
#SS_URL = "http://138.68.4.177:8000/"
SS_API_KEY = None

# Path relative to /home where transfer sources live.
# TRANSFER_SOURCE_PATH = 'vagrant/acceptance-tests'
# TRANSFER_SOURCE_PATH = 'vagrant'
TRANSFER_SOURCE_PATH = (
    'vagrant/archivematica-sampledata/TestTransfers/acceptance-tests')
HOME = 'vagrant'

def get_am_sel_cli():
    """Instantiate an ArchivematicaSelenium."""
    return archivematicaselenium.ArchivematicaSelenium(
        AM_USERNAME,
        AM_PASSWORD,
        AM_URL,
        AM_API_KEY,
        SS_USERNAME,
        SS_PASSWORD,
        SS_URL,
        SS_API_KEY
    )


def before_scenario(context, scenario):
    """Instantiate an Archivematica Selenium browser instance. The
    ArchivematicaSelenium instance creates many drivers/browsers. If we don't
    destroy then in between scenarios, we end up with too many and it causes
    the tests to fail. That is why we are using ``before_scenario`` here and
    not ``before_all``.
    """
    context.am_sel_cli = get_am_sel_cli()
    context.am_sel_cli.set_up()
    context.TRANSFER_SOURCE_PATH = TRANSFER_SOURCE_PATH
    context.HOME = HOME


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
