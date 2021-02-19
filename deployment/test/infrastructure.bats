#!/bin/npx bats


load "node_modules/bats-support/load.bash"
load "node_modules/bats-assert/load.bash"

load ".env"


TF="terraform -chdir=../infrastructure/live/$FUNCTION_STAGE/license-manager"
CURL="curl -o- -L -i"


@test "is terraform installed" {
    command terraform version
}


@test "does the terraform config validate" {
    run $TF validate
}


@test "is the lambda running" {
    fn=$($TF output -raw lambda-function-name)
    run aws lambda invoke --function-name $fn --payload file://doc/example-lambda.json /dev/stdout
    assert_success
    assert_line --partial '\"status\":\"ok\"'
}


@test "is api gateway able to access the function" {
    url=$($TF output -raw apigw-url)
    run $CURL $url
    assert_success
    assert_line --partial '{"status":"ok"}'
}
