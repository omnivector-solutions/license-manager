import setuptools


VERSION = "1.0.0+dev"


setuptools.setup(
    author="Omnivector Solutions",
    author_email="info@omnivector.solutions",
    extras_require={
        "dev": [
            "python-lambda-local",
            "pytest",
            "pytest-cov",
            "pytest-env",
        ]
    },
    install_requires=[
        "boto3",
        "pyjwt",
    ],
    license="MIT",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    name="jawthorizer",
    package_dir={"": "src"},
    packages=setuptools.find_packages(
        where="./src", include=("jawthorizer", "jawthorizer.*")
    ),
    python_requires=">=3.7",
    url="https://github.com/omnivector-solutions/jawthorizer",
    version=VERSION,
)
