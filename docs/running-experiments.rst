================================================================================
  Running Experiments with the AMAUAT
================================================================================

This document describes how to run experiments with the Archivematica Automated
User Acceptance Tests (AMAUAT).

The
`performance-stdout-no-write.feature <https://github.com/artefactual-labs/archivematica-acceptance-tests/blob/master/features/core/performance-stdout-no-write.feature>`_
file automates the running of an experiment against Archivematica. This
particular experiment measures the performance improvement that results from
changing the *output capturing* configuration setting. It creates the same AIP
twice, once with output capturing enabled and once with it disabled, and
measures and compares the results. To be specific, it automates performance of
the following steps:

1. configure Archivematica to have *output capturing* turned on;
2. initiate an initial transfer A;
3. record the task run times for A (rtA);
4. configure Archivematica to have *output capturing* turned off;
5. initiate a second transfer B, which is identical to the first;
6. record the task run times for B (rtB); and
7. assert that rtB is less than rtA.

The result is a replicable experiment that could be performed on different
Archivematica instances, with different compute resources, and on transfers
with various properties, e.g., with differing numbers of files, sizes of files,
and/or types of files.

How can I run this experiment?
================================================================================

Assuming you have Archivematica and the AM Acceptance tests installed using the
`Docker Compose deployment method <https://github.com/artefactual-labs/am/tree/master/compose>`_,
the following command illustrates how this experiment might be run using
``behave``. In this case, we are creating an AIP from an 11M transfer containing
10 (image) files as indicated by the ``--tags=transfer.name.size-11M-files-10``
flag::

    $ behave \
        --tags=performance-no-stdout \
        --tags=transfer.name.size-11M-files-10 \
        --no-skipped \
        --no-logcapture \
        -D driver_name=Firefox \
        -D am_url=http://127.0.0.1:62080/ \
        -D am_password=test \
        -D am_version=1.7 \
        -D docker_compose_path=/abs/path/to/am/compose \
        -D home=archivematica

The log messages sent to stdout will indicate the total runtime (in seconds)
for each of the transfers::

    Total runtime for without output tasks: 361.778649
    Total runtime for with output tasks: 370.786003

If we want to perform the same experiment on a different transfer, we would
replace ``size-11M-files-10`` in ``--tags=transfer.name.size-11M-files-10``
with the name of a different row in the ``Examples`` table of the
`performance-stdout-no-write.feature <../features/core/performance-stdout-no-write.feature>`_
file. For example, the flag ``--tags=transfer.name.size-11G-files-669`` would
run the same experiment using an 11G transfer containing 669 14M video files.

If we want to perform the same experiment on a transfer that is not in the
``Examples`` table, we would have to add a row for it to that table, providing
its path and a descriptive name, and then call behave with the corresponding
``--tags=transfer.name.<...>`` flag.


What is being measured?
================================================================================

When the Gherkin step ``And performance statistics are saved to <FILENAME>`` is
run, the ``ArchivematicaUser.get_tasks_from_sip_uuid`` method defined in
`amuser/am_docker_ability.py <../amuser/am_docker_ability.py>`_ is called. This
performs the following ``SELECT`` on the ``MCP.Tasks`` table and saves the
result as a JSON array of objects, one for each task in the database::

    SELECT t.fileUUID as file_uuid,
        f.fileSize as file_size,
        LENGTH(t.stdOut) as len_std_out,
        LENGTH(t.stdError) as len_std_err,
        t.exec,
        t.exitCode,
        t.endTime,
        t.startTime,
        TIMEDIFF(t.endTime,t.startTime) as duration
     FROM Tasks t
     INNER JOIN Files f ON f.fileUUID=t.fileUUID
     WHERE f.sipUUID='{}'
     ORDER by endTime-startTime, exec;

An example JSON object created from the return value of the ``SELECT``::

    {
        "duration": "00:00:01.243750",
        "exec": "removeFilesWithoutPresmisMetadata_v0.0",
        "file_size": "1080282",
        "len_std_err": "0",
        "len_std_out": "0",
        "file_uuid": "dfcb34c1-42f1-4679-ade8-e15cff81c7dd",
        "endTime": "2018-02-24 01:01:11.174039",
        "startTime": "2018-02-24 01:01:09.930289"
    }

The entire array of Task objects can be viewed in the timestamp-named JSON
files under data/, e.g., data/without_outputs_stats-1519435385.json or
data/with_outputs_stats-1519492395.json.

When the ``And the runtime of client scripts in without_outputs_stats is less
than the runtime of client scripts in with_outputs_stats`` Gherkin step is run,
all of the ``duration`` values from the task objects are summed and the script
asserts that the total task runtime for the AIP created when output capturing
was disabled is less than the corresponding sum for the AIP created when output
capturing was enabled.

Note that because Archivematica runs tasks in parallel (usually with one task
runner per CPU), the total serial task runtime is not a direct indication of
the total processing time of the AIP as a whole. However, a shorter total task
runtime should correlate with a shorter AIP creation time.

Note also that the ``startTime`` and ``endTime`` values are set by the MCP
Server (task manager/scheduler) immediately before and immediately after a job
(i.e., a task) is submitted to the gearman worker. See especially the
``taskCompletedCallBackFunction`` and ``__init__`` methods of the
``linkTaskManagerFiles`` class in
`MCPServer/lib/linkTaskManagerFiles.py <https://github.com/artefactual/archivematica/blob/stable/1.7.x/src/MCPServer/lib/linkTaskManagerFiles.py>`_.


Can I run this experiment on an otherwise-deployed Archivematica instance?
================================================================================

No. Not yet. Some modification could be made to the acceptance tests to make
this possible, but currently you must deploy Archivematica using the Docker
Compose strategy on the same machine where the experiment (the behave tests)
will be run.

An easy way to make this work in other deployment scenarios would involve the
following.

1. Modify how task data are retrieved from the database so that it works with
   other deployment types. One option would make ``ssh`` ``mysql`` calls to the
   instance. Another approach would use the tasks API endpoint that will soon
   be developed.
2. Create a new feature scenario (experiment) which simply creates the AIP and
   harvests and sums the task data without automatically re-configuring
   Archivematica to (not) capture output streams. Let the runner of the
   experiment toggle output capturing manually and have the experiment scenario
   automate the work of creating the AIP and measuring the task runtime.
