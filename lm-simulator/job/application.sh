#!/usr/bin/env bash
set -e

# You must modify this value to reflect the IP address and port that the
# license-manager-simulator is listening on in your environment.
#
# The format of the value is: `http://<ip-address>:<port>`
URL="http://localhost:8000"

# Number of licenses: from the CLI or default to 42
if [ -z "$1" ]; then
    X=42
else
    X=$1
fi

payload="{\"quantity\": "$X", \
          \"user_name\": \""$USER"\", \
          \"lead_host\": \"$(hostname)\", \
          \"license_name\": \"test_feature\"}"

echo "Requesting $X licenses for user $USER"
response=$(curl -s -w 'HTTPSTATUS:%{http_code}' \
              -X 'POST' \
              -H 'Content-Type: application/json' \
              -d "$payload" \
              "$URL"/lm-sim/licenses-in-use)

response_status=$(echo "$response" | sed -e 's/.*HTTPSTATUS://')
response_body=$(echo "$response" | sed -e 's/HTTPSTATUS:.*//')

if [ "$response_status" = "201" ]; then
    echo "There are enough licenses available, let's run (sleep) the job"
    sleep $((RANDOM % 100 + 100))
else
    echo "There are not enough licenses, let's crash the job"
    tail /NOT_ENOUGH_LICENSES
fi

license_in_use_id=$(echo "$response_body" | grep -o '"id":[0-9]*' | awk -F: '{print $2}')

echo "Putting the licenses back"
curl -s -o /dev/null \
     -X DELETE \
     "$URL/lm-sim/licenses-in-use/$license_in_use_id"

echo "Job done"
