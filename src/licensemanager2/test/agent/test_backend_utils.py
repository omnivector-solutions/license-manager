"""
Tests of backend_utils
"""
import os
from typing import List, Any
from unittest.mock import patch

from licensemanager2.agent import backend_utils
from licensemanager2.agent import settings


def license_server_features() -> List[Any]:
    """
    The license server type and features.
    """
    return [{"features": ["TESTFEATURE"], "license_server_type": "flexlm"}]


def get_license_server_feature_config_file(filename):
    """
    Return the license_server_feature_config_file path as a string.
    """
    path = os.path.abspath(__file__)
    dir_path = os.path.dirname(path)
    return os.path.join(dir_path, f"test_configs/{filename}")


def test_get_license_server_features():
    """
    Do I produce the correct license server/features config?
    """
    config_file_name = "license_server_config.yaml"
    license_server_features_config_path = get_license_server_feature_config_file(config_file_name)
    # Patch the objects needed to generate a report.
    p1 = patch.object(settings.SETTINGS, "LICENSE_SERVER_FEATURES_CONFIG_PATH", license_server_features_config_path)
    with p1:
        assert license_server_features() == backend_utils.get_license_server_features()


def test_bad_license_server_features_config():
    """
    Do I produce the correct config when a non-valid config file is passed?
    """
    config_file_name = "license_server_config_bad.yaml"
    license_server_features_config_path = get_license_server_feature_config_file(config_file_name)
    # Patch the objects needed to generate a report.
    p1 = patch.object(settings.SETTINGS, "LICENSE_SERVER_FEATURES_CONFIG_PATH", license_server_features_config_path)
    with p1:
        assert [] == backend_utils.get_license_server_features()
