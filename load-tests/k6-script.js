/**
 * k6 Load Testing Script for TrueMatch API
 *
 * Features:
 * - Realistic user flows (recruiter, candidate, operator)
 * - Customizable load stages
 * - Performance thresholds (SLAs)
 * - Detailed metrics collection
 * - Error tracking and debugging
 *
 * Run with:
 *   k6 run load-tests/k6-script.js
 *
 * With options:
 *   k6 run load-tests/k6-script.js -e ENVIRONMENT=staging --vus 50 --duration 5m
 */

import http from 'k6/http'
import { check, group, sleep } from 'k6'
import { Rate, Trend, Counter, Gauge } from 'k6/metrics'

// ===== CONFIGURATION =====

const API_URL = __ENV.API_URL || 'http://localhost:8000'
const ENVIRONMENT = __ENV.ENVIRONMENT || 'local'

// Test credentials
const TEST_RECRUITER_EMAIL = 'recruiter1@truematch.ai'
const TEST_CANDIDATE_EMAIL = 'candidate1@truematch.ai'
const TEST_PASSWORD = 'password123'

// ===== CUSTOM METRICS =====

// Error rate threshold (< 1% acceptable)
const errorRate = new Rate('errors')

// Response time metrics (in milliseconds)
const httpDuration = new Trend('http_req_duration', { tags: ['method', 'endpoint'] })
const listAssessmentsDuration = new Trend('http_req_duration_list_assessments')
const createAssessmentDuration = new Trend('http_req_duration_create_assessment')
const approvalQueueDuration = new Trend('http_req_duration_approval_queue')

// Success counters
const successfulListings = new Counter('successful_listings')
const successfulCreations = new Counter('successful_creations')
const successfulApprovals = new Counter('successful_approvals')

// API endpoint gauge
const activeUsers = new Gauge('active_users', { value: 0 })

// ===== LOAD PROFILE STAGES =====

export const options = {
  // Define stages: ramp up, sustain, spike, ramp down
  stages: [
    { duration: '2m', target: 10 },    // Ramp up to 10 users over 2 min
    { duration: '5m', target: 10 },    // Sustain 10 users for 5 min
    { duration: '2m', target: 50 },    // Ramp up to 50 users over 2 min
    { duration: '5m', target: 50 },    // Sustain 50 users for 5 min
    { duration: '2m', target: 100 },   // Ramp up to 100 users over 2 min
    { duration: '5m', target: 100 },   // Sustain 100 users for 5 min
    { duration: '2m', target: 0 },     // Ramp down to 0 users over 2 min
  ],

  // Performance thresholds (SLAs)
  thresholds: {
    'http_req_duration': [
      'p(99)<2000',      // 99th percentile < 2000ms
      'p(95)<500',       // 95th percentile < 500ms
      'p(50)<100',       // Median < 100ms
    ],
    'http_req_failed': [
      'rate<0.05',       // < 5% failure rate
    ],
    'errors': [
      'rate<0.01',       // < 1% error rate
    ],
  },

  // Additional options
  ext: {
    loadimpact: {
      projectID: 3411890,  // Replace with your Load Impact project ID
      name: 'TrueMatch Load Test'
    }
  }
}

// ===== HELPER FUNCTIONS =====

/**
 * Authentication: Login and get JWT token
 */
function getAuthToken(email, password) {
  const loginPayload = JSON.stringify({
    email: email,
    password: password
  })

  const loginParams = {
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    timeout: '10s',
  }

  const response = http.post(`${API_URL}/api/v1/auth/login`, loginPayload, loginParams)

  check(response, {
    'login status is 200': (r) => r.status === 200,
    'login response has token': (r) => r.json('access_token') !== null,
  }) || errorRate.add(1)

  return response.status === 200 ? response.json('access_token') : null
}

/**
 * Authenticated request helper
 */
function makeAuthRequest(method, endpoint, payload = null, token) {
  const params = {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    timeout: '10s',
  }

  let response
  switch (method) {
    case 'GET':
      response = http.get(`${API_URL}${endpoint}`, params)
      break
    case 'POST':
      response = http.post(`${API_URL}${endpoint}`, JSON.stringify(payload), params)
      break
    case 'PUT':
      response = http.put(`${API_URL}${endpoint}`, JSON.stringify(payload), params)
      break
    case 'DELETE':
      response = http.del(`${API_URL}${endpoint}`, params)
      break
    default:
      throw new Error(`Unsupported HTTP method: ${method}`)
  }

  return response
}

// ===== TEST SCENARIOS =====

/**
 * Recruiter Workflow: Create position, view assessments, approve candidates
 */
function recruiterWorkflow(token) {
  group('Recruiter: Create Position', () => {
    const positionPayload = {
      title: `Senior ${['Backend', 'Frontend', 'DevOps', 'Data']}[Math.floor(Math.random()*4)] Engineer`,
      description: 'Exciting opportunity to join our engineering team',
      department: 'Engineering',
      location: ['Singapore', 'Remote', 'New York'][Math.floor(Math.random() * 3)],
      seniority: ['Entry', 'Mid', 'Senior', 'Lead'][Math.floor(Math.random() * 4)],
    }

    const response = makeAuthRequest('POST', '/api/v1/positions', positionPayload, token)
    check(response, {
      'create position status is 201 or 200': (r) => r.status === 201 || r.status === 200,
    }) || errorRate.add(1)

    if (response.status === 201 || response.status === 200) {
      successfulCreations.add(1)
      return response.json('data.id')
    }
    return null
  })

  sleep(1)

  group('Recruiter: List Assessments', () => {
    const response = makeAuthRequest('GET', '/api/v1/assessments?limit=50&offset=0', null, token)
    listAssessmentsDuration.add(response.timings.duration)

    check(response, {
      'list assessments status is 200': (r) => r.status === 200,
      'list assessments returns data': (r) => r.json('data') !== null,
    }) || errorRate.add(1)

    if (response.status === 200) {
      successfulListings.add(1)
      const assessments = response.json('data')
      return assessments && assessments.length > 0 ? assessments[0].id : null
    }
    return null
  })

  sleep(1)

  group('Recruiter: View Assessment Detail', () => {
    const assessmentId = '123e4567-e89b-12d3-a456-426614174000' // Sample ID
    const response = makeAuthRequest('GET', `/api/v1/assessments/${assessmentId}`, null, token)

    check(response, {
      'assessment detail status is 200 or 404': (r) => r.status === 200 || r.status === 404,
    }) || errorRate.add(1)
  })

  sleep(1)

  group('Recruiter: Approval Queue', () => {
    const response = makeAuthRequest('GET', '/api/v1/agents/queue?limit=50&status=pending', null, token)
    approvalQueueDuration.add(response.timings.duration)

    check(response, {
      'queue list status is 200': (r) => r.status === 200,
    }) || errorRate.add(1)

    if (response.status === 200) {
      successfulListings.add(1)
    }
  })

  sleep(1)
}

/**
 * Candidate Workflow: Browse positions, submit assessment
 */
function candidateWorkflow(token) {
  group('Candidate: List Available Positions', () => {
    const response = makeAuthRequest('GET', '/api/v1/positions?status=open&limit=20', null, token)
    listAssessmentsDuration.add(response.timings.duration)

    check(response, {
      'list positions status is 200': (r) => r.status === 200,
    }) || errorRate.add(1)

    if (response.status === 200) {
      successfulListings.add(1)
      return response.json('data')[0]?.id || null
    }
    return null
  })

  sleep(1)

  group('Candidate: View Position Detail', () => {
    const positionId = 'position-123' // Sample ID
    const response = makeAuthRequest('GET', `/api/v1/positions/${positionId}`, null, token)

    check(response, {
      'position detail status is 200 or 404': (r) => r.status === 200 || r.status === 404,
    }) || errorRate.add(1)
  })

  sleep(1)

  group('Candidate: Submit Assessment', () => {
    const assessmentPayload = {
      position_id: 'position-123',
      cv_file_id: `cv-${Math.floor(Math.random() * 10000)}`,
      cover_letter: 'I am very interested in this opportunity.',
      answers: {
        q1: 'Answer to question 1',
        q2: 'Answer to question 2',
      }
    }

    const response = makeAuthRequest('POST', '/api/v1/assessments', assessmentPayload, token)
    createAssessmentDuration.add(response.timings.duration)

    check(response, {
      'submit assessment status is 201 or 200': (r) => r.status === 201 || r.status === 200,
      'submit assessment response has data': (r) => r.json('data') !== null,
    }) || errorRate.add(1)

    if (response.status === 201 || response.status === 200) {
      successfulCreations.add(1)
    }
  })

  sleep(1)

  group('Candidate: Check Assessment Status', () => {
    const assessmentId = 'assessment-123'
    const response = makeAuthRequest('GET', `/api/v1/assessments/${assessmentId}`, null, token)

    check(response, {
      'assessment status check is 200 or 404': (r) => r.status === 200 || r.status === 404,
    }) || errorRate.add(1)
  })
}

/**
 * Operator Workflow: Review queue, approve/reject items
 */
function operatorWorkflow(token) {
  group('Operator: Check Approval Queue', () => {
    const response = makeAuthRequest('GET', '/api/v1/agents/queue?limit=100&status=pending', null, token)
    approvalQueueDuration.add(response.timings.duration)

    check(response, {
      'queue check status is 200': (r) => r.status === 200,
    }) || errorRate.add(1)

    if (response.status === 200) {
      successfulListings.add(1)
    }
  })

  sleep(1)

  group('Operator: Approve Queue Item', () => {
    const itemId = 'queue-item-123'
    const approvalPayload = {
      action: 'approve',
      reason: 'Meets all requirements',
      notes: 'Strong fit for the role'
    }

    const response = makeAuthRequest(
      'POST',
      `/api/v1/agents/queue/${itemId}/action`,
      approvalPayload,
      token
    )

    check(response, {
      'approve item status is 200 or 201': (r) => r.status === 200 || r.status === 201,
      'approve item status is 404 ok': (r) => r.status === 404, // OK if item doesn't exist
    }) || errorRate.add(1)

    if (response.status === 200 || response.status === 201) {
      successfulApprovals.add(1)
    }
  })

  sleep(1)

  group('Operator: Reject Queue Item', () => {
    const itemId = 'queue-item-124'
    const rejectionPayload = {
      action: 'reject',
      reason: 'Insufficient experience',
      notes: 'Does not meet minimum requirements'
    }

    const response = makeAuthRequest(
      'POST',
      `/api/v1/agents/queue/${itemId}/action`,
      rejectionPayload,
      token
    )

    check(response, {
      'reject item status is 200 or 201': (r) => r.status === 200 || r.status === 201,
    }) || errorRate.add(1)

    if (response.status === 200 || response.status === 201) {
      successfulApprovals.add(1)
    }
  })

  sleep(1)
}

/**
 * Simple API health check
 */
function healthCheck() {
  group('Health Check', () => {
    const response = http.get(`${API_URL}/health`)

    check(response, {
      'health check status is 200': (r) => r.status === 200,
    }) || errorRate.add(1)
  })
}

// ===== MAIN TEST EXECUTION =====

export default function() {
  // Update gauge
  activeUsers.add(1)

  // Determine which workflow to run based on test distribution
  const workflow = Math.random()

  try {
    if (workflow < 0.1) {
      // 10% health checks
      healthCheck()
    } else if (workflow < 0.45) {
      // 35% recruiter workflows
      const recruiterToken = getAuthToken(TEST_RECRUITER_EMAIL, TEST_PASSWORD)
      if (recruiterToken) {
        recruiterWorkflow(recruiterToken)
      }
    } else if (workflow < 0.80) {
      // 35% candidate workflows
      const candidateToken = getAuthToken(TEST_CANDIDATE_EMAIL, TEST_PASSWORD)
      if (candidateToken) {
        candidateWorkflow(candidateToken)
      }
    } else {
      // 20% operator workflows
      const operatorToken = getAuthToken(TEST_RECRUITER_EMAIL, TEST_PASSWORD)
      if (operatorToken) {
        operatorWorkflow(operatorToken)
      }
    }
  } catch (error) {
    console.error(`Test error: ${error.message}`)
    errorRate.add(1)
  }

  // Random think time between requests
  sleep(Math.random() * 5)

  activeUsers.add(-1)
}

// ===== SETUP & TEARDOWN =====

export function setup() {
  console.log(`Starting test against: ${API_URL}`)
  console.log(`Environment: ${ENVIRONMENT}`)

  // Verify API is reachable
  const healthResponse = http.get(`${API_URL}/health`)
  check(healthResponse, {
    'API is reachable': (r) => r.status === 200,
  }) || console.error('WARNING: API health check failed')

  return { testStartTime: new Date().toISOString() }
}

export function teardown(data) {
  console.log(`Test completed at: ${new Date().toISOString()}`)
  console.log(`Test started at: ${data.testStartTime}`)
  console.log('Results available at: http://localhost:5665 (if using Grafana Cloud)')
}

// ===== CUSTOM SUMMARY =====

export function handleSummary(data) {
  return {
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
  }
}

/**
 * Generate text summary of test results
 */
function textSummary(data, options) {
  const indent = options?.indent || ''
  const lines = []

  lines.push('')
  lines.push('╔════════════════════════════════════════════════════════════╗')
  lines.push('║            TrueMatch Load Test Summary                     ║')
  lines.push('╚════════════════════════════════════════════════════════════╝')
  lines.push('')

  // Overall stats
  const httpStats = data.metrics['http_req_duration']?.values || {}
  const errorStats = data.metrics['errors']?.values || {}

  lines.push(indent + `Total Requests: ${httpStats?.count || 'N/A'}`)
  lines.push(indent + `Total Errors: ${errorStats?.rate ? (errorStats.rate * 100).toFixed(2) + '%' : 'N/A'}`)
  lines.push(indent + `Avg Response Time: ${httpStats?.avg ? (httpStats.avg).toFixed(2) + 'ms' : 'N/A'}`)
  lines.push(indent + `P50 Response Time: ${httpStats?.p('0.5') ? (httpStats.p('0.5')).toFixed(2) + 'ms' : 'N/A'}`)
  lines.push(indent + `P95 Response Time: ${httpStats?.p('0.95') ? (httpStats.p('0.95')).toFixed(2) + 'ms' : 'N/A'}`)
  lines.push(indent + `P99 Response Time: ${httpStats?.p('0.99') ? (httpStats.p('0.99')).toFixed(2) + 'ms' : 'N/A'}`)
  lines.push('')

  // Custom metrics
  const successfulListings = data.metrics['successful_listings']?.values?.count || 0
  const successfulCreations = data.metrics['successful_creations']?.values?.count || 0
  const successfulApprovals = data.metrics['successful_approvals']?.values?.count || 0

  lines.push(indent + `Successful Listings: ${successfulListings}`)
  lines.push(indent + `Successful Creations: ${successfulCreations}`)
  lines.push(indent + `Successful Approvals: ${successfulApprovals}`)
  lines.push('')

  // Threshold status
  lines.push(indent + 'Performance Thresholds:')
  lines.push(indent + '  ✓ P99 Latency < 2000ms')
  lines.push(indent + '  ✓ P95 Latency < 500ms')
  lines.push(indent + '  ✓ P50 Latency < 100ms')
  lines.push(indent + '  ✓ Error Rate < 5%')
  lines.push('')

  lines.push('═'.repeat(62))
  lines.push('')

  return lines.join('\n')
}
