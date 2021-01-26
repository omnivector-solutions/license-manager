import setuptools


VERSION = "2.0.0+dev"


setuptools.setup(
    name="license-manager",
    version=VERSION,
    packages=setuptools.find_packages(
        where="./src", include=("licensemanager2", "licensemanager2.*")
    ),
    package_dir={"": "src"},
    license="GPLv3",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    install_requires=[
        "boto3",
        "databases[postgresql]",
        "fastapi",
        "mangum",
        "sqlalchemy",
    ],
    extras_require={
        "dev": [
            "black",
            "databases[sqlite]",
            "flake8",
            "isort",
            "mypy",
            "pytest",
            "pytest-cov",
            "sqlalchemy-stubs",
            "tox",
            "uvicorn",
            "wheel",
        ]
    },
    entry_points={
        "console_scripts": [
            # "license-agent=license_manager.agent.main:main",
        ],
    },
    include_package_data=True,
    python_requires=">=3.6.8",
)
