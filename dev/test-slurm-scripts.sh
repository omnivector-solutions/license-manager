#!/bin/bash
#
# Test script for Slurm prolog/epilog scripts
#
# This script simulates Slurm environment variables and tests the prolog
# and epilog scripts against the prolog/epilog API running in Docker.
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}=== Slurm Prolog/Epilog Script Test ===${NC}"

# Check if API is reachable
API_URL="${LM_PROLOG_EPILOG_API_URL:-http://localhost:8081}"
echo "Testing API at: $API_URL"

if ! curl -s "${API_URL}/health" > /dev/null 2>&1; then
    echo -e "${RED}ERROR: Prolog/Epilog API is not reachable at ${API_URL}${NC}"
    echo "Make sure the lm-agent container is running with ENABLE_PROLOG_EPILOG_API=true"
    echo ""
    echo "To start the container:"
    echo "  docker run -d --name lm-agent-test \\"
    echo "    -p 8081:8081 \\"
    echo "    -e ENABLE_PROLOG_EPILOG_API=true \\"
    echo "    -e LM_AGENT_USE_RECONCILE_IN_PROLOG_EPILOG=false \\"
    echo "    -e LM_AGENT_OIDC_DOMAIN=test.auth0.com \\"
    echo "    -e LM_AGENT_OIDC_CLIENT_ID=test-client-id \\"
    echo "    -e LM_AGENT_OIDC_CLIENT_SECRET=test-client-secret \\"
    echo "    -e LM_AGENT_BACKEND_BASE_URL=http://localhost:8000 \\"
    echo "    lm-agent:test"
    exit 1
fi

echo -e "${GREEN}✓ API is reachable${NC}"

# Make scripts executable
chmod +x "$SCRIPT_DIR/slurm-prolog.sh"
chmod +x "$SCRIPT_DIR/slurm-epilog.sh"

# Set up simulated Slurm environment
export SLURM_CLUSTER_NAME="test-cluster"
export SLURM_JOB_ID="12345"
export SLURM_JOB_NODELIST="node001"
export SLURM_JOB_USER="testuser"
export SLURM_JOB_LICENSES="matlab:1,ansys:2"
export LM_PROLOG_EPILOG_API_URL="$API_URL"

echo ""
echo "Simulated Slurm environment:"
echo "  SLURM_CLUSTER_NAME=$SLURM_CLUSTER_NAME"
echo "  SLURM_JOB_ID=$SLURM_JOB_ID"
echo "  SLURM_JOB_NODELIST=$SLURM_JOB_NODELIST"
echo "  SLURM_JOB_USER=$SLURM_JOB_USER"
echo "  SLURM_JOB_LICENSES=$SLURM_JOB_LICENSES"

# Test 1: Run prolog script
echo ""
echo -e "${YELLOW}Test 1: Running prolog script...${NC}"
if "$SCRIPT_DIR/slurm-prolog.sh"; then
    echo -e "${GREEN}✓ Prolog script succeeded${NC}"
else
    echo -e "${RED}✗ Prolog script failed${NC}"
    exit 1
fi

# Test 2: Run epilog script
echo ""
echo -e "${YELLOW}Test 2: Running epilog script...${NC}"
if "$SCRIPT_DIR/slurm-epilog.sh"; then
    echo -e "${GREEN}✓ Epilog script succeeded${NC}"
else
    echo -e "${RED}✗ Epilog script failed${NC}"
    exit 1
fi

# Test 3: Test with bracket notation nodelist
echo ""
echo -e "${YELLOW}Test 3: Testing with bracket notation nodelist...${NC}"
export SLURM_JOB_ID="12346"
export SLURM_JOB_NODELIST="compute[001-004]"
if "$SCRIPT_DIR/slurm-prolog.sh"; then
    echo -e "${GREEN}✓ Prolog with bracket notation succeeded${NC}"
else
    echo -e "${RED}✗ Prolog with bracket notation failed${NC}"
    exit 1
fi

# Test 4: Test with no licenses
echo ""
echo -e "${YELLOW}Test 4: Testing with no licenses...${NC}"
export SLURM_JOB_ID="12347"
export SLURM_JOB_NODELIST="gpu001"
unset SLURM_JOB_LICENSES
if "$SCRIPT_DIR/slurm-prolog.sh"; then
    echo -e "${GREEN}✓ Prolog with no licenses succeeded${NC}"
else
    echo -e "${RED}✗ Prolog with no licenses failed${NC}"
    exit 1
fi

# Test 5: Test missing required variable
echo ""
echo -e "${YELLOW}Test 5: Testing with missing SLURM_JOB_ID (should fail)...${NC}"
unset SLURM_JOB_ID
if "$SCRIPT_DIR/slurm-prolog.sh" 2>/dev/null; then
    echo -e "${RED}✗ Prolog should have failed with missing variable${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Prolog correctly failed with missing variable${NC}"
fi

echo ""
echo -e "${GREEN}=== All tests passed! ===${NC}"
echo ""
echo "To use these scripts in Slurm, configure slurm.conf:"
echo "  PrologSlurmctld=/path/to/slurm-prolog.sh"
echo "  EpilogSlurmctld=/path/to/slurm-epilog.sh"
echo ""
echo "And set the API URL environment variable:"
echo "  export LM_PROLOG_EPILOG_API_URL=http://<api-host>:8081"
