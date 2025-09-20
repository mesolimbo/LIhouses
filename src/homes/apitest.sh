#!/usr/bin/env bash

set -e

RENTCAST_API_KEY=${RENTCAST_API_KEY:?'Environment variable RENTCAST_API_KEY must be set'}
ZIP_CODE='11743'

curl -k --request GET \
  --url "https://api.rentcast.io/v1/listings/sale?zipCode=${ZIP_CODE}&status=Active&limit=10" \
  --header 'Accept: application/json' \
  --header "X-Api-Key: ${RENTCAST_API_KEY}" | tee "${ZIP_CODE}.json"
