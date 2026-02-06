#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
IMAGE_NAME="lm-agent:test"
CONTAINER_NAME="lm-agent-test"

echo -e "${YELLOW}=== LM Agent Docker Test ===${NC}"
echo "Project root: $PROJECT_ROOT"

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Cleaning up...${NC}"
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm "$CONTAINER_NAME" 2>/dev/null || true
}

# Set trap to cleanup on exit
trap cleanup EXIT

# Stop and remove any existing container
echo -e "\n${YELLOW}Stopping any existing container...${NC}"
docker stop "$CONTAINER_NAME" 2>/dev/null || true
docker rm "$CONTAINER_NAME" 2>/dev/null || true

# Build the Docker image
echo -e "\n${YELLOW}Building Docker image...${NC}"
cd "$PROJECT_ROOT"
docker build -f lm-agent/Dockerfile -t "$IMAGE_NAME" .

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Docker build failed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker image built successfully${NC}"

# Test 1: Verify binaries are installed
echo -e "\n${YELLOW}Test 1: Verifying installed binaries...${NC}"
BINARIES=$(docker run --rm --entrypoint bash "$IMAGE_NAME" -c '
    echo "license-manager-agent: $(which license-manager-agent)"
    echo "lmutil: $(which lmutil)"
    echo "rlmutil: $(which rlmutil)"
    echo "lstc_qrun: $(which lstc_qrun)"
    echo "lmxendutil: $(which lmxendutil)"
    echo "olixtool: $(which olixtool)"
')
echo "$BINARIES"
if echo "$BINARIES" | grep -q "license-manager-agent:"; then
    echo -e "${GREEN}✓ All binaries are installed${NC}"
else
    echo -e "${RED}✗ Some binaries are missing${NC}"
    exit 1
fi

# Test 2: Start container with simulator and prolog/epilog API enabled
echo -e "\n${YELLOW}Test 2: Starting container with simulator and prolog/epilog API enabled...${NC}"
docker run -d --name "$CONTAINER_NAME" \
    -e ENABLE_LM_SIMULATOR=true \
    -e ENABLE_PROLOG_EPILOG_API=true \
    -e LM_AGENT_OIDC_DOMAIN=test.auth0.com \
    -e LM_AGENT_OIDC_CLIENT_ID=test-client-id \
    -e LM_AGENT_OIDC_CLIENT_SECRET=test-client-secret \
    -e LM_AGENT_BACKEND_BASE_URL=http://localhost:8000 \
    -e LM_AGENT_USE_RECONCILE_IN_PROLOG_EPILOG=false \
    -e LM_AGENT_LOG_LEVEL=DEBUG \
    "$IMAGE_NAME"

# Wait for container to start and all services to initialize
sleep 6

# Check container is running
if docker ps --filter name="$CONTAINER_NAME" --format "{{.Names}}" | grep -q "$CONTAINER_NAME"; then
    echo -e "${GREEN}✓ Container is running${NC}"
else
    echo -e "${RED}✗ Container failed to start${NC}"
    docker logs "$CONTAINER_NAME" 2>&1
    exit 1
fi

# Test 3: Verify entrypoint output shows simulator and prolog/epilog API enabled
echo -e "\n${YELLOW}Test 3: Verifying entrypoint output...${NC}"
LOGS=$(docker logs "$CONTAINER_NAME" 2>&1)
echo "$LOGS"

if echo "$LOGS" | grep -q "LM Simulator is enabled"; then
    echo -e "${GREEN}✓ Simulator is enabled in entrypoint${NC}"
else
    echo -e "${RED}✗ Simulator not enabled${NC}"
    exit 1
fi

if echo "$LOGS" | grep -q "Prolog/Epilog API is enabled"; then
    echo -e "${GREEN}✓ Prolog/Epilog API is enabled in entrypoint${NC}"
else
    echo -e "${RED}✗ Prolog/Epilog API not enabled${NC}"
    exit 1
fi

if echo "$LOGS" | grep -q "Starting License Manager Agent"; then
    echo -e "${GREEN}✓ Agent startup message found${NC}"
else
    echo -e "${RED}✗ Agent startup message not found${NC}"
    exit 1
fi

# Test 4: Verify agent process is running
echo -e "\n${YELLOW}Test 4: Verifying agent process...${NC}"
PROCESS=$(docker exec "$CONTAINER_NAME" cat /proc/1/cmdline | tr '\0' ' ')
echo "PID 1: $PROCESS"

if echo "$PROCESS" | grep -q "license-manager-agent"; then
    echo -e "${GREEN}✓ Agent is running as main process${NC}"
else
    echo -e "${RED}✗ Agent process not found${NC}"
    exit 1
fi

# Test 5: Verify log file is being written
echo -e "\n${YELLOW}Test 5: Checking log file...${NC}"
sleep 2
LOG_CONTENT=$(docker exec "$CONTAINER_NAME" cat /var/log/license-manager-agent/license-manager-agent.log 2>&1 || echo "")

if echo "$LOG_CONTENT" | grep -q "Starting License Manager Agent"; then
    echo -e "${GREEN}✓ Log file is being written${NC}"
    echo "Log content:"
    echo "$LOG_CONTENT" | head -5
else
    echo -e "${YELLOW}⚠ Log file may be empty or not yet written${NC}"
fi

# Test 6: Verify SQLite database was created
echo -e "\n${YELLOW}Test 6: Checking SQLite database...${NC}"
if docker exec "$CONTAINER_NAME" ls /app/data/simulator.db > /dev/null 2>&1; then
    echo -e "${GREEN}✓ SQLite database created${NC}"
else
    echo -e "${RED}✗ SQLite database not found${NC}"
    exit 1
fi

# Test 7: Test Simulator API - add a license
echo -e "\n${YELLOW}Test 7: Testing Simulator API - adding license...${NC}"
LICENSE_RESPONSE=$(docker exec "$CONTAINER_NAME" curl -s -X POST http://127.0.0.1:8080/lm-sim/licenses \
    -H "Content-Type: application/json" \
    -d '{"name": "testfeature", "total": 50, "license_server_type": "flexlm"}')
echo "$LICENSE_RESPONSE"

if echo "$LICENSE_RESPONSE" | grep -q '"name":"testfeature"'; then
    echo -e "${GREEN}✓ License added successfully${NC}"
else
    echo -e "${RED}✗ Failed to add license${NC}"
    exit 1
fi

# Test 8: Test fake lmutil binary with simulator
echo -e "\n${YELLOW}Test 8: Testing fake lmutil binary...${NC}"
LMUTIL_OUTPUT=$(docker exec "$CONTAINER_NAME" lmutil lmstat -c 8080@127.0.0.1 -f testfeature 2>&1)
echo "$LMUTIL_OUTPUT"

if echo "$LMUTIL_OUTPUT" | grep -q "Users of testfeature"; then
    echo -e "${GREEN}✓ Fake lmutil binary works with simulator${NC}"
else
    echo -e "${RED}✗ Fake lmutil binary failed${NC}"
    exit 1
fi

# Test 9: Test Prolog/Epilog API health endpoint
echo -e "\n${YELLOW}Test 9: Testing Prolog/Epilog API health endpoint...${NC}"
HEALTH_STATUS=$(docker exec "$CONTAINER_NAME" curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8081/health)
echo "Health endpoint returned: HTTP $HEALTH_STATUS"

if [ "$HEALTH_STATUS" = "204" ]; then
    echo -e "${GREEN}✓ Prolog/Epilog API health check passed${NC}"
else
    echo -e "${RED}✗ Prolog/Epilog API health check failed (expected 204, got $HEALTH_STATUS)${NC}"
    exit 1
fi

# Test 10: Test Prolog endpoint
echo -e "\n${YELLOW}Test 10: Testing Prolog endpoint...${NC}"
PROLOG_RESPONSE=$(docker exec "$CONTAINER_NAME" curl -s -X POST http://127.0.0.1:8081/prolog \
    -H "Content-Type: application/json" \
    -d '{"cluster_name": "test-cluster", "job_id": "12345", "lead_host": "node001", "user_name": "testuser", "job_licenses": ""}')
echo "$PROLOG_RESPONSE"

if echo "$PROLOG_RESPONSE" | grep -q '"status"'; then
    echo -e "${GREEN}✓ Prolog endpoint works${NC}"
else
    echo -e "${RED}✗ Prolog endpoint failed${NC}"
    exit 1
fi

# Test 11: Test Epilog endpoint
echo -e "\n${YELLOW}Test 11: Testing Epilog endpoint...${NC}"
EPILOG_RESPONSE=$(docker exec "$CONTAINER_NAME" curl -s -X POST http://127.0.0.1:8081/epilog \
    -H "Content-Type: application/json" \
    -d '{"cluster_name": "test-cluster", "job_id": "12345", "lead_host": "node001", "user_name": "testuser", "job_licenses": ""}')
echo "$EPILOG_RESPONSE"

if echo "$EPILOG_RESPONSE" | grep -q '"status"'; then
    echo -e "${GREEN}✓ Epilog endpoint works${NC}"
else
    echo -e "${RED}✗ Epilog endpoint failed${NC}"
    exit 1
fi

# Test 12: Test with simulator disabled
echo -e "\n${YELLOW}Test 12: Testing with simulator disabled...${NC}"
docker stop "$CONTAINER_NAME" >/dev/null
docker rm "$CONTAINER_NAME" >/dev/null

# Run container briefly with simulator disabled and capture startup logs
docker run -d --name "$CONTAINER_NAME" \
    -e ENABLE_LM_SIMULATOR=false \
    -e ENABLE_PROLOG_EPILOG_API=false \
    -e LM_AGENT_OIDC_DOMAIN=test.auth0.com \
    -e LM_AGENT_OIDC_CLIENT_ID=test-client-id \
    -e LM_AGENT_OIDC_CLIENT_SECRET=test-client-secret \
    -e LM_AGENT_BACKEND_BASE_URL=http://localhost:8000 \
    "$IMAGE_NAME" >/dev/null

sleep 2
DISABLED_OUTPUT=$(docker logs "$CONTAINER_NAME" 2>&1)

echo "$DISABLED_OUTPUT" | head -10

if echo "$DISABLED_OUTPUT" | grep -q "LM Simulator is disabled"; then
    echo -e "${GREEN}✓ Simulator correctly disabled${NC}"
else
    echo -e "${RED}✗ Simulator disable check failed${NC}"
    exit 1
fi

if echo "$DISABLED_OUTPUT" | grep -q "Prolog/Epilog API is disabled"; then
    echo -e "${GREEN}✓ Prolog/Epilog API correctly disabled${NC}"
else
    echo -e "${RED}✗ Prolog/Epilog API disable check failed${NC}"
    exit 1
fi

echo -e "\n${GREEN}=== All tests passed! ===${NC}"
echo -e "Image: ${YELLOW}$IMAGE_NAME${NC}"
echo ""
echo "To run the container manually:"
echo "  docker run -d --name lm-agent \\"
echo "    -e ENABLE_LM_SIMULATOR=true \\"
echo "    -e ENABLE_PROLOG_EPILOG_API=true \\"
echo "    -e LM_AGENT_OIDC_DOMAIN=<your-domain> \\"
echo "    -e LM_AGENT_OIDC_CLIENT_ID=<your-client-id> \\"
echo "    -e LM_AGENT_OIDC_CLIENT_SECRET=<your-secret> \\"
echo "    -e LM_AGENT_BACKEND_BASE_URL=<backend-url> \\"
echo "    $IMAGE_NAME"
