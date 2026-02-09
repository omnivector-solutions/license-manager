from prometheus_client import Gauge

LICENSE_TOTAL = Gauge(
    "license_total",
    "Total licenses",
    ["cluster", "product", "feature"],
)

LICENSE_USED = Gauge(
    "license_used",
    "Used licenses",
    ["cluster", "product", "feature"],
)
