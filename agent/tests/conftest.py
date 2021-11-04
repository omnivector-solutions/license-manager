"""
Configuration of pytest for agent tests
"""
from pathlib import Path
from textwrap import dedent
from unittest.mock import patch

import respx
from httpx import ASGITransport, AsyncClient
from pytest import fixture

from lm_agent.config import settings

MOCK_BIN_PATH = Path(__file__).parent / "mock_tools"


@fixture
def license_servers():
    return ["172.0.1.2 2345", "172.0.1.3 2345"]


@fixture(autouse=True)
def backend_setting():
    """
    Force a specific host for the backend
    """
    with patch.multiple(settings, BACKEND_BASE_URL="http://backend", BIN_PATH=MOCK_BIN_PATH) as mck:
        yield mck


@fixture
def respx_mock():
    """
    Run a test in the respx context (similar to respx decorator, but it's a fixture)
    """
    with respx.mock as mock:
        yield mock


@fixture
def lm_output_bad():
    """
    Some unparseable lmstat output
    """
    return dedent(
        """\
    lmstat - Copyright (c) 1989-2004 by Macrovision Corporation. All rights reserved.
    Flexible License Manager status on Wed 03/31/2021 09:12

    Error getting status: Cannot connect to license server (-15,570:111 "Connection refused")
    """
    )


@fixture
def lm_output():
    """
    Some lmstat output to parse
    """
    return dedent(
        """\
        lmstat - Copyright (c) 1989-2004 by Macrovision Corporation. All rights reserved.
        ...

        Users of TESTFEATURE:  (Total of 1000 licenses issued;  Total of 93 licenses in use)

        ...


        """
        "           jbemfv myserver.example.com /dev/tty (v62.2) (myserver.example.com/24200 12507), "
        "start Thu 10/29 8:09, 29 licenses\n"
        "           cdxfdn myserver.example.com /dev/tty (v62.2) (myserver.example.com/24200 12507), "
        "start Thu 10/29 8:09, 27 licenses\n"
        "           jbemfv myserver.example.com /dev/tty (v62.2) (myserver.example.com/24200 12507), "
        "start Thu 10/29 8:09, 37 licenses\n"
    )


@fixture
def rlm_output():
    return """Setting license file path to 10@licserv.server.com
rlmutil v12.2
Copyright (C) 2006-2017, Reprise Software, Inc. All rights reserved.


	rlm status on licserv.com (port 35015), up 99d 11:08:25
	rlm software version v12.2 (build:2)
	rlm comm version: v1.2
	Startup time: Tue Oct 19 01:40:13 2021
	Todays Statistics (13:48:32), init time: Tue Nov  2 23:00:06 2021
	Recent Statistics (00:16:08), init time: Wed Nov  3 12:32:30 2021

	             Recent Stats         Todays Stats         Total Stats
	              00:16:08             13:48:32         15d 11:08:25
	Messages:    582 (0/sec)           28937 (0/sec)          777647 (0/sec)
	Connections: 463 (0/sec)           23147 (0/sec)          622164 (0/sec)

	--------- ISV servers ----------
	   Name           Port Running Restarts
	csci             63133   Yes      0

	------------------------

	csci ISV server status on licserv.server.com (port 63133), up 99d 11:08:18
	csci software version v12.2 (build: 2)
	csci comm version: v1.2
	csci Debug log filename: F:\RLM\Logs\csci.dlog
	csci Report log filename: F:\RLM\logs\Reportlogs\CSCILOG.rl
	Startup time: Tue Oct 19 01:40:20 2021
	Todays Statistics (13:48:32), init time: Tue Nov  2 23:00:06 2021
	Recent Statistics (00:16:08), init time: Wed Nov  3 12:32:30 2021

	             Recent Stats         Todays Stats         Total Stats
	              00:16:08             13:48:32         15d 11:08:18
	Messages:    991 (0/sec)           34770 (0/sec)          935961 (0/sec)
	Connections: 945 (0/sec)           17359 (0/sec)          466699 (0/sec)
	Checkouts:   0 (0/sec)           1 (0/sec)          937 (0/sec)
	Denials:     0 (0/sec)           0 (0/sec)          0 (0/sec)
	Removals:    0 (0/sec)           0 (0/sec)          0 (0/sec)


	------------------------

	csci license pool status on licser.server.com (port 63133)

	converge v3.0
		count: 1, # reservations: 0, inuse: 0, exp: 31-jan-2022
		obsolete: 0, min_remove: 120, total checkouts: 0
	converge_gui v1.0
		count: 45, # reservations: 0, inuse: 0, exp: 31-jan-2022
		obsolete: 0, min_remove: 120, total checkouts: 26
	converge_gui_polygonica v1.0
		count: 1, # reservations: 0, inuse: 0, exp: 31-jan-2022
		obsolete: 0, min_remove: 120, total checkouts: 26
	converge_super v3.0
		count: 1000, # reservations: 0, inuse: 93, exp: 31-jan-2022
		obsolete: 0, min_remove: 120, total checkouts: 169
	converge_tecplot v1.0
		count: 45, # reservations: 0, inuse: 0, exp: 31-jan-2022
		obsolete: 0, min_remove: 120, total checkouts: 16


	------------------------

	csci license usage status on licser.server.com (port 63133)

	converge_super v3.0: jbemfv@myserver.example.com 29/0 at 11/01 09:01  (handle: 15a) 
	converge_super v3.0: cdxfdn@myserver.example.com 27/0 at 11/03 10:38  (handle: 128) 
	converge_super v3.0: jbemfv@myserver.example.com 37/0 at 11/01 09:01  (handle: 15a)
"""
