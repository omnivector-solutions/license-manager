import setuptools


VERSION = "1.0.0+dev"


setuptools.setup(
    name="jwt-apigw-authorizer",
    version=VERSION,
    py_modules=["authorizer"],
    author="Omnivector Solutions",
    author_email="info@omnivector.solutions",
    url="https://github.com/omnivector-solutions/jwt-apigw-authorizer",
    license="MIT",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    install_requires=[
        "boto3",
        "pyjwt",
    ],
    extras_require={"dev": ["python-lambda-local"]},
    python_requires=">=3.7",
)
