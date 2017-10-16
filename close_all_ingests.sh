#!/usr/bin/env bash
behave --tags=-wip, --tags=close-all-ingests --no-skipped $@
