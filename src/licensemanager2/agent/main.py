"""
License-manager agent, command line entrypoint

Run with e.g. `uvicorn licensemanager2.agent.main:app`
"""
from itertools import cycle
import logging
import typing

from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every
from httpx import ConnectError

from licensemanager2.agent import (
    init_logging,
    log as logger,
    tokenstat,
)
from licensemanager2.common_api import OK

from licensemanager2.agent.api import api_v1
from licensemanager2.agent.forward import async_client
from licensemanager2.agent.settings import SETTINGS


RECONCILE_URL_PATH = "/api/v1/license/reconcile"


def generate_primes():
    """
    A series of prime numbers for generating non-overlapping time intervals
    """
    ret = [
        int(i)
        for i in (
            "877 1019 1153 1297 1453 1597 1741 1901 2063 2221 2371 2539 2689 2833 3001 3187 3343 3517"
            " 3659 3823 4001 4153 4327 4507 4663 4861 5009 5189 5393 5527 5701 5861 6067 6229 6373 6577"
            " 6763 6947 7109 7307 7507 7649 7841 8039 8221 8389 8599 8747 8933 9127 9293 9461 9643 9817"
        ).split()
    ]
    for n in cycle(ret):
        yield n


primes = generate_primes()


def interval_prime_offset(seconds: typing.Union[int, float]) -> float:
    """
    Produce a number of seconds offset by a prime number

    This creates a number of seconds from s+0.877 to s+9.817. The resulting
    intervals will not overlap one another, even for same values of `seconds'

    This helps you to detect timed patterns in your logs based on the ms
    interval between events, even if the timed event itself doesn't log
    anything.

    NOTE: the generator only has 54 primes, so if you need more than 54
    similar timers, maybe improve on this.
    """
    return next(primes) / 1000.0 + seconds


app = FastAPI()
# app.add_middleware(
#     CORSMiddleware,
#     allow_origin_regex=SETTINGS.ALLOW_ORIGINS_REGEX,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
# app.add_middleware(TrustedHostMiddleware)
# app.add_middleware(ProxyHeadersMiddleware)
# app.add_middleware(RateLimitMiddleware)


@app.get("/")
async def root():
    """
    Well, *something* should happen here.
    """
    return OK()


@app.get("/health")
async def health():
    """
    Healthcheck, for health monitors in the deployed environment
    """
    return OK()


@app.on_event("startup")
def begin_logging():
    """
    Configure logging
    """
    init_logging("license-manager-agent")

    level = getattr(logging, SETTINGS.LOG_LEVEL)
    logger.setLevel(level)

    # as a developer you'll run this with uvicorn,
    # which takes over logging.
    uvicorn = logging.getLogger("uvicorn")
    if uvicorn.handlers:  # pragma: nocover
        logger.addHandler(uvicorn.handlers[0])

    logger.info(f"Forwarding requests ⇒ {SETTINGS.BACKEND_BASE_URL}")


@app.on_event("startup")
@repeat_every(
    seconds=interval_prime_offset(SETTINGS.STAT_INTERVAL),
    logger=logger,
    raise_exceptions=True,
)
async def collect_stats():
    """
    Periodically get license stats and report them to the backend
    """
    logger.info("⏲️ 📒 begin stat collection")
    rep = await tokenstat.report()
    if not rep:
        logger.error(
            "No license data could be collected, check that tools are installed "
            "correctly and the right hosts/ports are configured in settings"
        )
        return

    client = async_client()
    path = RECONCILE_URL_PATH
    try:
        r = await async_client().patch(path, json=rep)
    except ConnectError as e:
        logger.error(f"{client.base_url}{path}: {e}")
        return

    if r.status_code == 200:
        logger.info(f"backend updated: {len(rep)} feature(s)")
    else:
        logger.error(f"{r.url}: {r.status_code}!: {r.text}")

    return r


app.include_router(api_v1, prefix="/api/v1")
