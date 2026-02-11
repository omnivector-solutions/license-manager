import asyncio
from unittest.mock import AsyncMock, patch

from pytest import mark, raises

from lm_api.api.metrics.updater import MetricsManager
from lm_api.api.schemas.metrics import LICENSE_TOTAL, LICENSE_USED


@mark.asyncio
async def test_update_metrics_populates_prometheus(metrics_data, synth_session):
    metrics_manager = MetricsManager()

    count = await metrics_manager.update(synth_session)

    assert count == 2

    total_abaqus = LICENSE_TOTAL.labels(
        cluster="dummy1",
        product="abaqus",
        feature="abaqus",
    )._value.get()

    used_abaqus = LICENSE_USED.labels(
        cluster="dummy1",
        product="abaqus",
        feature="abaqus",
    )._value.get()

    assert total_abaqus == 1000
    assert used_abaqus == 25

    total_converge = LICENSE_TOTAL.labels(
        cluster="dummy2",
        product="converge",
        feature="converge_super",
    )._value.get()

    used_converge = LICENSE_USED.labels(
        cluster="dummy2",
        product="converge",
        feature="converge_super",
    )._value.get()

    assert total_converge == 1000
    assert used_converge == 250


@mark.asyncio
async def test_update_metrics_returns_zero_when_no_data(synth_session):
    metrics_manager = MetricsManager()

    count = await metrics_manager.update(synth_session)

    assert count == 0


@mark.asyncio
async def test_metrics_manager_lifecycle():
    metrics_manager = MetricsManager()

    assert not metrics_manager.is_running

    await metrics_manager.start(interval=3600)
    assert metrics_manager.is_running

    await metrics_manager.stop()
    assert not metrics_manager.is_running


@mark.asyncio
async def test_update_doesnt_close_provided_session(metrics_data, synth_session):
    close_mock = AsyncMock()
    synth_session.close = close_mock
    metrics_manager = MetricsManager()

    count = await metrics_manager.update(synth_session)

    assert count == 2
    close_mock.assert_not_called()


@mark.asyncio
@patch("lm_api.api.metrics.updater.collect_feature_metrics")
@patch("lm_api.api.metrics.updater.engine_factory.get_session")
async def test_update_closes_created_internally_session(mock_get_session, mock_collect):
    metrics_manager = MetricsManager()

    mock_session = AsyncMock()
    mock_get_session.return_value = mock_session

    mock_collect.return_value = []

    await metrics_manager.update()

    mock_session.close.assert_called_once()


@mark.asyncio
@patch("lm_api.api.metrics.updater.collect_feature_metrics")
async def test_update_handles_cancelled_error(mock_collect):
    metrics_manager = MetricsManager()

    mock_collect.side_effect = asyncio.CancelledError("Task cancelled")

    with raises(asyncio.CancelledError):
        await metrics_manager.update()


@mark.asyncio
@patch("lm_api.api.metrics.updater.collect_feature_metrics")
@patch("lm_api.api.metrics.updater.logger")
async def test_update_handles_exceptions_and_logs(mock_logger, mock_collect):
    metrics_manager = MetricsManager()

    mock_collect.side_effect = RuntimeError("Database error")
    with raises(RuntimeError):
        await metrics_manager.update()

    mock_logger.exception.assert_called_once()
    called_args = mock_logger.exception.call_args[0][0]
    assert "Metrics update failed: Database error" in called_args


@mark.asyncio
async def test_run_exits_on_stop_event():
    metrics_manager = MetricsManager()

    metrics_manager.update = AsyncMock(return_value=0)
    metrics_manager._stop_event.set()

    await metrics_manager.run(interval=1)

    metrics_manager.update.assert_not_called()


@mark.asyncio
async def test_stop_sets_event_and_waits_for_task():
    manager = MetricsManager()

    async def fake_update():
        await asyncio.sleep(0.01)
        return 1

    manager.update = fake_update

    await manager.start(interval=60)

    assert manager.is_running

    with patch.object(manager._stop_event, "set") as mock_set:
        await manager.stop()

    mock_set.assert_called_once()
    assert manager.task is None
