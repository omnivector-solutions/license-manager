from pytest import mark

from lm_api.api.metrics.collector import collect_feature_metrics


@mark.asyncio
async def test_collect_feature_metrics__success(synth_session, metrics_data):
    fetched = await collect_feature_metrics(synth_session)

    assert len(fetched) == 2

    abaqus, converge = fetched

    assert abaqus.cluster == "dummy1"
    assert abaqus.product == "abaqus"
    assert abaqus.feature == "abaqus"
    assert abaqus.total == 1000
    assert abaqus.used == 25

    assert converge.cluster == "dummy2"
    assert converge.product == "converge"
    assert converge.feature == "converge_super"
    assert converge.total == 1000
    assert converge.used == 250


@mark.asyncio
async def test_collect_feature_metrics__empty_db(synth_session):
    fetched = await collect_feature_metrics(synth_session)

    assert len(fetched) == 0
