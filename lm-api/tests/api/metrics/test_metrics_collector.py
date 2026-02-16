from unittest.mock import MagicMock, patch

from prometheus_client.core import CollectorRegistry
from pytest import fixture

from lm_api.metrics import MetricsCollector
from lm_api.security import IdentityPayload


class TestMetricsCollector:
    """
    Test functionality of MetricsCollector.
    """

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
        mock_get_session.assert_called_once_with(override_db_name=None, asynchronous=False)
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


class TestMetricsCollectorMultiTenancy:
    """
    Test multi-tenancy functionality of MetricsCollector.
    """

    @fixture
    def identity_payload(self):
        """
        Create a mock identity payload for multi-tenancy tests.
        """
        payload = MagicMock(spec=IdentityPayload)
        payload.organization_id = "test-org-123"
        payload.email = "test@example.com"
        return payload

    @fixture
    def collector_with_identity(self, identity_payload):
        """
        Create a collector instance with identity payload for multi-tenancy tests.
        """
        return MetricsCollector(identity_payload=identity_payload)

    @fixture
    def tenant1_identity(self):
        """
        Mock identity for tenant 1.
        """
        payload = MagicMock(spec=IdentityPayload)
        payload.organization_id = "tenant-1"
        payload.email = "user@tenant1.com"
        return payload

    @fixture
    def tenant2_identity(self):
        """
        Mock identity for tenant 2.
        """
        payload = MagicMock(spec=IdentityPayload)
        payload.organization_id = "tenant-2"
        payload.email = "user@tenant2.com"
        return payload

    def test_collector_initialization_with_identity(self, collector_with_identity, identity_payload):
        """
        Test that collector initializes properly with identity payload.
        """
        assert isinstance(collector_with_identity.registry, CollectorRegistry)
        assert collector_with_identity.identity_payload == identity_payload
        assert collector_with_identity.identity_payload.organization_id == "test-org-123"

        registered_collectors = list(collector_with_identity.registry._collector_to_names.keys())
        assert collector_with_identity in registered_collectors

    @patch("lm_api.metrics.engine_factory.get_session")
    def test_get_metrics_data__with_multi_tenancy_enabled(
        self, mock_get_session, collector_with_identity, identity_payload, tweak_settings
    ):
        """
        Test metrics data retrieval with multi-tenancy enabled.
        """
        with tweak_settings(MULTI_TENANCY_ENABLED=True):
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session

            mock_rows = [MagicMock(), MagicMock()]
            collector_with_identity._collect_feature_metrics = MagicMock(return_value=mock_rows)

            rows = collector_with_identity._get_metrics_data()

            assert rows == mock_rows

            mock_get_session.assert_called_once_with(override_db_name="test-org-123", asynchronous=False)
            collector_with_identity._collect_feature_metrics.assert_called_once_with(mock_session)
            mock_session.close.assert_called_once()

    @patch("lm_api.metrics.engine_factory.get_session")
    def test_get_metrics_data__with_multi_tenancy_disabled(
        self, mock_get_session, collector_with_identity, tweak_settings
    ):
        """
        Test metrics data retrieval with multi-tenancy disabled (should ignore organization_id).
        """
        with tweak_settings(MULTI_TENANCY_ENABLED=False):
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session

            mock_rows = [MagicMock(), MagicMock()]
            collector_with_identity._collect_feature_metrics = MagicMock(return_value=mock_rows)

            rows = collector_with_identity._get_metrics_data()

            assert rows == mock_rows
            mock_get_session.assert_called_once_with(override_db_name=None, asynchronous=False)
            collector_with_identity._collect_feature_metrics.assert_called_once_with(mock_session)
            mock_session.close.assert_called_once()

    @patch("lm_api.metrics.engine_factory.get_session")
    def test_get_metrics_data__multi_tenant_session_error(
        self, mock_get_session, collector_with_identity, tweak_settings
    ):
        """
        Test handling of session creation errors in multi-tenant environment.
        """
        with tweak_settings(MULTI_TENANCY_ENABLED=True):
            mock_get_session.side_effect = Exception("Multi-tenant session creation failed")

            rows = collector_with_identity._get_metrics_data()

            assert len(rows) == 0
            mock_get_session.assert_called_once_with(override_db_name="test-org-123", asynchronous=False)

    def test_collect_with_multi_tenant_data(self, collector_with_identity, tweak_settings):
        """
        Test the collect method with multi-tenant setup.
        """
        with tweak_settings(MULTI_TENANCY_ENABLED=True):
            mock_rows = [
                MagicMock(
                    cluster="tenant-cluster",
                    product="tenant-product",
                    feature="tenant-feature",
                    total=500,
                    used=100,
                ),
            ]
            collector_with_identity._get_metrics_data = MagicMock(return_value=mock_rows)

            metric_families = list(collector_with_identity.collect())

            assert len(metric_families) == 2

            total_metrics = metric_families[0]
            used_metrics = metric_families[1]

            assert len(total_metrics.samples) == 1
            assert len(used_metrics.samples) == 1

            assert total_metrics.samples[0].value == 500
            assert used_metrics.samples[0].value == 100
            assert "tenant-cluster" in str(total_metrics.samples[0].labels)
            assert "tenant-product" in str(total_metrics.samples[0].labels)
            assert "tenant-feature" in str(total_metrics.samples[0].labels)

    @patch("lm_api.metrics.engine_factory.get_session")
    def test_different_tenants_get_different_sessions(
        self, mock_get_session, tenant1_identity, tenant2_identity, tweak_settings
    ):
        """
        Test that different tenants result in different database session calls.
        """
        with tweak_settings(MULTI_TENANCY_ENABLED=True):
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session

            collector1 = MetricsCollector(tenant1_identity)
            collector2 = MetricsCollector(tenant2_identity)

            collector1._collect_feature_metrics = MagicMock(return_value=[])
            collector2._collect_feature_metrics = MagicMock(return_value=[])

            collector1._get_metrics_data()
            collector2._get_metrics_data()

            assert mock_get_session.call_count == 2
            calls = mock_get_session.call_args_list

            assert calls[0].kwargs["override_db_name"] == "tenant-1"
            assert calls[1].kwargs["override_db_name"] == "tenant-2"
            assert all(not call.kwargs["asynchronous"] for call in calls)

    def test_multi_tenancy_disabled_ignores_organization_id(
        self, tenant1_identity, tenant2_identity, tweak_settings
    ):
        """
        Test that when multi-tenancy is disabled, organization_id is ignored.
        """
        with tweak_settings(MULTI_TENANCY_ENABLED=False):
            with patch("lm_api.metrics.engine_factory.get_session") as mock_get_session:
                mock_session = MagicMock()
                mock_get_session.return_value = mock_session

                collector1 = MetricsCollector(tenant1_identity)
                collector2 = MetricsCollector(tenant2_identity)

                collector1._collect_feature_metrics = MagicMock(return_value=[])
                collector2._collect_feature_metrics = MagicMock(return_value=[])

                collector1._get_metrics_data()
                collector2._get_metrics_data()

                assert mock_get_session.call_count == 2
                calls = mock_get_session.call_args_list

                assert calls[0].kwargs["override_db_name"] is None
                assert calls[1].kwargs["override_db_name"] is None
                assert all(not call.kwargs["asynchronous"] for call in calls)

    def test_tenant_isolation_in_metrics_collection(self, tenant1_identity, tenant2_identity, tweak_settings):
        """
        Test that different tenants collect isolated metrics data.
        """
        with tweak_settings(MULTI_TENANCY_ENABLED=True):
            collector1 = MetricsCollector(tenant1_identity)
            collector2 = MetricsCollector(tenant2_identity)

            tenant1_data = [
                MagicMock(cluster="tenant1-cluster", product="prod1", feature="feat1", total=100, used=10)
            ]
            tenant2_data = [
                MagicMock(cluster="tenant2-cluster", product="prod2", feature="feat2", total=200, used=20)
            ]

            collector1._get_metrics_data = MagicMock(return_value=tenant1_data)
            collector2._get_metrics_data = MagicMock(return_value=tenant2_data)

            metrics1 = list(collector1.collect())
            metrics2 = list(collector2.collect())

            assert len(metrics1) == 2
            assert len(metrics2) == 2

            assert metrics1[0].samples[0].value == 100  # total
            assert metrics1[1].samples[0].value == 10  # used
            assert "tenant1-cluster" in str(metrics1[0].samples[0].labels)

            assert metrics2[0].samples[0].value == 200  # total
            assert metrics2[1].samples[0].value == 20  # used
            assert "tenant2-cluster" in str(metrics2[0].samples[0].labels)
