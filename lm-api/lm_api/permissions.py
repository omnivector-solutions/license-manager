from enum import Enum


class Permissions(str, Enum):
    """
    Describe the permissions that may be used for protecting LM Backend routes.
    """

    ADMIN = "license-manager:admin"

    STATUS_UPDATE = "license-manager:status:update"
    STATUS_READ = "license-manager:status:read"

    LICENSE_SERVER_CREATE = "license-manager:license-server:create"
    LICENSE_SERVER_READ = "license-manager:license-server:read"
    LICENSE_SERVER_UPDATE = "license-manager:license-server:update"
    LICENSE_SERVER_DELETE = "license-manager:license-server:delete"

    CONFIG_CREATE = "license-manager:config:create"
    CONFIG_READ = "license-manager:config:read"
    CONFIG_UPDATE = "license-manager:config:update"
    CONFIG_DELETE = "license-manager:config:delete"

    PRODUCT_CREATE = "license-manager:product:create"
    PRODUCT_READ = "license-manager:product:read"
    PRODUCT_UPDATE = "license-manager:product:update"
    PRODUCT_DELETE = "license-manager:product:delete"

    FEATURE_CREATE = "license-manager:feature:create"
    FEATURE_READ = "license-manager:feature:read"
    FEATURE_UPDATE = "license-manager:feature:update"
    FEATURE_DELETE = "license-manager:feature:delete"

    JOB_CREATE = "license-manager:job:create"
    JOB_READ = "license-manager:job:read"
    JOB_UPDATE = "license-manager:job:update"
    JOB_DELETE = "license-manager:job:delete"

    BOOKING_CREATE = "license-manager:booking:create"
    BOOKING_READ = "license-manager:booking:read"
    BOOKING_UPDATE = "license-manager:booking:update"
    BOOKING_DELETE = "license-manager:booking:delete"
