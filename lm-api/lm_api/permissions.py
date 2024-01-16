from enum import Enum


class Permissions(str, Enum):
    """
    Describe the permissions that may be used for protecting LM Backend routes.
    """

    LICENSE_SERVER_VIEW = "license-manager:license-server:view"
    LICENSE_SERVER_EDIT = "license-manager:license-server:edit"

    CLUSTER_VIEW = "license-manager:cluster:view"
    CLUSTER_EDIT = "license-manager:cluster:edit"

    CONFIG_VIEW = "license-manager:config:view"
    CONFIG_EDIT = "license-manager:config:edit"

    PRODUCT_VIEW = "license-manager:product:view"
    PRODUCT_EDIT = "license-manager:product:edit"

    FEATURE_VIEW = "license-manager:feature:view"
    FEATURE_EDIT = "license-manager:feature:edit"

    JOB_VIEW = "license-manager:job:view"
    JOB_EDIT = "license-manager:job:edit"

    BOOKING_VIEW = "license-manager:booking:view"
    BOOKING_EDIT = "license-manager:booking:edit"
