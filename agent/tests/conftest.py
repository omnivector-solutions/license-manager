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
    ClusterSchema,
    ConfigurationSchema,
    FeatureSchema,
    InventorySchema,
    JobSchema,
    LicenseServerSchema,
    LicenseServerType,
    ProductSchema,
)
# from lm_agent.backend_utils.models import BackendConfigurationRow
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
def clusters():
    """Some cluster reponse examples."""
    return [
        {
            "id": 1,
            "name": "Cluster 1",
            "client_id": "cluster1",
            "configurations": [
                {
                    "id": 1,
                    "name": "Abaqus",
                    "cluster_id": 1,
                    "features": [
                        {
                            "id": 1,
                            "name": "abaqus",
                            "product": {"id": 1, "name": "abaqus"},
                            "config_id": 1,
                            "reserved": 100,
                            "inventory": {"id": 1, "feature_id": 2, "total": 123, "used": 12},
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
                    "cluster_id": 1,
                    "features": [
                        {
                            "id": 2,
                            "name": "converge_super",
                            "product": {"id": 2, "name": "converge"},
                            "config_id": 2,
                            "reserved": 0,
                            "inventory": {"id": 2, "feature_id": 2, "total": 500, "used": 50},
                        }
                    ],
                    "license_servers": [{"id": 2, "config_id": 2, "host": "licserv0002", "port": 2345}],
                    "grace_time": 123,
                    "type": "rlm",
                },
            ],
            "jobs": [
                {
                    "id": 1,
                    "slurm_job_id": "123",
                    "cluster_id": 1,
                    "username": "string",
                    "lead_host": "string",
                    "bookings": [
                        {"id": 1, "job_id": 1, "feature_id": 1, "quantity": 12},
                        {"id": 2, "job_id": 1, "feature_id": 2, "quantity": 50},
                    ],
                }
            ],
        },
        {
            "id": 2,
            "name": "Cluster 2",
            "client_id": "cluster2",
            "configurations": [
                {
                    "id": 3,
                    "name": "Configuration 2",
                    "cluster_id": 2,
                    "features": [
                        {
                            "id": 4,
                            "name": "Feature 3",
                            "product": {"id": 5, "name": "Product 3"},
                            "config_id": 3,
                            "reserved": 20,
                            "inventory": {"id": 6, "feature_id": 4, "total": 200, "used": 15},
                        },
                        {
                            "id": 7,
                            "name": "Feature 4",
                            "product": {"id": 8, "name": "Product 4"},
                            "config_id": 3,
                            "reserved": 30,
                            "inventory": {"id": 9, "feature_id": 7, "total": 300, "used": 25},
                        },
                    ],
                    "license_servers": [
                        {"id": 10, "config_id": 3, "host": "licserv2_1", "port": 1234},
                        {"id": 11, "config_id": 3, "host": "licserv2_2", "port": 5678},
                    ],
                    "grace_time": 60,
                    "type": "flexlm",
                }
            ],
            "jobs": [
                {
                    "id": 5,
                    "slurm_job_id": "456",
                    "cluster_id": 2,
                    "username": "user2",
                    "lead_host": "host2",
                    "bookings": [
                        {"id": 12, "job_id": 5, "feature_id": 4, "quantity": 10},
                        {"id": 13, "job_id": 5, "feature_id": 7, "quantity": 8},
                    ],
                },
                {
                    "id": 6,
                    "slurm_job_id": "789",
                    "cluster_id": 2,
                    "username": "user3",
                    "lead_host": "host3",
                    "bookings": [
                        {"id": 14, "job_id": 6, "feature_id": 4, "quantity": 5},
                        {"id": 15, "job_id": 6, "feature_id": 7, "quantity": 17},
                    ],
                },
            ],
        },
    ]


@fixture
def parsed_clusters():
    return [
        ClusterSchema(
            id=1,
            name="Cluster 1",
            client_id="cluster1",
            configurations=[
                ConfigurationSchema(
                    id=1,
                    name="Abaqus",
                    cluster_id=1,
                    features=[
                        FeatureSchema(
                            id=1,
                            name="abaqus",
                            product=ProductSchema(id=1, name="abaqus"),
                            config_id=1,
                            reserved=100,
                            inventory=InventorySchema(id=1, feature_id=2, total=123, used=12),
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
                    cluster_id=1,
                    features=[
                        FeatureSchema(
                            id=2,
                            name="converge_super",
                            product=ProductSchema(id=2, name="converge"),
                            config_id=2,
                            reserved=0,
                            inventory=InventorySchema(id=2, feature_id=2, total=500, used=50),
                        )
                    ],
                    license_servers=[
                        LicenseServerSchema(id=2, config_id=2, host="licserv0002", port=2345),
                    ],
                    grace_time=123,
                    type=LicenseServerType.RLM,
                ),
            ],
            jobs=[
                JobSchema(
                    id=1,
                    slurm_job_id="123",
                    cluster_id=1,
                    username="string",
                    lead_host="string",
                    bookings=[
                        BookingSchema(id=1, job_id=1, feature_id=1, quantity=12),
                        BookingSchema(id=2, job_id=1, feature_id=2, quantity=50),
                    ],
                )
            ],
        ),
        ClusterSchema(
            id=2,
            name="Cluster 2",
            client_id="cluster2",
            configurations=[
                ConfigurationSchema(
                    id=3,
                    name="Configuration 2",
                    cluster_id=2,
                    features=[
                        FeatureSchema(
                            id=4,
                            name="Feature 3",
                            product=ProductSchema(id=5, name="Product 3"),
                            config_id=3,
                            reserved=20,
                            inventory=InventorySchema(id=6, feature_id=4, total=200, used=15),
                        ),
                        FeatureSchema(
                            id=7,
                            name="Feature 4",
                            product=ProductSchema(id=8, name="Product 4"),
                            config_id=3,
                            reserved=30,
                            inventory=InventorySchema(id=9, feature_id=7, total=300, used=25),
                        ),
                    ],
                    license_servers=[
                        LicenseServerSchema(id=10, config_id=3, host="licserv2_1", port=1234),
                        LicenseServerSchema(id=11, config_id=3, host="licserv2_2", port=5678),
                    ],
                    grace_time=60,
                    type=LicenseServerType.FLEXLM,
                ),
            ],
            jobs=[
                JobSchema(
                    id=5,
                    slurm_job_id="456",
                    cluster_id=2,
                    username="user2",
                    lead_host="host2",
                    bookings=[
                        BookingSchema(id=12, job_id=5, feature_id=4, quantity=10),
                        BookingSchema(id=13, job_id=5, feature_id=7, quantity=8),
                    ],
                ),
                JobSchema(
                    id=6,
                    slurm_job_id="789",
                    cluster_id=2,
                    username="user3",
                    lead_host="host3",
                    bookings=[
                        BookingSchema(id=14, job_id=6, feature_id=4, quantity=5),
                        BookingSchema(id=15, job_id=6, feature_id=7, quantity=17),
                    ],
                ),
            ],
        ),
    ]


@fixture
def bookings():
    """Bookings returned by /booking/all endpoint."""
    return [
        {
            "id": 1,
            "job_id": 123,
            "product_feature": "product.feature",
            "booked": 15,
            "config_id": 1,
            "lead_host": "host1",
            "user_name": "user1",
            "cluster_name": "cluster1",
        },
        {
            "id": 2,
            "job_id": 123,
            "product_feature": "product.feature",
            "booked": 17,
            "config_id": 1,
            "lead_host": "host1",
            "user_name": "user1",
            "cluster_name": "cluster2",
        },
        {
            "id": 3,
            "job_id": 123,
            "product_feature": "product.feature",
            "booked": 4,
            "config_id": 1,
            "lead_host": "host1",
            "user_name": "user1",
            "cluster_name": "cluster3",
        },
        {
            "id": 4,
            "job_id": 123,
            "product_feature": "product.feature",
            "booked": 67,
            "config_id": 1,
            "lead_host": "host1",
            "user_name": "user1",
            "cluster_name": "cluster3",
        },
        {
            "id": 4,
            "job_id": 123,
            "product_feature": "product2.feature2",
            "booked": 1,
            "config_id": 2,
            "lead_host": "host1",
            "user_name": "user1",
            "cluster_name": "cluster4",
        },
    ]


@fixture
def cluster_update_payload():
    """A response returned by /license/cluster_update endpoint."""
    return [
        {
            "product_feature": "product.feature",
            "bookings_sum": 100,
            "license_total": 1000,
            "license_used": 200,
        },
    ]


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
def lmstat_output_bad():
    """Some unparseable lmstat output."""
    return dedent(
        """\
        lmstat - Copyright (c) 1989-2004 by Macrovision Corporation. All rights reserved.
        Flexible License Manager status on Wed 03/31/2021 09:12

        Error getting status: Cannot connect to license server (-15,570:111 "Connection refused")
        """
    )


@fixture
def lmstat_output():
    """Some lmstat output to parse."""
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
def lmstat_output_no_licenses():
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
