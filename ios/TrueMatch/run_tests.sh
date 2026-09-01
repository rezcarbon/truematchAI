#!/bin/bash
#
# TrueMatch iOS Test Runner Script
# Comprehensive test execution for unit, integration, and E2E tests
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCHEME="TrueMatch"
CONFIGURATION="Debug"
DERIVED_DATA_PATH="build"
COVERAGE_REPORT_PATH="coverage_report"

# Print colored output
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Display help
show_help() {
    cat << EOF
TrueMatch iOS Test Runner

Usage: ./run_tests.sh [command] [options]

Commands:
    all             Run all tests (unit + integration + E2E)
    unit            Run unit tests only
    integration     Run integration tests only
    e2e             Run E2E tests only
    simulator       Run tests on iOS simulator
    device          Run tests on physical device
    coverage        Run tests with code coverage report
    performance     Run performance tests
    ci              Run tests in CI environment
    help            Show this help message

Options:
    --scheme        Xcode scheme (default: TrueMatch)
    --config        Build configuration (default: Debug)
    --simulator     Device name (e.g., "iPhone 15")
    --timeout       Test timeout in seconds (default: 300)
    --verbose       Enable verbose output
    --debug         Enable debug logging

Examples:
    ./run_tests.sh all
    ./run_tests.sh unit --verbose
    ./run_tests.sh simulator --simulator "iPhone 15"
    ./run_tests.sh coverage --config Release
    ./run_tests.sh performance

EOF
}

# Run unit tests
run_unit_tests() {
    print_header "Running Unit Tests"

    xcodebuild test \
        -scheme "$SCHEME" \
        -configuration "$CONFIGURATION" \
        -derivedDataPath "$DERIVED_DATA_PATH" \
        -only-testing TrueMatchTests \
        ${VERBOSE_FLAG} \
        ${TIMEOUT_FLAG} || {
        print_error "Unit tests failed"
        return 1
    }

    print_success "Unit tests completed"
}

# Run integration tests
run_integration_tests() {
    print_header "Running Integration Tests"

    xcodebuild test \
        -scheme "$SCHEME" \
        -configuration "$CONFIGURATION" \
        -derivedDataPath "$DERIVED_DATA_PATH" \
        -only-testing TrueMatchIntegrationTests \
        ${VERBOSE_FLAG} \
        ${TIMEOUT_FLAG} || {
        print_error "Integration tests failed"
        return 1
    }

    print_success "Integration tests completed"
}

# Run E2E tests
run_e2e_tests() {
    print_header "Running E2E Tests"

    xcodebuild test \
        -scheme "$SCHEME" \
        -configuration "$CONFIGURATION" \
        -derivedDataPath "$DERIVED_DATA_PATH" \
        -only-testing TrueMatchUITests \
        ${VERBOSE_FLAG} \
        ${TIMEOUT_FLAG} || {
        print_error "E2E tests failed"
        return 1
    }

    print_success "E2E tests completed"
}

# Run tests on simulator
run_on_simulator() {
    local simulator_name="${1:-iPhone 15}"

    print_header "Running Tests on Simulator: $simulator_name"

    xcodebuild test \
        -scheme "$SCHEME" \
        -configuration "$CONFIGURATION" \
        -destination "platform=iOS Simulator,name=$simulator_name,OS=latest" \
        -derivedDataPath "$DERIVED_DATA_PATH" \
        ${VERBOSE_FLAG} \
        ${TIMEOUT_FLAG} || {
        print_error "Simulator tests failed"
        return 1
    }

    print_success "Simulator tests completed"
}

# Run tests on device
run_on_device() {
    print_header "Running Tests on Device"

    xcodebuild test \
        -scheme "$SCHEME" \
        -configuration "$CONFIGURATION" \
        -destination "generic/platform=iOS" \
        -derivedDataPath "$DERIVED_DATA_PATH" \
        ${VERBOSE_FLAG} \
        ${TIMEOUT_FLAG} || {
        print_error "Device tests failed"
        return 1
    }

    print_success "Device tests completed"
}

# Run tests with coverage
run_with_coverage() {
    print_header "Running Tests with Code Coverage"

    xcodebuild test \
        -scheme "$SCHEME" \
        -configuration "$CONFIGURATION" \
        -derivedDataPath "$DERIVED_DATA_PATH" \
        -enableCodeCoverage YES \
        ${VERBOSE_FLAG} \
        ${TIMEOUT_FLAG} || {
        print_error "Coverage tests failed"
        return 1
    }

    print_success "Tests completed with coverage enabled"

    # Generate coverage report
    generate_coverage_report
}

# Generate coverage report
generate_coverage_report() {
    print_header "Generating Coverage Report"

    mkdir -p "$COVERAGE_REPORT_PATH"

    # Extract and process coverage data
    xcrun xccov view --report --json "$DERIVED_DATA_PATH" > "$COVERAGE_REPORT_PATH/coverage.json" 2>/dev/null || true

    print_success "Coverage report generated at $COVERAGE_REPORT_PATH/"
}

# Run performance tests
run_performance_tests() {
    print_header "Running Performance Tests"

    xcodebuild test \
        -scheme "$SCHEME" \
        -configuration "$CONFIGURATION" \
        -derivedDataPath "$DERIVED_DATA_PATH" \
        -only-testing TrueMatchTests/PerformanceTests \
        ${VERBOSE_FLAG} || {
        print_warning "Performance tests failed"
    }

    print_success "Performance tests completed"
}

# Run CI tests
run_ci_tests() {
    print_header "Running Tests in CI Environment"

    # Set CI environment variables
    export CI=true
    export CI_BUILD_ID="${CI_BUILD_ID:-local_$(date +%s)}"

    print_header "Unit Tests"
    run_unit_tests || return 1

    print_header "Integration Tests"
    run_integration_tests || return 1

    print_header "E2E Tests"
    run_e2e_tests || return 1

    print_header "Coverage Analysis"
    run_with_coverage || return 1

    print_success "All CI tests passed!"
}

# Clean build artifacts
cleanup() {
    print_header "Cleaning Up"
    rm -rf "$DERIVED_DATA_PATH"
    print_success "Cleanup completed"
}

# Main execution
main() {
    local command="${1:-all}"
    shift || true

    # Parse options
    VERBOSE_FLAG=""
    TIMEOUT_FLAG=""
    SIMULATOR_NAME="iPhone 15"

    while [[ $# -gt 0 ]]; do
        case $1 in
            --scheme)
                SCHEME="$2"
                shift 2
                ;;
            --config)
                CONFIGURATION="$2"
                shift 2
                ;;
            --simulator)
                SIMULATOR_NAME="$2"
                shift 2
                ;;
            --timeout)
                TIMEOUT_FLAG="-maximumTestExecutionTimeAllowance $2"
                shift 2
                ;;
            --verbose)
                VERBOSE_FLAG="-verbose"
                shift
                ;;
            --debug)
                set -x
                shift
                ;;
            *)
                echo "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # Execute command
    case $command in
        all)
            run_unit_tests && run_integration_tests && run_e2e_tests
            ;;
        unit)
            run_unit_tests
            ;;
        integration)
            run_integration_tests
            ;;
        e2e)
            run_e2e_tests
            ;;
        simulator)
            run_on_simulator "$SIMULATOR_NAME"
            ;;
        device)
            run_on_device
            ;;
        coverage)
            run_with_coverage
            ;;
        performance)
            run_performance_tests
            ;;
        ci)
            run_ci_tests
            ;;
        cleanup)
            cleanup
            ;;
        help)
            show_help
            ;;
        *)
            echo "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac

    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
        print_success "Tests completed successfully!"
    else
        print_error "Tests failed with exit code $exit_code"
    fi

    cleanup
    exit $exit_code
}

# Run main function
main "$@"
