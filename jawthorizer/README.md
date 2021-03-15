# Jawthorizer

## About The Project
`jawthorizer` is a small module appropriate to be used as a "custom authorizer" (aka "lambda authorizer") in AWS API Gateway. Package and deploy this software as a lambda function and set up an API Gateway to use the lambda as your token authorizer.


## Prerequisites

This software makes the following assumptions about your deployment environment:

- You are using AWS to deploy software, and specifically you are using API Gateway. (You may use any Integration Type you want with your API methods.)
- You want to use JWT tokens to authenticate into your API.

In addition, you will need to build a number of AWS resources to use this software. Terraform modules exist to build these with some configuration you supply, assuming you want to run Terraform.


## Installation (for running locally to debug)

```
git clone git@github.com:omnivector-solutions/jawthorizer
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

[infrastructure]: https://github.com/omnivector-solutions/infrastructure

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

The authorizer is not intended to be deployed outside of AWS in production, and serves no useful purpose that way, but it can be debugged this way.

When running locally, you still need to create an AWS Secrets Manager secret, in your region of choice, for example:
`/my-app/edge/token-secret`. The secret name should follow this pattern, but the last part of the string **must** be `token-secret`.

Install the dev dependencies:
```
pip install .[dev]
```

Now you can run the lambda locally with `python-lambda-local`.

You will need to:

- configure AWS credentials to be able to access AWS Secrets Manager
- create the `/my-app/edge/token-secret` secret as described above. The string value of the secret can be any random sequence of characters.

- create two json files:
    - env.json, with contents:
        ```
        {
            "JAWTHORIZER_APP_SHORT_NAME": "my-app",
            "JAWTHORIZER_STAGE": "edge",
            "JAWTHORIZER_REGION": "us-west-2",
            "JAWTHORIZER_ALLOWED_SUBS": "*"
        }
        ```

    - event.json, with contents:
        ```
        {
            "methodArn": "arn:aws:execute-api:us-west-2:000000000000:q999999999/edge/GET/api/v1/doot/doot",
            "authorizationToken": "Bearer xxxxxxxxxxxxxxxxxx.yyyyyyyyyyyyyyyyyyyyy.zzzzzzzzzzzzzzzzzzzzzz"
        }
        ```

      `methodArn` should be a method ARN for an API Gateway method, but the
      method doesn't have to actually exist just to test the authorizer. It
      should follow this string pattern, though.

      `authorizationToken` should be a legitimate token generated from the
      `token-secret` you created earlier (unless you are testing for errors,
      in which case put any garbage you want).

      For the token payload:
      - you must specify both `sub` and `iss` in the payload
      - you may specify any `sub` that you want (it must glob-match JAWTHORIZER_ALLOWED_SUBS)
      - specify `iss` as: `my-app::edge::us-west-2`
      - you may specify payload `exp` for an expiring token, and it will be checked if it is set

- run: `python-lambda-local -e env.json jawthorizer/src/jawthorizer/__init__.py event.json`

  This simulates the way API Gateway would invoke your Lambda with a Bearer Authorization token from an inbound request.


## License
Distributed under the MIT License. See `LICENSE` for more information.


## Contact
Omnivector Solutions - [www.omnivector.solutions][website] - <info@omnivector.solutions>

Project Link: [https://github.com/omnivector-solutions/jawthorizer](https://github.com/omnivector-solutions/jawthorizer)
