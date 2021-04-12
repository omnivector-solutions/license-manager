#!/usr/bin/env python
"""
Simulate flexlm licenses + benchmark tool
"""

# pragma: nocover

import importlib
import random
from textwrap import dedent
import typing

import click
from jinja2 import Template
import tqdm


USERS = "jxezha jbemfv cdxfdn".split()
LICENSE_MAX = 1000

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

    """
    "    Users of abaqus:  (Total of {{total_licenses}} licenses issued;  "
    "    Total of {{ jobs | sum(attribute='license_allocations') }} licenses in use)"
    """

    "abaqus" v62.2, vendor: ABAQUSLM

    floating license

    {% for job in jobs %}
    """
    "    {{job.user}} myserver.example.com /dev/tty (v62.2) (myserver.example.com/24200 12507),"
    " start Thu 10/29 8:09, {{job.license_allocations}} licenses"
    """
    {%- endfor %}
    """
)


def bv(n: int) -> int:
    """
    A cheap way to get some simulation curves with a mode near zero
    """
    return int(n * random.betavariate(alpha=2, beta=3))


def _job_data() -> typing.Tuple[int, typing.Sequence[dict]]:
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
    ret = []
    for n, count in enumerate(rows):
        ret.append(
            {"job_id": n, "user": random.choice(USERS), "license_allocations": count}
        )

    return tot, ret


def _lm_output(job_data: typing.Sequence[typing.Dict]) -> str:
    """
    A template populated with generated jobs
    """
    total, rows = job_data
    tpl = Template(TPL)
    return tpl.render(jobs=rows, total_licenses=total)


def get_parse_fn(s) -> typing.Callable:
    """
    Parse s, a FQPN, to get the parse fn
    """
    parts = s.rsplit(".", 1)
    callable_name = parts.pop(-1)
    if not parts:
        parts = ["__main__"]
    mod = importlib.import_module(parts[0])

    return getattr(mod, callable_name)


@click.group()
def flexlmsim():
    """
    Simulate flexlm licenses + benchmark tool
    """


@flexlmsim.command()
def gen():
    """
    Generate test files
    """
    for n in tqdm.trange(1000):
        with open(f"{n}.txt", "w") as f:
            dat = _job_data()
            txt = _lm_output(dat) + "\n"
            f.write(txt)


@click.option("--parser-fn", "-p", default="licensemanager2.agent.parsing.flexlm.parse")
@click.option("--echo/--no-echo", default=False)
@flexlmsim.command()
def benchmark(parser_fn, echo):
    fn = get_parse_fn(parser_fn)
    print("warmup")
    tr = tqdm.trange(20)
    for n in tr:
        with open(f"{n}.txt") as f:
            ret = fn(f.read())
            if echo:
                tr.write(repr(ret))

    print("main")
    tr = tqdm.trange(20, 1001)
    for n in tr:
        with open(f"{n}.txt") as f:
            ret = fn(f.read())
            if echo:
                tr.write(repr(ret))


# results: this script, vanilla python 3.8, lark parser = 36 files/s
#          this script, pypy3.7, lark parser = 108 files/s
#          this script, vanilla python 3.8, re parser = 15355 files/s
#          this script, pypy3.7, re parser = 5207 files/s
