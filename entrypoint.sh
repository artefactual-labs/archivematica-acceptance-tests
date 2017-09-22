#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

readonly __dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

function behave::run() {
    behave \
        --tags=mo-aip-reingest \
        --no-skipped \
        -v \
        -D am_username=${AM_DASHBOARD_USER} \
        -D am_password=${AM_DASHBOARD_PASSWORD} \
        -D am_url=${AM_URL} \
        -D am_version=${AM_VERSION} \
        -D am_api_key=${AM_DASHBOARD_API_KEY} \
        -D ss_username=${AM_SS_USER} \
        -D ss_password=${AM_SS_PASSWORD} \
        -D ss_url=${SS_URL} \
        -D ss_api_key=${AM_SS_API_KEY} \
        -D transfer_source_path=archivematica/archivematica-sampledata/TestTransfers/acceptance-tests \
        -D home=archivematica \
        -D driver_name=$1 \
        -D ssh_accessible=no 2>&1 | tee -a output-acceptance-tests.log output-acceptance-tests-firefox.log | tee last-acceptance-test.log
}

function simplehubtest::run () {
    /home/archivematica/acceptance-tests/simplehubtest.py
}

if [ $# -eq 0 ]; then
    echo "No arguments supplied."
    exit 0
fi

firefox=false
chrome=false
simplehubtest=false

for arg in "$@"
do
    case $arg in
        "firefox" )
           firefox=true;;
        "chrome" )
           chrome=true;;
        "simplehubtest" )
           simplehubtest=true;;
        "all" )
           firefox=true; chrome=true;;
   esac
done

if [ "$firefox" = true ]; then
    behave::run "Firefox-Hub"
fi

if [ "$chrome" = true ]; then
    behave::run "Chrome-Hub"
fi

if [ "$simplehubtest" = true ]; then
    simplehubtest::run
fi
