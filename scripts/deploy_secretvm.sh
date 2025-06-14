#!/bin/bash

# SecretVM Deployment Script for attest_ai
# This script handles the complete deployment workflow to SecretVM

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VM_NAME="${VM_NAME:-attest-ai-mvp}"
VM_TYPE="${VM_TYPE:-medium}"
ENV_FILE="${ENV_FILE:-$PROJECT_ROOT/.env.production}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking deployment prerequisites..."
    
    # Check if secretvm-cli is installed
    if ! command -v secretvm-cli &> /dev/null; then
        log_error "secretvm-cli is not installed. Please install it first."
        echo "Installation: https://docs.scrt.network/secret-network-documentation/development/tools-and-libraries/secret-vm-cli"
        exit 1
    fi
    
    # Check authentication
    if ! secretvm-cli auth status &> /dev/null; then
        log_error "Not authenticated with SecretVM. Please run: secretvm-cli auth login -w <wallet_address>"
        exit 1
    fi
    
    # Check if production environment file exists
    if [ ! -f "$ENV_FILE" ]; then
        log_error "Production environment file not found: $ENV_FILE"
        log_info "Please create the production environment file with real credentials."
        exit 1
    fi
    
    # Check if docker-compose.yaml exists
    if [ ! -f "$PROJECT_ROOT/docker-compose.yaml" ]; then
        log_error "docker-compose.yaml not found in project root"
        exit 1
    fi
    
    log_success "All prerequisites met"
}

# Validate environment file
validate_environment() {
    log_info "Validating production environment configuration..."
    
    # Check required environment variables
    required_vars=("SECRET_AI_API_KEY" "ARWEAVE_WALLET_JWK")
    
    source "$ENV_FILE"
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            log_error "Required environment variable $var is not set in $ENV_FILE"
            exit 1
        fi
    done
    
    # Validate API key format
    if [[ ! "$SECRET_AI_API_KEY" =~ ^[A-Za-z0-9+/=]+$ ]]; then
        log_error "SECRET_AI_API_KEY appears to be invalid (should be base64 encoded)"
        exit 1
    fi
    
    # Validate Arweave wallet JWK format
    if ! echo "$ARWEAVE_WALLET_JWK" | jq empty 2>/dev/null; then
        log_error "ARWEAVE_WALLET_JWK is not valid JSON"
        exit 1
    fi
    
    log_success "Environment configuration validated"
}

# Create VM and deploy
deploy_to_secretvm() {
    log_info "Starting deployment to SecretVM..."
    
    # Step 1: Create VM
    log_info "Creating SecretVM instance: $VM_NAME"
    
    VM_CREATE_OUTPUT=$(secretvm-cli vm create \
        -n "$VM_NAME" \
        -t "$VM_TYPE" \
        -d "$PROJECT_ROOT/docker-compose.yaml" \
        --wait-for-ready \
        2>&1)
    
    if [ $? -ne 0 ]; then
        log_error "Failed to create VM"
        echo "$VM_CREATE_OUTPUT"
        exit 1
    fi
    
    # Extract VM ID from output
    VM_ID=$(echo "$VM_CREATE_OUTPUT" | grep -o 'VM ID: [a-zA-Z0-9-]*' | cut -d' ' -f3)
    
    if [ -z "$VM_ID" ]; then
        log_error "Could not extract VM ID from creation output"
        echo "$VM_CREATE_OUTPUT"
        exit 1
    fi
    
    log_success "VM created successfully: $VM_ID"
    
    # Step 2: Upload environment file (encrypted)
    log_info "Uploading encrypted environment configuration..."
    
    if ! secretvm-cli vm upload-env "$VM_ID" "$ENV_FILE"; then
        log_error "Failed to upload environment file"
        exit 1
    fi
    
    log_success "Environment file uploaded and encrypted"
    
    # Step 3: Wait for deployment to complete
    log_info "Waiting for deployment to complete..."
    
    # Wait up to 10 minutes for deployment
    timeout=600
    elapsed=0
    interval=30
    
    while [ $elapsed -lt $timeout ]; do
        status=$(secretvm-cli vm status "$VM_ID" --format json | jq -r '.status')
        
        case "$status" in
            "running")
                log_success "VM deployment completed successfully"
                break
                ;;
            "failed"|"error")
                log_error "VM deployment failed"
                secretvm-cli vm logs "$VM_ID" --tail 50
                exit 1
                ;;
            *)
                log_info "Deployment status: $status (waiting...)"
                sleep $interval
                elapsed=$((elapsed + interval))
                ;;
        esac
    done
    
    if [ $elapsed -ge $timeout ]; then
        log_error "Deployment timed out after $timeout seconds"
        exit 1
    fi
    
    # Get VM URL
    VM_URL=$(secretvm-cli vm status "$VM_ID" --format json | jq -r '.url')
    
    if [ "$VM_URL" = "null" ] || [ -z "$VM_URL" ]; then
        log_error "Could not retrieve VM URL"
        exit 1
    fi
    
    log_success "VM accessible at: $VM_URL"
    echo "$VM_ID" > "$PROJECT_ROOT/.vm_id"
    echo "$VM_URL" > "$PROJECT_ROOT/.vm_url"
}

# Validate deployment
validate_deployment() {
    log_info "Validating deployment..."
    
    VM_URL=$(cat "$PROJECT_ROOT/.vm_url" 2>/dev/null)
    
    if [ -z "$VM_URL" ]; then
        log_error "VM URL not found. Deployment may have failed."
        exit 1
    fi
    
    # Test health endpoint
    log_info "Testing health endpoint..."
    
    for attempt in {1..10}; do
        if curl -f -s "${VM_URL}:8000/health" > /dev/null; then
            log_success "Health endpoint responding"
            break
        else
            if [ $attempt -eq 10 ]; then
                log_error "Health endpoint not responding after 10 attempts"
                exit 1
            fi
            log_info "Attempt $attempt/10: Health endpoint not ready, waiting..."
            sleep 30
        fi
    done
    
    # Test self-attestation endpoint
    log_info "Testing self-attestation endpoint..."
    
    HEALTH_RESPONSE=$(curl -s "${VM_URL}:8000/health")
    SELF_ATTESTATION_STATUS=$(echo "$HEALTH_RESPONSE" | jq -r '.services.self_attestation.available // false')
    
    if [ "$SELF_ATTESTATION_STATUS" = "true" ]; then
        log_success "Self-attestation service is available"
    else
        log_warning "Self-attestation service not available (may be expected)"
    fi
    
    # Test API endpoints
    log_info "Testing API endpoints..."
    
    endpoints=(
        "/api"
        "/api/attestation/status"
        "/api/secretai/health"
        "/api/arweave/status"
        "/api/proofs/validation-schema"
    )
    
    for endpoint in "${endpoints[@]}"; do
        if curl -f -s "${VM_URL}:8000${endpoint}" > /dev/null; then
            log_success "Endpoint $endpoint responding"
        else
            log_warning "Endpoint $endpoint not responding"
        fi
    done
    
    log_success "Deployment validation completed"
}

# Run post-deployment tests
run_post_deployment_tests() {
    log_info "Running post-deployment tests..."
    
    VM_URL=$(cat "$PROJECT_ROOT/.vm_url" 2>/dev/null)
    
    if [ -z "$VM_URL" ]; then
        log_error "VM URL not found"
        exit 1
    fi
    
    # Run the post-deployment test script
    if [ -f "$SCRIPT_DIR/test_secretvm_deployment.py" ]; then
        export SECRETVM_URL="$VM_URL"
        python3 "$SCRIPT_DIR/test_secretvm_deployment.py"
    else
        log_warning "Post-deployment test script not found"
    fi
}

# Display deployment summary
show_deployment_summary() {
    log_info "Deployment Summary"
    echo "=================="
    
    VM_ID=$(cat "$PROJECT_ROOT/.vm_id" 2>/dev/null)
    VM_URL=$(cat "$PROJECT_ROOT/.vm_url" 2>/dev/null)
    
    echo "VM ID: $VM_ID"
    echo "VM URL: $VM_URL"
    echo "Application URL: ${VM_URL}:8000"
    echo "Health Check: ${VM_URL}:8000/health"
    echo "API Documentation: ${VM_URL}:8000/api"
    echo ""
    echo "Management Commands:"
    echo "  Status: secretvm-cli vm status $VM_ID"
    echo "  Logs: secretvm-cli vm logs $VM_ID"
    echo "  Stop: secretvm-cli vm stop $VM_ID"
    echo "  Restart: secretvm-cli vm restart $VM_ID"
    echo "  Delete: secretvm-cli vm delete $VM_ID"
}

# Cleanup function
cleanup() {
    if [ -n "$VM_ID" ] && [ "$1" = "delete" ]; then
        log_info "Cleaning up VM: $VM_ID"
        secretvm-cli vm delete "$VM_ID" --force
        rm -f "$PROJECT_ROOT/.vm_id" "$PROJECT_ROOT/.vm_url"
    fi
}

# Main deployment function
main() {
    case "${1:-deploy}" in
        "deploy")
            check_prerequisites
            validate_environment
            deploy_to_secretvm
            validate_deployment
            run_post_deployment_tests
            show_deployment_summary
            log_success "🎉 Deployment completed successfully!"
            ;;
        "validate")
            validate_deployment
            ;;
        "test")
            run_post_deployment_tests
            ;;
        "status")
            show_deployment_summary
            ;;
        "cleanup")
            cleanup delete
            ;;
        "help")
            echo "Usage: $0 [command]"
            echo "Commands:"
            echo "  deploy   - Full deployment (default)"
            echo "  validate - Validate existing deployment"
            echo "  test     - Run post-deployment tests"
            echo "  status   - Show deployment status"
            echo "  cleanup  - Delete VM and cleanup"
            echo "  help     - Show this help"
            ;;
        *)
            log_error "Unknown command: $1"
            $0 help
            exit 1
            ;;
    esac
}

# Handle interrupts
trap 'log_error "Deployment interrupted"; exit 1' INT TERM

# Run main function
main "$@"