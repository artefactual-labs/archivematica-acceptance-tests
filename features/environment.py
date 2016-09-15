import archivematicaselenium
import pprint
import requests

# Change these to match your test environment
AM_USERNAME = "test"
AM_PASSWORD = "test"
AM_URL = "http://192.168.168.192/"
AM_API_KEY = None
SS_USERNAME = "test"
SS_PASSWORD = "test"
SS_URL = "http://192.168.168.192:8000/"
SS_API_KEY = None


def before_all(context):
    """Instantiate an Archivematica Selenium browser instance."""
    context.am_sel_cli = archivematicaselenium.ArchivematicaSelenium(
        AM_USERNAME,
        AM_PASSWORD,
        AM_URL,
        AM_API_KEY,
        SS_USERNAME,
        SS_PASSWORD,
        SS_URL,
        SS_API_KEY)
    context.am_sel_cli.set_up()


def after_all(context):
    """Close all browser windows/Selenium drivers."""
    context.am_sel_cli.tear_down()


def after_tag(context, tag):
    if tag == 'mp4-fpr-restore':
        # Put things back as they were: make access .mov files normalize to .mp4
        context.am_sel_cli.change_normalization_rule_command(
            'Access Generic MOV',
            'Transcoding to mp4 with ffmpeg')

