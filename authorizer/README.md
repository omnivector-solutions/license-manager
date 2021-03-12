# JWT-APIGW-Authorizer

## About The Project
`jwt-apigw-authorizer` is a small module appropriate to be used as a "custom authorizer" (aka "lambda authorizer") in AWS API Gateway. Package and deploy this software as a lambda function and set up an API Gateway to use the lambda as your token authorizer.


## Prerequisites

This software makes the following assumptions about your deployment environment:

- You are using AWS to deploy software, and specifically you are using API Gateway. (You may use any Integration Type you want with your API methods.)
- You want to use JWT tokens to authenticate into your API.

In addition, you will need to build a number of AWS resources to use this software. Terraform modules exist to build these with some configuration you supply, assuming you want to run Terraform.


## Installation (backend)

```
git clone git@github.com:omnivector-solutions/jwt-apigw-authorizer
python3 -m venv venv
. venv/bin/activate
pip install wheel .[dev]
```


## Deployment

1. Start by building the lambda zipfile:

    ```#!bash
    make -B function.zip
    ```

2. Use the github
[omnivector-solutions/infrastructure][infrastructure] repository to deploy
this software. Follow the instructions in the infrastructure README.md to
install `terraform`.

    Live deployments should be configured in `live/license-manager/xxxx` (stage,
    prod, edge, or other).

    Before running terraform:

    ```#!bash
    # create scratch.auto.tfvars
    echo > scratch.auto.tfvars << EOF
    zipfile = "/some/path/to/function.zip"
    zipfile_authorizer = "/some/path/to/function.zip"
    EOF

    ```


3. Run terraform commands:

    ```#!bash
    cd live/project-name/xxxx  # plug in some stage or custom directory here

    # install the modules this terraform configuration will import (like pip install)
    terraform init

    # show what resources will be changed, like a dry run
    terraform plan -out my.out

    # actually create/modify resources
    terraform apply my.out
    ```

    Terraform will output the live internet URL where you can access the HTTP API of the backend.


4. Run infrastructure tests.

    ```#!bash
    npm i
    npx bats deployment/test
    ```


## Run locally

```
# TODO
```



## License
Distributed under the MIT License. See `LICENSE` for more information.


## Contact
Omnivector Solutions - [www.omnivector.solutions][website] - <info@omnivector.solutions>

Project Link: [https://github.com/omnivector-solutions/jwt-apigw-authorizer](https://github.com/omnivector-solutions/jwt-apigw-authorizer)
