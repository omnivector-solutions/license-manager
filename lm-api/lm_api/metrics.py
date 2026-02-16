from typing import Iterator, Optional

from loguru import logger
from prometheus_client.core import CollectorRegistry, GaugeMetricFamily
from prometheus_client.registry import Collector
from sqlalchemy import select
from sqlalchemy.orm import Session

from lm_api.api.models.configuration import Configuration
from lm_api.api.models.feature import Feature
from lm_api.api.models.product import Product
from lm_api.config import settings
from lm_api.database import engine_factory
from lm_api.security import IdentityPayload


class MetricsCollector(Collector):
    """
    Custom Prometheus collector for license metrics.

    This collector queries the database for license usage information and formats it for Prometheus.
    The metrics collected include total licenses available and licenses currently in use,
    labeled by cluster, product, and feature.

    The collector is registered with a CollectorRegistry, which is used by the /lm/metrics endpoint.

    If multi-tenancy is enabled, the collector uses the identity payload to determine which database to query,
    ensuring that it collects metrics for the correct tenant.
    """

    def __init__(self, identity_payload: Optional[IdentityPayload] = None):
        self.registry = CollectorRegistry()
        self.registry.register(self)
        self.identity_payload = identity_payload

    def _collect_feature_metrics(self, session: Session):
        """
        Collect feature metrics from database.
        """
        stmt = (
            select(
                Configuration.cluster_client_id.label("cluster"),
                Product.name.label("product"),
                Feature.name.label("feature"),
                Feature.total,
                Feature.used,
            )
            .join(Feature, Feature.config_id == Configuration.id)
            .join(Product, Feature.product_id == Product.id)
            .order_by(Configuration.cluster_client_id, Product.name, Feature.name)
        )

        result = session.execute(stmt)
        return result.all()

    def _get_metrics_data(self):
        """
        Get metrics data from database.

        If multi-tenancy is enabled, the database is determined by the
        organization_id in the identity payload.
        """
        try:
            override_db_name = None
            if self.identity_payload and settings.MULTI_TENANCY_ENABLED:
                override_db_name = self.identity_payload.organization_id

            session = engine_factory.get_session(override_db_name=override_db_name, asynchronous=False)
            try:
                return self._collect_feature_metrics(session)
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Failed to get metrics data: {e}")
            return []

    def collect(self) -> Iterator[GaugeMetricFamily]:
        """
        Collect metrics for Prometheus.
        """
        rows = self._get_metrics_data()

        total = GaugeMetricFamily(
            "license_total",
            "Total licenses available",
            labels=["cluster", "product", "feature"],
        )

        used = GaugeMetricFamily(
            "license_used",
            "Licenses currently in use",
            labels=["cluster", "product", "feature"],
        )

        for r in rows:
            labels = [r.cluster, r.product, r.feature]
            total.add_metric(labels, r.total or 0)
            used.add_metric(labels, r.used or 0)

        logger.debug(f"Collected metrics for {len(rows)} features")

        yield total
        yield used
