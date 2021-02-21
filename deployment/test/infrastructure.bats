#!/bin/npx bats


load "node_modules/bats-support/load.bash"
load "node_modules/bats-assert/load.bash"

load ".env"


TF="terraform -chdir=../infrastructure/live/$FUNCTION_STAGE/license-manager"
CURL="curl -o- -L -i --no-progress-meter"


@test "is terraform installed" {
    command terraform version
}


@test "is a postgres client installed" {
    command pg_isready --version
}


@test "does the terraform config validate" {
    run $TF validate
}


@test "is the database up" {
    pgurl=$($TF output -raw database-url)
    run pg_isready -d $pgurl
    assert_success
    assert_line --partial ":5432 - accepting connections"
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


@test "can we reach the API through the public url" {
    url=$($TF output -raw internet-url)
    run $CURL $url
    assert_success
    assert_line --partial '{"status":"ok"}'
}
