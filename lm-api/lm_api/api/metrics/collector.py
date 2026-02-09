from sqlalchemy import select

from lm_api.api.models.configuration import Configuration
from lm_api.api.models.feature import Feature
from lm_api.api.models.product import Product


async def collect_feature_metrics(session):
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
    )

    result = await session.execute(stmt)
    return result.all()
