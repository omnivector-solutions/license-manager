#!/usr/bin/env python3
"""
Reconcile functionality live here.
"""
from httpx import ConnectError

from licensemanager2.agent import (
    log as logger,
    tokenstat,
)
from licensemanager2.agent.forward import async_client


RECONCILE_URL_PATH = "/api/v1/license/reconcile"


async def reconcile():
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
