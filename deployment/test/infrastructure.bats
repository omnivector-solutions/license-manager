#!/bin/npx bats


load "node_modules/bats-support/load.bash"
load "node_modules/bats-assert/load.bash"

load ".env"


TF="terraform -chdir=../infrastructure/live/license-manager/$FUNCTION_STAGE"
CURL="curl -o- -f -L -i --no-progress-meter"


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
    auth_header='authorization: Bearer giant.base64-encoded.apikey'
    run $CURL $url --header "$auth_header"
    assert_success
    assert_line --partial '{"status":"ok","message":""}'
}


@test "does the API work, through the public url" {
    base_url=$($TF output -raw internet-url)
    auth_header='authorization: Bearer giant.base64-encoded.apikey'

    # root url
    run $CURL --header "$auth_header" \
        $base_url
    assert_success
    assert_line --partial '{"status":"ok","message":""}'

    # insert license data
    run $CURL --header "$auth_header" \
        --request PATCH \
        --header 'content-type: application/json' \
        --data '[{"product_feature": "abaqus.abaqus","booked": 0,"total": 119},{"product_feature": "abaqus.gpu","booked": 119,"total": 1909}]' \
        $base_url/api/v1/license/reconcile
    assert_success
    assert_line --partial '[{"product_feature":"abaqus.abaqus",'

    # query licenses
    run $CURL --header "$auth_header" \
        $base_url/api/v1/license/all
    assert_success
    assert_line --partial '[{"product_feature":"abaqus.abaqus",'

    # reset db
    run $CURL --header "$auth_header" \
        --request PUT \
        --header 'x-reset: please' \
        $base_url/api/v1/reset
    assert_success
    assert_line --partial '{"status":"ok","message":'
}
