"""
Test the flexlm parser
"""

import random
from textwrap import dedent

from jinja2 import Template
from pytest import fixture


USERS = "jxezha jbemfv cdxfdn".split()

TPL = dedent(
    """\
    lmutil - Copyright (c) 1989-2012 Flexera Software LLC. All Rights Reserved.
    Flexible License Manager status on Thu 10/29/2020 17:44

    License server status: server1,server2,server3
        License file(s) on server1: f:\\flexlm\\AbaqusLM\\License\\license.dat:

    server1: license server UP v11.13
    server2: license server UP (MASTER) v11.13
    server3: license server UP v11.13

    Vendor daemon status (on server2):
    ABAQUSLM: UP v11.13

    Feature usage info:

    Users of abaqus:  (Total of {{total_licenses}} licenses issued;  Total of {{ jobs | sum(attribute='license_allocations') }} licenses in use)

    "abaqus" v62.2, vendor: ABAQUSLM

    floating license

    {% for job in jobs %}
        {{job.user}} myserver.example.com /dev/tty (v62.2) (myserver.example.com/24200 12507), start Thu 10/29 8:09, {{job.license_allocations}} licenses
    {%- endfor %}
    """
)


LICENSE_MAX = 1000


def bv(n: int) -> int:
    """
    A cheap way to get some simulation curves with a mode near zero
    """
    return int(n * random.betavariate(alpha=2, beta=3))


def _job_data():
    """
    Generate a data set of random jobs

    The randomly chosen load will skew near the lower end, but also has a tiny spike at the max since the
    license server cannot give out a number of licenses >1000
    """
    rows = [bv(50) for n in range(bv(50))]
    tot = sum(rows)
    while tot - LICENSE_MAX > 0:
        del rows[-1]
        tot = sum(rows)
    rows = [
        {"job_id": n, "user": random.choice(USERS), "license_allocations": count}
        for (n, count) in enumerate(rows)
    ]
    return tot, rows


job_data = fixture(_job_data)


def _lm_output(job_data):
    """
    A full template populated with jobs
    """
    total, rows = job_data
    tpl = Template(TPL)
    return tpl.render(jobs=rows, total_licenses=total)


lm_output = fixture(_lm_output)


def test_parse(lm_output):
    assert 0
