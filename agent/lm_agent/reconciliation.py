#!/usr/bin/env python3
"""
Reconciliation functionality live here.
"""
from fastapi import HTTPException, status
from httpx import ConnectError

from lm_agent.forward import async_client
from lm_agent.logs import logger
from lm_agent.tokenstat import report

RECONCILE_URL_PATH = "/api/v1/license/reconcile"


async def reconcile():
    """Generate the report and reconcile the license feature token usage."""
    # Generate the report.
    logger.info("Beginning forced reconciliation process")
    rep = await report()
    if not rep:
        logger.error(
            "No license data could be collected, check that tools are installed "
            "correctly and the right hosts/ports are configured in settings"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="report failed",
        )

    # Send the report to the backend.
    client = async_client()
    path = RECONCILE_URL_PATH
    try:
        r = await async_client().patch(path, json=rep)
    except ConnectError as e:
        logger.error(f"{client.base_url}{path}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="connection to reconcile api failed",
        )

    if r.status_code != 200:
        logger.error(f"{r.url}: {r.status_code}!: {r.text}")
        raise HTTPException(
            status_code=r.status_code,
            detail="reconciliation failed",
        )

    logger.info("Forced reconciliation succeeded. backend updated: {len(rep)} feature(s)")
    return r
