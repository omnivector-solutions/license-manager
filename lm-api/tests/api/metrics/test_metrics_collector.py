from unittest.mock import MagicMock, patch

from prometheus_client.core import CollectorRegistry
from pytest import fixture

from lm_api.metrics import MetricsCollector


class TestMetricsCollector:
    @fixture
    def collector(self):
        """
        Create a fresh collector instance for each test.
        """
        return MetricsCollector()

    def test_collector_initialization(self, collector):
        """
        Test that collector initializes properly.
        """
        assert isinstance(collector.registry, CollectorRegistry)

        registered_collectors = list(collector.registry._collector_to_names.keys())
        assert collector in registered_collectors

    async def test_collect_feature_metrics__success(self, collector, synth_sync_session, metrics_data):
        """
        Test successful database query execution using a sync session.
        """
        rows = collector._collect_feature_metrics(synth_sync_session)

        assert len(rows) == 2
        assert rows[0].cluster == "dummy1"
        assert rows[0].product == "abaqus"
        assert rows[0].feature == "abaqus"
        assert rows[0].total == 1000
        assert rows[0].used == 25

        assert rows[1].cluster == "dummy2"
        assert rows[1].product == "converge"
        assert rows[1].feature == "converge_super"
        assert rows[1].total == 1000
        assert rows[1].used == 250

    def test_collect_feature_metrics__empty_result(self, synth_sync_session, collector):
        """
        Test when database query returns no results.
        """
        rows = collector._collect_feature_metrics(synth_sync_session)
        assert len(rows) == 0

    @patch("lm_api.metrics.engine_factory.get_session")
    def test_get_metrics_data__success(self, mock_get_session, collector):
        """
        Test successful retrieval of metrics data.
        """
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        mock_rows = [MagicMock(), MagicMock()]
        collector._collect_feature_metrics = MagicMock(return_value=mock_rows)

        rows = collector._get_metrics_data()

        assert rows == mock_rows
        mock_get_session.assert_called_once_with(asynchronous=False)
        collector._collect_feature_metrics.assert_called_once_with(mock_session)
        mock_session.close.assert_called_once()

    @patch("lm_api.metrics.engine_factory.get_session")
    def test_get_metrics_data_session__error(self, mock_engine_factory, collector):
        """
        Test handling of session creation errors.
        """
        mock_engine_factory.get_session.side_effect = Exception("Session creation failed")

        rows = collector._get_metrics_data()

        assert len(rows) == 0

    def test_collect_with_no_data(self, collector):
        """
        Test the collect method when no data is available.
        """
        collector._get_metrics_data = MagicMock(return_value=[])

        metric_families = list(collector.collect())

        assert len(metric_families) == 2

        total_metrics = metric_families[0]
        used_metrics = metric_families[1]

        assert total_metrics.name == "license_total"
        assert used_metrics.name == "license_used"
        assert len(total_metrics.samples) == 0
        assert len(used_metrics.samples) == 0

    def test_collect_with_real_data(self, collector, metrics_data):
        """
        Test the collect method with real data from the database.
        """
        metric_families = list(collector.collect())

        assert len(metric_families) == 2

        total_metrics = metric_families[0]
        used_metrics = metric_families[1]

        assert len(total_metrics.samples) == 2
        assert len(used_metrics.samples) == 2
