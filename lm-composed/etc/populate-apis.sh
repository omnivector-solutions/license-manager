#!/bin/bash
set -e


echo "---> Populating LM-API with pre-defined license ..."

OIDC_RESPONSE=$(curl -s --request POST \
    --url $LM2_AGENT_OIDC_DOMAIN/protocol/openid-connect/token \
    --header "Content-Type: application/x-www-form-urlencoded" \
    --data audience=$LM2_AGENT_OIDC_AUDIENCE \
    --data client_id=$LM2_AGENT_OIDC_CLIENT_ID \
    --data client_secret=$LM2_AGENT_OIDC_CLIENT_SECRET \
    --data grant_type=client_credentials
)
TOKEN=$(echo $OIDC_RESPONSE | jq -r .access_token)

if [ -z "$TOKEN" ]; then
  echo "Error: Unable to retrieve access token"
  exit 1
fi

EXISTING_PRODUCTS_RESPONSE=$(curl -s --request GET \
    --url $LM2_AGENT_BACKEND_BASE_URL/lm/products \
    --header "Authorization: Bearer $TOKEN"
)

if [ -z $EXISTING_PRODUCTS_RESPONSE ]; then
    echo "Error: Unable to read products"
    exit 1
fi

if [ "$(echo $EXISTING_PRODUCTS_RESPONSE | jq '. | length')" -gt 0 ]; then
    echo "The product has already been created before"
    PRODUCT_ID=$(echo "$EXISTING_PRODUCTS_RESPONSE" | jq '.[0].id')
else
    PRODUCT_RESPONSE=$(curl -s --request POST \
        --url $LM2_AGENT_BACKEND_BASE_URL/lm/products \
        --header "Authorization: Bearer $TOKEN" \
        --header "Content-Type: application/json" \
        --data "{\"name\": \"abaqus\"}"
    )

    if [ -z $PRODUCT_RESPONSE ]; then
        echo "Error: Unable to create product"
        exit 1
    fi

    PRODUCT_ID=$(echo $PRODUCT_RESPONSE | jq -r .id)
    echo "Product response: $PRODUCT_RESPONSE"
fi


if [ -z $PRODUCT_ID ]; then
  echo "Error: Unable to retrieve product ID"
  exit 1
fi

EXISTING_CONFIGS_RESPONSE=$(curl -s --request GET \
    --url $LM2_AGENT_BACKEND_BASE_URL/lm/configurations \
    --header "Authorization: Bearer $TOKEN"
)

if [ -z $EXISTING_CONFIGS_RESPONSE ]; then
    echo "Error: Unable to read configurations"
    exit 1
fi

if [ "$(echo $EXISTING_CONFIGS_RESPONSE | jq '. | length')" -gt 0 ]; then
    echo "The configuration has already been created before"
else
    LM_ABAQUS_RESPONSE=$(curl -s --request POST \
        --url $LM2_AGENT_BACKEND_BASE_URL/lm/configurations \
        --header "Authorization: Bearer $TOKEN" \
        --header "Content-Type: application/json" \
        --data "{
                    \"name\": \"Abaqus\",
                    \"cluster_client_id\": \"agent\",
                    \"features\": [
                        {
                            \"name\": \"abaqus\",
                            \"product_id\": $PRODUCT_ID,
                            \"reserved\": 0
                        }
                    ],
                    \"license_servers\": [
                        {
                            \"host\": \"localhost\",
                            \"port\": 1234
                        }
                    ],
                    \"grace_time\": 300,
                    \"type\": \"flexlm\"
                }"
    )
    echo "API Abaqus response: $LM_ABAQUS_RESPONSE"
fi

echo "-- Populated LM API ..."

echo " ---> Populating LM-SIM API with pre-defined license ..."

LM_SIM="http://lm-simulator:8000"

SIM_ABAQUS_RESPONSE=$(curl -s --request POST \
    --url $LM_SIM/lm-sim/licenses/ \
    --header "Content-Type: application/json" \
    --data "{\"name\": \"abaqus\", \"total\": 1000}"
)
echo "LM-SIM Abaqus response: $SIM_ABAQUS_RESPONSE"

echo "-- Populated LM-SIM API ..."
