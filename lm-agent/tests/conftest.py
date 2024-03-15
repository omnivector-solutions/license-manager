"""
Configuration of pytest for agent tests.
"""
from pathlib import Path
from textwrap import dedent
from unittest.mock import patch

import httpx
import respx
from pytest import fixture

from lm_agent.backend_utils.models import (
    BookingSchema,
    ConfigurationSchema,
    FeatureSchema,
    JobSchema,
    LicenseServerSchema,
    LicenseServerType,
    ProductSchema,
)
from lm_agent.config import settings

MOCK_BIN_PATH = Path(__file__).parent / "mock_tools"


@fixture(autouse=True)
def mock_cache_dir(tmp_path):
    """Mock a cache directory."""
    _cache_dir = tmp_path / "license-manager-cache"
    assert not _cache_dir.exists()
    with patch("lm_agent.config.settings.CACHE_DIR", new=_cache_dir):
        yield _cache_dir


@fixture
def license_servers():
    """List of license servers."""
    return ["172.0.1.2 2345", "172.0.1.3 2345"]


@fixture
def respx_mock():
    """
    Run a test in the respx context (similar to respx decorator, but it's a fixture).

    Mocks the OIDC route used to secure a token.
    """
    with respx.mock as mock:
        respx.post(f"https://{settings.OIDC_DOMAIN}/protocol/openid-connect/token").mock(
            return_value=httpx.Response(status_code=200, json=dict(access_token="dummy-token"))
        )
        yield mock


@fixture
def jobs():
    """Some job response examples."""
    return [
        {
            "id": 1,
            "slurm_job_id": "123",
            "cluster_client_id": "dummy",
            "username": "user1",
            "lead_host": "host1",
            "bookings": [
                {"id": 1, "job_id": 1, "feature_id": 1, "quantity": 12},
                {"id": 2, "job_id": 1, "feature_id": 2, "quantity": 50},
            ],
        },
        {
            "id": 2,
            "slurm_job_id": "456",
            "cluster_client_id": "dummy",
            "username": "user2",
            "lead_host": "host2",
            "bookings": [
                {"id": 3, "job_id": 2, "feature_id": 4, "quantity": 15},
                {"id": 4, "job_id": 2, "feature_id": 7, "quantity": 25},
            ],
        },
        {
            "id": 3,
            "slurm_job_id": "789",
            "cluster_client_id": "dummy-2",
            "username": "user3",
            "lead_host": "host3",
            "bookings": [
                {"id": 14, "job_id": 6, "feature_id": 4, "quantity": 5},
                {"id": 15, "job_id": 6, "feature_id": 7, "quantity": 17},
            ],
        },
    ]


@fixture
def parsed_jobs():
    """Some parsed job response examples."""
    return [
        JobSchema(
            id=1,
            slurm_job_id="123",
            cluster_client_id="dummy",
            username="user1",
            lead_host="host1",
            bookings=[
                BookingSchema(id=1, job_id=1, feature_id=1, quantity=12),
                BookingSchema(id=2, job_id=1, feature_id=2, quantity=50),
            ],
        ),
        JobSchema(
            id=2,
            slurm_job_id="456",
            cluster_client_id="dummy",
            username="user2",
            lead_host="host2",
            bookings=[
                BookingSchema(id=3, job_id=2, feature_id=4, quantity=15),
                BookingSchema(id=4, job_id=2, feature_id=7, quantity=25),
            ],
        ),
        JobSchema(
            id=3,
            slurm_job_id="789",
            cluster_client_id="dummy",
            username="user3",
            lead_host="host3",
            bookings=[
                BookingSchema(id=14, job_id=6, feature_id=4, quantity=5),
                BookingSchema(id=15, job_id=6, feature_id=7, quantity=17),
            ],
        ),
    ]


@fixture
def bookings():
    """Some booking response examples."""
    return [
        {"id": 1, "job_id": 1, "feature_id": 1, "quantity": 12},
        {"id": 2, "job_id": 1, "feature_id": 2, "quantity": 50},
        {"id": 3, "job_id": 2, "feature_id": 4, "quantity": 15},
        {"id": 4, "job_id": 2, "feature_id": 7, "quantity": 25},
        {"id": 14, "job_id": 6, "feature_id": 4, "quantity": 5},
        {"id": 15, "job_id": 6, "feature_id": 7, "quantity": 17},
    ]


@fixture
def configurations():
    """Some configuration response examples."""
    return [
        {
            "id": 1,
            "name": "Abaqus",
            "cluster_client_id": "dummy",
            "features": [
                {
                    "id": 1,
                    "name": "abaqus",
                    "product": {"id": 1, "name": "abaqus"},
                    "config_id": 1,
                    "reserved": 100,
                    "total": 123,
                    "used": 12,
                    "booked_total": 12,
                }
            ],
            "license_servers": [
                {"id": 1, "config_id": 1, "host": "licserv0001", "port": 1234},
                {"id": 3, "config_id": 1, "host": "licserv0003", "port": 8760},
            ],
            "grace_time": 60,
            "type": "flexlm",
        },
        {
            "id": 2,
            "name": "Converge",
            "cluster_client_id": "dummy",
            "features": [
                {
                    "id": 2,
                    "name": "converge_super",
                    "product": {"id": 2, "name": "converge"},
                    "config_id": 2,
                    "reserved": 0,
                    "total": 500,
                    "used": 50,
                    "booked_total": 50,
                }
            ],
            "license_servers": [{"id": 2, "config_id": 2, "host": "licserv0002", "port": 2345}],
            "grace_time": 123,
            "type": "rlm",
        },
    ]


@fixture
def parsed_configurations():
    """Some parsed configuration response examples."""
    return [
        ConfigurationSchema(
            id=1,
            name="Abaqus",
            cluster_client_id="dummy",
            features=[
                FeatureSchema(
                    id=1,
                    name="abaqus",
                    product=ProductSchema(id=1, name="abaqus"),
                    config_id=1,
                    reserved=100,
                    total=123,
                    used=12,
                    booked_total=12,
                )
            ],
            license_servers=[
                LicenseServerSchema(id=1, config_id=1, host="licserv0001", port=1234),
                LicenseServerSchema(id=3, config_id=1, host="licserv0003", port=8760),
            ],
            grace_time=60,
            type=LicenseServerType.FLEXLM,
        ),
        ConfigurationSchema(
            id=2,
            name="Converge",
            cluster_client_id="dummy",
            features=[
                FeatureSchema(
                    id=2,
                    name="converge_super",
                    product=ProductSchema(id=2, name="converge"),
                    config_id=2,
                    reserved=0,
                    total=500,
                    used=50,
                    booked_total=50,
                )
            ],
            license_servers=[LicenseServerSchema(id=2, config_id=2, host="licserv0002", port=2345)],
            grace_time=123,
            type=LicenseServerType.RLM,
        ),
    ]


@fixture
def features():
    """Some features reponse examples."""
    return [
        {
            "id": 1,
            "name": "abaqus",
            "product": {"id": 1, "name": "abaqus"},
            "config_id": 1,
            "reserved": 100,
            "total": 123,
            "used": 12,
            "booked_total": 12,
        },
        {
            "id": 2,
            "name": "abaqus",
            "product": {"id": 1, "name": "abaqus"},
            "config_id": 2,
            "reserved": 100,
            "total": 123,
            "used": 12,
            "booked_total": 50,
        },
    ]


@fixture
def parsed_features():
    """Some parsed features reponse examples."""
    return [
        FeatureSchema(
            id=1,
            name="abaqus",
            product=ProductSchema(id=1, name="abaqus"),
            config_id=1,
            reserved=100,
            total=123,
            used=12,
            booked_total=12,
        ),
        FeatureSchema(
            id=2,
            name="abaqus",
            product=ProductSchema(id=1, name="abaqus"),
            config_id=2,
            reserved=100,
            total=123,
            used=12,
            booked_total=50,
        ),
    ]


@fixture
def one_configuration_row_flexlm():
    return ConfigurationSchema(
        id=1,
        name="Test Feature",
        cluster_client_id="dummy",
        features=[
            FeatureSchema(
                id=1,
                name="testfeature",
                product=ProductSchema(id=1, name="testproduct"),
                config_id=1,
                reserved=100,
                total=1000,
                used=93,
                booked_total=0,
            )
        ],
        license_servers=[
            LicenseServerSchema(id=1, config_id=1, host="127.0.0.1", port=2345),
        ],
        grace_time=60,
        type=LicenseServerType.FLEXLM,
    )


@fixture
def one_configuration_row_rlm():
    return ConfigurationSchema(
        id=1,
        name="Converge",
        cluster_client_id="dummy",
        features=[
            FeatureSchema(
                id=1,
                name="converge_super",
                product=ProductSchema(id=1, name="converge"),
                config_id=1,
                reserved=100,
                total=1000,
                used=93,
                booked_total=0,
            )
        ],
        license_servers=[
            LicenseServerSchema(id=1, config_id=1, host="127.0.0.1", port=2345),
        ],
        grace_time=60,
        type=LicenseServerType.RLM,
    )


@fixture
def one_configuration_row_lsdyna():
    return ConfigurationSchema(
        id=1,
        name="MPPDYNA",
        cluster_client_id="dummy",
        features=[
            FeatureSchema(
                id=1,
                name="mppdyna",
                product=ProductSchema(id=1, name="mppdyna"),
                config_id=1,
                reserved=100,
                total=500,
                used=440,
                booked_total=0,
            )
        ],
        license_servers=[
            LicenseServerSchema(id=1, config_id=1, host="127.0.0.1", port=2345),
        ],
        grace_time=60,
        type=LicenseServerType.LSDYNA,
    )


@fixture
def one_configuration_row_lmx():
    return ConfigurationSchema(
        id=1,
        name="HyperWorks",
        cluster_client_id="dummy",
        features=[
            FeatureSchema(
                id=1,
                name="hyperworks",
                product=ProductSchema(id=1, name="hyperworks"),
                config_id=1,
                reserved=100,
                total=1000,
                used=93,
                booked_total=0,
            )
        ],
        license_servers=[
            LicenseServerSchema(id=1, config_id=1, host="127.0.0.1", port=2345),
        ],
        grace_time=60,
        type=LicenseServerType.LMX,
    )


@fixture
def one_configuration_row_olicense():
    return ConfigurationSchema(
        id=1,
        name="FTire Adams",
        cluster_client_id="dummy",
        features=[
            FeatureSchema(
                id=1,
                name="ftire_adams",
                product=ProductSchema(id=1, name="cosin"),
                config_id=1,
                reserved=100,
                total=1000,
                used=93,
                booked_total=0,
            )
        ],
        license_servers=[
            LicenseServerSchema(id=1, config_id=1, host="127.0.0.1", port=2345),
        ],
        grace_time=60,
        type=LicenseServerType.OLICENSE,
    )


@fixture
def scontrol_show_lic_output_flexlm():
    """An output of scontrol show lic command for FlexLM license."""
    return dedent(
        """
        LicenseName=testproduct.testfeature@flexlm
            Total=10 Used=0 Free=10 Reserved=0 Remote=yes
        """
    )


@fixture
def scontrol_show_lic_output_rlm():
    """An output of scontrol show lic command for RLM license."""
    return dedent(
        """
        LicenseName=converge.converge_super@rlm
            Total=10 Used=0 Free=10 Reserved=0 Remote=yes
        """
    )


@fixture
def scontrol_show_lic_output_lsdyna():
    """An output of scontrol show lic command for LSDyna license."""
    return dedent(
        """
        LicenseName=mppdyna.mppdyna@lsdyna
            Total=500 Used=0 Free=500 Reserved=0 Remote=yes
        """
    )


@fixture
def scontrol_show_lic_output_lmx():
    """An output of scontrol show lic command for LM-X license."""
    return dedent(
        """
        LicenseName=hyperworks.hyperworks@lmx
            Total=1000000 Used=0 Free=500 Reserved=0 Remote=yes
        """
    )


@fixture
def scontrol_show_lic_output_olicense():
    """An output of scontrol show lic command for OLicense license."""
    return dedent(
        """
        LicenseName=cosin.ftire_adams@olicense
            Total=4 Used=0 Free=4 Reserved=0 Remote=yes
        """
    )


@fixture
def flexlm_output_bad():
    """Some unparseable lmstat output."""
    return dedent(
        """\
        lmstat - Copyright (c) 1989-2004 by Macrovision Corporation. All rights reserved.
        Flexible License Manager status on Wed 03/31/2021 09:12

        Error getting status: Cannot connect to license server (-15,570:111 "Connection refused")
        """
    )


@fixture
def flexlm_output():
    """Some FlexLM output to parse."""
    return dedent(
        """\
        lmstat - Copyright (c) 1989-2004 by Macrovision Corporation. All rights reserved.
        ...
        Users of TESTFEATURE:  (Total of 1000 licenses issued;  Total of 93 licenses in use)
        ...
            sdmfva myserver.example.com /dev/tty (v62.2) (myserver.example.com/24200 12507), start Thu 10/29 8:09, 29 licenses
            adfdna myserver.example.com /dev/tty (v62.2) (myserver.example.com/24200 12507), start Thu 10/29 8:09, 27 licenses
            sdmfva myserver.example.com /dev/tty (v62.2) (myserver.example.com/24200 12507), start Thu 10/29 8:09, 37 licenses
        """
    )


@fixture
def flexlm_output_2():
    """Some FlexLM output to parse."""
    return dedent(
        """\
        lmutil - Copyright (c) 1989-2012 Flexera Software LLC. All Rights Reserved.
        ...
        Users of TEST_FEATURE:  (Total of 42800 licenses issued;  Total of 1600 licenses in use)
        ...
            usbn12 p-c94.com /dev/tty feature=test_feature (v2023.0) (myserver.example.com/41020 10223), start Mon 3/11 13:16, 100 licenses
            usbn12 p-c94.com /dev/tty feature=test_feature_2 (v2023.0) (myserver.example.com/41020 626), start Mon 3/11 13:16, 1400 licenses
            usbn12 p-c94.com /dev/tty feature=test_feature_3 (v2023.0) (myserver.example.com/41020 10110), start Mon 3/11 13:16, 100 licenses
        """
    )


@fixture
def flexlm_output_3():
    """Some FlexLM output to parse."""
    return dedent(
        """\
        lmutil - Copyright (c) 1989-2012 Flexera Software LLC. All Rights Reserved.
        ...
        Users of ccmppower:  (Total of 40 licenses issued;  Total of 3 licenses in use)
        ...
        "ccmppower" v2025.09, vendor: abc
        floating license
            1nou7p dcv033.com /dev/tty (v2023.06) (myserver.example.com/27012 3457), start Mon 3/11 12:17

        "ccmppower" v2024.09, vendor: abc
        floating license

            1nou7p n-c41.com /dev/tty (v2023.06) (myserver.example.com/27012 2541), start Mon 3/11 22:36
            1nou7p nid001234 /dev/tty (v2022.10) (myserver.example.com/27012 3331), start Sun 3/10 10:41
        """
    )


@fixture
def flexlm_output_4():
    """Some FlexLM output to parse."""
    return dedent(
        """\
        lmutil - Copyright (c) 1989-2012 Flexera Software LLC. All Rights Reserved.
        ...
        Users of MSCONE:  (Total of 750 licenses issued;  Total of 18 licenses in use)
        ...
            ABCDKK ER0037 SESOR045 MSCONE:ADAMS_View (v2023.0331) (myserver.example.com/29065 2639), start Fri 3/8 13:25, 5 licenses
            ABCDKK ER0037 SESOR045 MSCONE:ADAMS_Car_Plugin (v2023.0331) (myserver.example.com/29065 8195), start Fri 3/8 13:25
            ABCDKK ER0037 SESOR045 MSCONE:ADAMS_View (v2023.0331) (myserver.example.com/29065 2474), start Fri 3/8 13:25, 5 licenses
            ABCDKK ER0037 SESOR045 MSCONE:ADAMS_Car_Plugin (v2023.0331) (myserver.example.com/29065 4903), start Fri 3/8 13:25
            ABCDKK ER0037 SESOR100 MSCONE:ADAMS_View (v2021.0630) (myserver.example.com/29065 11260), start Mon 3/11 10:49, 5 licenses
            ABCDKK ER0037 SESOR100 MSCONE:ADAMS_Car_Plugin (v2021.0630) (myserver.example.com/29065 7727), start Mon 3/11 10:49
        """
    )


@fixture
def flexlm_output_no_licenses():
    """Some lmstat output with no licenses in use to parse."""
    return dedent(
        """\
        lmstat - Copyright (c) 1989-2004 by Macrovision Corporation. All rights reserved.
        ...

        Users of TESTFEATURE:  (Total of 1000 licenses issued;  Total of 0 licenses in use)

        ...

        """
    )


@fixture
def rlm_output_bad():
    """Some unparseable rlm output."""
    return dedent(
        """\
        rlmutil v12.2
        Copyright (C) 2006-2017, Reprise Software, Inc. All rights reserved.


        Error connecting to "rlm" server

        Connection attempted to host: "" on port 5053

        No error
        """
    )


@fixture
def rlm_output():
    """Some rlm output to parse."""
    return dedent(
        """\
        Setting license file path to 10@licserv.server.com
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
    )


@fixture
def another_rlm_output():
    """Some rlm output to parse."""
    return dedent(
        """\
        Setting license file path to 1234@licserv0001.com
        rlmutil v12.2

            powercase v1.0
                count: 5, # reservations: 0, inuse: 3, exp: 31-dec-2023
                obsolete: 0, min_remove: 120, total checkouts: 19
            powerexport v1.0
                count: 5, # reservations: 0, inuse: 0, exp: 31-dec-2023
                obsolete: 0, min_remove: 120, total checkouts: 0
            powerflow-decomp v1.0
                count: 3000, # reservations: 0, inuse: 0, exp: 31-dec-2023
                obsolete: 0, min_remove: 120, total checkouts: 6
            powerflow-disc v1.0
                count: 3000, # reservations: 0, inuse: 0, exp: 31-dec-2023
                obsolete: 0, min_remove: 120, total checkouts: 6
            powerinsight v1.0
                count: 5, # reservations: 0, inuse: 0, exp: 31-dec-2023
                obsolete: 0, min_remove: 120, total checkouts: 5
            powerviz v1.0
                count: 5, # reservations: 0, inuse: 0, exp: 31-dec-2023
                obsolete: 0, min_remove: 120, total checkouts: 26
            powerviz-generator v1.0
                count: 2, # reservations: 0, inuse: 0, exp: 31-dec-2023
                obsolete: 0, min_remove: 120, total checkouts: 22
            powerviz-soiling v1.0
                count: 7, # reservations: 0, inuse: 0, exp: 31-dec-2023
                obsolete: 0, min_remove: 120, total checkouts: 0
            exasignalprocessingjob v1.0
                count: 6, # reservations: 0, inuse: 0, exp: 31-dec-2023
                obsolete: 0, min_remove: 120, total checkouts: 0
            poweracoustics v1.0
                count: 1, # reservations: 0, inuse: 0, exp: 31-dec-2023
                obsolete: 0, min_remove: 120, total checkouts: 2
            powercool v1.0
                count: 1, # reservations: 0, inuse: 0, exp: 31-dec-2023
                obsolete: 0, min_remove: 120, total checkouts: 0
            powerdelta v1.0
                count: 1, # reservations: 0, inuse: 1, exp: 31-dec-2023
                obsolete: 0, min_remove: 120, total checkouts: 9
            powerdelta-meshunion v1.0
                count: 1, # reservations: 0, inuse: 0, exp: 31-dec-2023
                obsolete: 0, min_remove: 120, total checkouts: 0
            powerdelta-translate2 v1.0
                count: 1000000, # reservations: 0, inuse: 0, exp: 31-dec-2023
                obsolete: 0, min_remove: 120, total checkouts: 0
            powerflow-sim v1.0
                count: 7000, # reservations: 0, inuse: 0, exp: 31-dec-2023
                obsolete: 0, min_remove: 120, total checkouts: 6
            powerinsight-generator v1.0
                count: 1, # reservations: 0, inuse: 0, exp: 31-dec-2023
                obsolete: 0, min_remove: 120, total checkouts: 0
            powerthermconnector v1.0
                count: 1, # reservations: 0, inuse: 0, exp: 31-dec-2023
                obsolete: 0, min_remove: 120, total checkouts: 0

            ------------------------

            tainc license pool status on licserv0001.com (port 1234)

            powertherm v2023.1
                count: 1, # reservations: 0, inuse: 0, exp: 31-dec-2023
                obsolete: 0, min_remove: 120, total checkouts: 0
            powertherm-mp v2023.1
                count: 3, # reservations: 0, inuse: 0, exp: 31-dec-2023
                obsolete: 0, min_remove: 120, total checkouts: 0
            powertherm-multigrid v2023.1
                count: 1, # reservations: 0, inuse: 0, exp: 31-dec-2023
                obsolete: 0, min_remove: 120, total checkouts: 0
            powertherm-sc v2023.1
                count: 1, # reservations: 0, inuse: 0, exp: 31-dec-2023
                obsolete: 0, min_remove: 120, total checkouts: 0
            powertherm-solver v2023.1
                count: 1, # reservations: 0, inuse: 0, exp: 31-dec-2023
                obsolete: 0, min_remove: 120, total checkouts: 0


            ------------------------

            exacorp license usage status on licserv0001.com (port 1234)

            powercase v1.0: dfsdgv@server1 1/0 at 08/15 09:34  (handle: 182)
            powercase v1.0: addvbh@server2 1/0 at 08/16 09:36  (handle: c4)
            powercase v1.0: wrtgb3@server3 1/0 at 08/21 14:53  (handle: 11c)
            powerdelta v1.0: ghnds2@server4 1/0 at 08/23 15:16  (handle: a2)
        """
    )


@fixture
def rlm_output_no_licenses():
    """Some rlm output with no licenses in use to parse."""
    return dedent(
        """\
        Setting license file path to 35015@licserv0011.com:35015@licserv0012.com
        rlmutil v12.2
        Copyright (C) 2006-2017, Reprise Software, Inc. All rights reserved.


            rlm status on licserv0011.com (port 35015), up 20d 13:21:16
            rlm software version v12.2 (build:2)
            rlm comm version: v1.2
            Startup time: Tue Oct 19 03:40:13 2021
            Todays Statistics (16:01:23), init time: Mon Nov  8 00:00:06 2021
            Recent Statistics (00:28:35), init time: Mon Nov  8 15:32:54 2021

                         Recent Stats         Todays Stats         Total Stats
                         00:28:35              16:01:23         20d 13:21:16
            Messages:    997 (0/sec)           33562 (0/sec)          1033736 (0/sec)
            Connections: 797 (0/sec)           26849 (0/sec)          827039 (0/sec)

            --------- ISV servers ----------
               Name           Port Running Restarts
            csci             63133   Yes      0

            ------------------------

            csci ISV server status on licserv0011.com (port 63133), up 20d 13:21:09
            csci software version v12.2 (build: 2)
            csci comm version: v1.2
            csci Debug log filename: F:\RLM\Logs\csci.dlog
            csci Report log filename: F:\RLM\logs\Reportlogs\CSCILOG.rl
            Startup time: Tue Oct 19 03:40:20 2021
            Todays Statistics (16:01:23), init time: Mon Nov  8 00:00:06 2021
            Recent Statistics (00:28:35), init time: Mon Nov  8 15:32:54 2021
                         Recent Stats         Todays Stats         Total Stats
                          00:28:35             16:01:23         20d 13:21:09
            Messages:    1196 (0/sec)           40276 (0/sec)          1243764 (0/sec)
            Connections: 598 (0/sec)           20138 (0/sec)          620365 (0/sec)
            Checkouts:   0 (0/sec)           0 (0/sec)          262 (0/sec)
            Denials:     0 (0/sec)           0 (0/sec)          0 (0/sec)
            Removals:    0 (0/sec)           0 (0/sec)          0 (0/sec)


            ------------------------

            csci license pool status on licserv0011.com (port 63133)

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
                count: 1000, # reservations: 0, inuse: 0, exp: 31-jan-2022
                obsolete: 0, min_remove: 120, total checkouts: 189
            converge_tecplot v1.0
                count: 45, # reservations: 0, inuse: 0, exp: 31-jan-2022
                obsolete: 0, min_remove: 120, total checkouts: 21
        """
    )


@fixture
def lsdyna_output_bad():
    """Some unparseable lsdyna output."""
    return dedent(
        """\
        Using default server 31010@localhost
        *** ERROR failed to open server localhost
        """
    )


@fixture
def lsdyna_output():
    """Some lsdyna output to parse."""
    return dedent(
        """\
        Using user specified server 31010@licserv0004.com

        LICENSE INFORMATION

        PROGRAM          EXPIRATION CPUS  USED   FREE    MAX | QUEUE
        ---------------- ----------      ----- ------ ------ | -----
        MPPDYNA          12/30/2022          -     60    500 |     0
         fane8y     59005@n-c13.maas.rnd.com  80
         ssskmj     10274@n-c52.maas.rnd.com  80
         ssskmj     47568@n-c15.maas.rnd.com  80
         ywazrn    239793@n-c53.maas.rnd.com  80
         ywazrn     91665@n-c51.maas.rnd.com  80
         ndhtw9     91626@n-c55.maas.rnd.com  40
        MPPDYNA_971      12/30/2022          0     60    500 |     0
        MPPDYNA_970      12/30/2022          0     60    500 |     0
        MPPDYNA_960      12/30/2022          0     60    500 |     0
        LS-DYNA          12/30/2022          0     60    500 |     0
        LS-DYNA_971      12/30/2022          0     60    500 |     0
        LS-DYNA_970      12/30/2022          0     60    500 |     0
        LS-DYNA_960      12/30/2022          0     60    500 |     0
                           LICENSE GROUP   440     60    500 |     0
        """
    )


@fixture
def lsdyna_output_no_licenses():
    """Some lsdyna output with no licenses in use to parse."""
    return dedent(
        """\
        Using user specified server 31010@licserv0004.com

        LICENSE INFORMATION

        PROGRAM          EXPIRATION CPUS  USED   FREE    MAX | QUEUE
        ---------------- ----------      ----- ------ ------ | -----
        MPPDYNA          12/30/2022          0    500    500 |     0
        MPPDYNA_971      12/30/2022          0    500    500 |     0
        MPPDYNA_970      12/30/2022          0    000    500 |     0
        MPPDYNA_960      12/30/2022          0    000    500 |     0
        LS-DYNA          12/30/2022          0    000    500 |     0
        LS-DYNA_971      12/30/2022          0    000    500 |     0
        LS-DYNA_970      12/30/2022          0    000    500 |     0
        LS-DYNA_960      12/30/2022          0    000    500 |     0
                           LICENSE GROUP     0    000    500 |     0
        """
    )


@fixture
def lmx_output_bad():
    """Some unparseable LM-X output."""
    return dedent(
        """\
        LM-X End-user Utility v3.32
        Copyright (C) 2002-2010 X-Formation. All rights reserved.

        ++++++++++++++++++++++++++++++++++++++++
        LM-X license server(s):
        ----------------------------------------
        There are no license server(s) available.
        """
    )


@fixture
def lmx_output():
    """Some LM-X output to parse."""
    return dedent(
        """\
        LM-X End-user Utility v3.32
        Copyright (C) 2002-2010 X-Formation. All rights reserved.

        ++++++++++++++++++++++++++++++++++++++++
        LM-X License Server on 6200@licserv0013.com:

        Server version: v5.1 Uptime: 3 day(s) 12 hour(s) 0 min(s) 51 sec(s)
        ----------------------------------------
        Feature: CatiaV5Reader Version: 21.0 Vendor: ALTAIR
        Start date: 2022-02-17 Expire date: 2023-01-31
        Key type: EXCLUSIVE License sharing: CUSTOM VIRTUAL

        0 of 3 license(s) used
        ----------------------------------------
        Feature: GlobalZoneEU Version: 21.0 Vendor: ALTAIR
        Start date: 2022-02-17 Expire date: 2023-01-31
        Key type: EXCLUSIVE License sharing: CUSTOM VIRTUAL

        40000 of 1000003 license(s) used:

        15000 license(s) used by VRAAFG@RD0082879 [138.106.159.158]
        Login time: 2022-02-18 09:26   Checkout time: 2022-02-18 09:29
        Shared on custom string: VRAAFG:RD0082879

        25000 license(s) used by VRAAFG@RD0082879 [138.106.159.158]
        Login time: 2022-02-18 09:26   Checkout time: 2022-02-18 09:26
        Shared on custom string: VRAAFG:RD0082879
        ----------------------------------------
        Feature: HWAIFPBS Version: 21.0 Vendor: ALTAIR
        Start date: 2022-02-17 Expire date: 2023-01-31
        Key type: EXCLUSIVE License sharing: CUSTOM VIRTUAL

        0 of 2147483647 license(s) used
        ----------------------------------------
        Feature: HWAWPF Version: 21.0 Vendor: ALTAIR
        Start date: 2022-02-17 Expire date: 2023-01-31
        Key type: EXCLUSIVE License sharing: CUSTOM VIRTUAL

        0 of 2147483647 license(s) used
        ----------------------------------------
        Feature: HWActivate Version: 21.0 Vendor: ALTAIR
        Start date: 2022-02-17 Expire date: 2023-01-31
        Key type: EXCLUSIVE License sharing: CUSTOM VIRTUAL

        0 of 2147483647 license(s) used
        ----------------------------------------
        Feature: HWFlux2D Version: 21.0 Vendor: ALTAIR
        Start date: 2022-02-17 Expire date: 2023-01-31
        Key type: EXCLUSIVE License sharing: CUSTOM VIRTUAL

        30000 of 2147483647 license(s) used:

        15000 license(s) used by VRAAFG@RD0082879 [138.106.159.158]
        Login time: 2022-02-18 09:26   Checkout time: 2022-02-18 09:29
        Shared on custom string: VRAAFG:RD0082879:27164_23514544_1645091752_138525

        15000 license(s) used by VRAAFG@RD0082879 [138.106.159.158]
        Login time: 2022-02-18 09:26   Checkout time: 2022-02-18 09:26
        Shared on custom string: VRAAFG:RD0082879:18896_1081950704_1645017269_309963
        ----------------------------------------
        Feature: HyperWorks Version: 21.0 Vendor: ALTAIR
        Start date: 2022-02-17 Expire date: 2023-01-31
        Key type: EXCLUSIVE License sharing: CUSTOM VIRTUAL

        25000 of 1000000 license(s) used:

        25000 license(s) used by sssaah@RD0082406 [138.106.154.220]
        Login time: 2022-02-18 09:26   Checkout time: 2022-02-18 09:26
        Shared on custom string: sssaah:RD0082406
        """
    )


@fixture
def lmx_output_2():
    return dedent(
        """
        LM-X End-user Utility v3.32
        Copyright (C) 2002-2010 X-Formation. All rights reserved.

        ++++++++++++++++++++++++++++++++++++++++
        LM-X License Server on 6300@licserv0003.scom:

        Server version: v4.9.3 Uptime: 10 day(s) 16 hour(s) 54 min(s) 21 sec(s)
        ----------------------------------------
        Feature: FEMFAT_VISUALIZER Version: 2024.0 Vendor: abc
        Start date: NONE Expire date: 2024-06-30
        Key type: EXCLUSIVE License sharing: HOST USER VIRTUAL

        2 of 2 license(s) used:

        1 license(s) used by fdsva1@dcv046.com_ver2023 [10.123.321.20]
            Login time: 2024-03-11 12:50   Checkout time: 2024-03-11 12:50 
            Shared on username: fdsva1   Shared on hostname: dcv046.com_ver2023 

        1 license(s) used by asdsc1@dcv048.com_ver2022a [10.123.321.10]
            Login time: 2024-03-11 17:29   Checkout time: 2024-03-11 17:29 
            Shared on username: asdsc1   Shared on hostname: dcv048.com_ver2022a 
        """
    )


@fixture
def lmx_output_no_licenses():
    """Some LM-X output with no licenses in use to parse."""
    return dedent(
        """\
        LM-X End-user Utility v3.32
        Copyright (C) 2002-2010 X-Formation. All rights reserved.

        ++++++++++++++++++++++++++++++++++++++++
        LM-X License Server on 6200@licserv0013.com:

        Server version: v5.1 Uptime: 3 day(s) 12 hour(s) 0 min(s) 51 sec(s)
        ----------------------------------------
        Feature: CatiaV5Reader Version: 21.0 Vendor: ALTAIR
        Start date: 2022-02-17 Expire date: 2023-01-31
        Key type: EXCLUSIVE License sharing: CUSTOM VIRTUAL

        0 of 3 license(s) used
        ----------------------------------------
        Feature: GlobalZoneEU Version: 21.0 Vendor: ALTAIR
        Start date: 2022-02-17 Expire date: 2023-01-31
        Key type: EXCLUSIVE License sharing: CUSTOM VIRTUAL

        0 of 1000003 license(s) used
        ----------------------------------------
        Feature: HWAIFPBS Version: 21.0 Vendor: ALTAIR
        Start date: 2022-02-17 Expire date: 2023-01-31
        Key type: EXCLUSIVE License sharing: CUSTOM VIRTUAL

        0 of 2147483647 license(s) used
        ----------------------------------------
        Feature: HWAWPF Version: 21.0 Vendor: ALTAIR
        Start date: 2022-02-17 Expire date: 2023-01-31
        Key type: EXCLUSIVE License sharing: CUSTOM VIRTUAL

        0 of 2147483647 license(s) used
        ----------------------------------------
        Feature: HWActivate Version: 21.0 Vendor: ALTAIR
        Start date: 2022-02-17 Expire date: 2023-01-31
        Key type: EXCLUSIVE License sharing: CUSTOM VIRTUAL

        0 of 2147483647 license(s) used
        ----------------------------------------
        Feature: HWFlux2D Version: 21.0 Vendor: ALTAIR
        Start date: 2022-02-17 Expire date: 2023-01-31
        Key type: EXCLUSIVE License sharing: CUSTOM VIRTUAL

        0 of 2147483647 license(s) used
        ----------------------------------------
        Feature: HyperWorks Version: 21.0 Vendor: ALTAIR
        Start date: 2022-02-17 Expire date: 2023-01-31
        Key type: EXCLUSIVE License sharing: CUSTOM VIRTUAL

        0 of 1000000 license(s) used
        """
    )


@fixture
def olicense_output_bad():
    """Some OLicense unparseable  output."""
    return dedent(
        """\
        olixtool 4.8.0 - OLicense XML Status Application
        Copyright (C) 2007-2013 Optimum GmbH, Karlsruhe, Germany

        Server: <123:80:0> (Proxy: <>)

        OlComm 454 Request cannot connect to target
        """
    )


@fixture
def olicense_output():
    """Some OLicense output to parse."""
    return dedent(
        """\
        olixtool 4.8.0 - OLicense XML Status Application
        Copyright (C) 2007-2013 Optimum GmbH, Karlsruhe, Germany

        Server: <138.106.32.97:31212:0> (Proxy: <>)

        List of requested licenses:

        ==============================================
        Application:	cosin
        VersionRange:	0-20231
        Licenser:	cosin scientific software
        Licensee:	Tomas Fjällström
        License-ID:	cosin-faf71fdc@cos550218
        Modules:
          Name; LicenseType; FloatCount; Expiration
          --------------------------------------------
          ftire_adams;         	FreeFloating;	3;	2022-12-31 23:59:59;
            3 FloatsLockedBy:
              sbhyma@RD0087712 #1
              sbhyma@RD0087713 #1
              user22@RD0087713 #1


        ==============================================
        Application:	cosin
        VersionRange:	0-20231
        Licenser:	cosin scientific software
        Licensee:	Tomas Fjällström
        License-ID:	cosin-faf71fdc@cos558164
        Modules:
          Name; LicenseType; FloatCount; Expiration
          --------------------------------------------
          ftire_adams;         	FreeFloating;	1;	2023-02-28 23:59:00;
        """
    )


@fixture
def olicense_output_no_licenses():
    """Some OLicense output with no licenses in use to parse."""
    return dedent(
        """\
        olixtool 4.8.0 - OLicense XML Status Application
        Copyright (C) 2007-2013 Optimum GmbH, Karlsruhe, Germany

        Server: <138.106.32.97:31212:0> (Proxy: <>)

        List of requested licenses:

        ==============================================
        Application:	cosin
        VersionRange:	0-20231
        Licenser:	cosin scientific software
        Licensee:	Tomas Fjällström
        License-ID:	cosin-faf71fdc@cos550218
        Modules:
          Name; LicenseType; FloatCount; Expiration
          --------------------------------------------
          ftire_adams;         	FreeFloating;	3;	2022-12-31 23:59:59;

        ==============================================
        Application:	cosin
        VersionRange:	0-20231
        Licenser:	cosin scientific software
        Licensee:	Tomas Fjällström
        License-ID:	cosin-faf71fdc@cos558164
        Modules:
          Name; LicenseType; FloatCount; Expiration
          --------------------------------------------
          ftire_adams;         	FreeFloating;	1;	2023-02-28 23:59:00;
        """
    )
