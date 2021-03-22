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
        "databases[postgresql]",
        "fastapi",
        "fastapi-utils",
        "mangum",
        "aws-psycopg2",  # soft-required by sqlalchemy
        "sqlalchemy>=1.3.23,<1.4",
        # "sqlalchemy>=1.4",  # waiting for https://github.com/encode/databases/issues/298
    ],
    extras_require={
        "agent": [
            "httpx",
        ],
        "admin": [
            # for lm-create-jwt
            "boto3",
            "click",
            "pyjwt",
        ],
        "dev": [
            "black",
            "databases[sqlite]",
            "flake8",
            "isort",
            "mypy",
            "pytest",
            "pytest-asyncio",
            "pytest-cov",
            "pytest-env",
            "pytest-freezegun",
            "respx",
            "sqlalchemy-stubs",
            "tox",
            "uvicorn",
            "wheel",
        ],
    },
    entry_points={
        "console_scripts": [
            "lm-create-jwt=licensemanager2.backend.createjwt:main",
        ],
    },
    include_package_data=True,
    python_requires=">=3.6.8",
)
