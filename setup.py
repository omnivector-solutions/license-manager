import sys

import setuptools


sys.path.append(".")

from license_manager import VERSION  # NOQA


setuptools.setup(
    name="license-manager",
    version=VERSION,
    packages=setuptools.find_packages(include=["license_manager", "license_manager.*"]),
    license="GPLv3",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    install_requires=["pyyaml", "sentry-sdk"],
    extras_require={
        "dev": ["black", "flake8", "isort", "pytest", "pytest-cov", "tox", "wheel"]
    },
    entry_points={
        "console_scripts": [
            "license-server=license_manager.server.main:main",
            "license-agent=license_manager.agent.main:main",
        ],
    },
    include_package_data=True,
    python_requires=">=3.6.8",
)
