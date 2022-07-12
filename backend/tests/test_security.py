from unittest.mock import patch

from lm_backend import security


def test_get_domain_configs__loads_only_base_settings():
    with patch.object(security.settings, "ARMASEC_DOMAIN", new="foo.io"):
        with patch.object(security.settings, "ARMASEC_AUDIENCE", new="https://bar.dev"):
            domain_configs = security.get_domain_configs()

    assert len(domain_configs) == 1
    first_config = domain_configs.pop()
    assert first_config.domain == "foo.io"
    assert first_config.audience == "https://bar.dev"


def test_get_domain_configs__loads_admin_settings_if_all_are_present():
    with patch.object(security.settings, "ARMASEC_DOMAIN", new="foo.io"):
        with patch.object(security.settings, "ARMASEC_AUDIENCE", new="https://bar.dev"):
            with patch.object(security.settings, "ARMASEC_ADMIN_DOMAIN", new="admin.io"):
                domain_configs = security.get_domain_configs()

    assert len(domain_configs) == 1
    first_config = domain_configs.pop()
    assert first_config.domain == "foo.io"
    assert first_config.audience == "https://bar.dev"

    with patch.object(security.settings, "ARMASEC_DOMAIN", new="foo.io"):
        with patch.object(security.settings, "ARMASEC_AUDIENCE", new="https://bar.dev"):
            with patch.object(security.settings, "ARMASEC_ADMIN_DOMAIN", new="admin.io"):
                with patch.object(security.settings, "ARMASEC_ADMIN_AUDIENCE", new="https://admin.dev"):
                    with patch.object(security.settings, "ARMASEC_ADMIN_MATCH_KEY", new="foo"):
                        with patch.object(security.settings, "ARMASEC_ADMIN_MATCH_VALUE", new="bar"):
                            domain_configs = security.get_domain_configs()

    assert len(domain_configs) == 2
    (first_config, second_config) = domain_configs
    assert first_config.domain == "foo.io"
    assert first_config.audience == "https://bar.dev"
    assert second_config.domain == "admin.io"
    assert second_config.audience == "https://admin.dev"
    assert second_config.match_keys == dict(foo="bar")
