# To run this feature against a Docker Compose (DC)-deployed Archivematica
# instance with output capturing turned off::
#
#     $ behave -v --tags=capture-stdout \
#           --tags=deploy.output_capture_state.off \
#           --no-skipped \
#           -D am_username=test \
#           -D am_password=test \
#           -D am_url=http://127.0.0.1:62080/ \
#           -D am_version=1.7 \
#           -D am_api_key=test \
#           -D ss_username=test \
#           -D ss_password=test \
#           -D ss_url=http://127.0.0.1:62081/ \
#           -D ss_api_key=test \
#           -D home=archivematica \
#           -D driver_name=Firefox
#
# To run the equivalent test against a DC deploy with capturing turned on,
# run the same command as above but set the tags flag to the "output capture
# on" value::
#
#           --tags=deploy.output_capture_state.on \
#
# To reconfigure a DC-deployed AM instance with or without output capturing on,
# change the relevant env var to `true` or `false` and call DC's `up` command.
# For example, the following will turn output capturing off:
#
#     AM_CAPTURE_CLIENT_SCRIPT_OUTPUT=false docker-compose up -d

@capture-stdout
Feature: Archivematica offers a configuration option that controls whether standard output is passed from MCPClient workers to the MCPServer scheduler
  When running Archivematica, users want to be able to decide whether or not to
  have MCPClient worker processes pass client script output (stdout from
  preservation tasks) to the MCPServer task scheduler. The stdout can be
  verbose and there are benefits to having the choice to retain it or not.

  @deploy.output_capture_state.<output_capture_state>
  Scenario Outline: Dina wants to configure stdout capturing in an Archivematica instance.
    Given an Archivematica instance that is deployed with output capturing <output_capture_state>
    When preservation tasks occur
    Then the stdout of the tasks is <outcome>
    And the stderr of the tasks is captured

    Examples: Stdout capture configurations
    | output_capture_state | outcome      |
    | off                  | not captured |
    | on                   | captured     |
