#!/usr/bin/env python
from features.environment import get_am_sel_cli

if __name__ == "__main__":
    am_sel_cli = get_am_sel_cli()
    am_sel_cli.set_up()
    am_sel_cli.remove_all_transfers()
    am_sel_cli.tear_down()
