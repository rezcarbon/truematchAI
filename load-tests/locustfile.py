"""
Locust load testing suite for TrueMatch API.

This suite simulates realistic user behavior patterns:
- AuthUser: Authenticated user browsing and action
- RecruitingUser: Recruiter-specific workflows
- CandidateUser: Candidate-specific workflows
- AdminUser: Admin operations
- APIStressUser: Direct API stress testing
- RealisticScenarioUser: Complex multi-step workflows

Run with: locust -f load-tests/locustfile.py --host=http://localhost:8000
"""

from locust import HttpUser, TaskSet, task, between, constant_pacing, events
from locust.contrib.fasthttp import FastHttpUser
import random
import time
import json
import logging
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ===== FIXTURES & DEFAULTS =====

# Test data for realistic scenarios
TEST_EMAILS = [f"recruiter{i}@truematch.ai" for i in range(1, 101)]
TEST_CANDIDATES = [f"candidate{i}@truematch.ai" for i in range(1, 1001)]
TEST_POSITIONS = [
    "Senior Software Engineer",
    "Product Manager",
    "Data Scientist",
    "DevOps Engineer",
    "UX Designer",
]

# Global metrics storage
METRICS = {
    "total_requests": 0,
    "total_errors": 0,
    "total_latency": 0,
    "min_latency": float('inf'),
    "max_latency": 0,
    "auth_failures": 0,
}


# ===== REQUEST LISTENERS FOR DETAILED METRICS =====

@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Track detailed request metrics for analysis."""
    METRICS["total_requests"] += 1
    METRICS["total_latency"] += response_time
    METRICS["min_latency"] = min(METRICS["min_latency"], response_time)
    METRICS["max_latency"] = max(METRICS["max_latency"], response_time)

    if exception:
        METRICS["total_errors"] += 1
        if "401" in str(exception) or "unauthorized" in str(exception).lower():
            METRICS["auth_failures"] += 1


@events.quitting.add_listener
def on_quit(environment, **kwargs):
    """Print summary statistics on test completion."""
    total_requests = METRICS["total_requests"]
    if total_requests == 0:
        return

    avg_latency = METRICS["total_latency"] / total_requests
    error_rate = (METRICS["total_errors"] / total_requests) * 100 if total_requests > 0 else 0

    print("\n" + "="*60)
    print("LOAD TEST SUMMARY STATISTICS")
    print("="*60)
    print(f"Total Requests: {total_requests:,}")
    print(f"Total Errors: {METRICS['total_errors']:,} ({error_rate:.2f}%)")
    print(f"Average Latency: {avg_latency:.2f}ms")
    print(f"Min Latency: {METRICS['min_latency']:.2f}ms")
    print(f"Max Latency: {METRICS['max_latency']:.2f}ms")
    print(f"Auth Failures: {METRICS['auth_failures']:,}")
    print("="*60 + "\n")


# ===== AUTHENTICATED USER BASE CLASS =====

class AuthenticatedUser(HttpUser):
    """Base class for authenticated users with common login/auth behavior."""

    wait_time = between(1, 3)

    def on_start(self):
        """Login and obtain auth token on session start."""
        self.token = None
        self.user_id = None
        self.assessment_ids = []
        self.position_ids = []
        self._login()

    def _login(self):
        """Authenticate and get JWT token."""
        email = random.choice(TEST_EMAILS)
        password = "password123"

        try:
            response = self.client.post(
                "/api/v1/auth/login",
                json={
                    "email": email,
                    "password": password
                },
                catch_response=True,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.user_id = data.get("user_id")
                self.headers = {"Authorization": f"Bearer {self.token}"}
                response.success()
                logger.info(f"✓ User authenticated: {email}")
            else:
                response.failure(f"Login failed: HTTP {response.status_code}")
                METRICS["auth_failures"] += 1
                logger.error(f"✗ Login failed for {email}: {response.status_code}")
        except Exception as e:
            logger.error(f"✗ Authentication error: {str(e)}")
            METRICS["auth_failures"] += 1

    def _get_headers(self) -> Dict:
        """Return headers with auth token."""
        return self.headers if self.token else {}


# ===== USER BEHAVIOR: RECRUITERS =====

class RecruiterTaskSet(TaskSet):
    """Recruiter-specific task workflows."""

    @task(3)
    def list_positions(self):
        """Most common: Browse positions."""
        with self.client.get(
            "/api/v1/positions?limit=50&offset=0",
            headers=self.user._get_headers(),
            catch_response=True,
            name="/api/v1/positions",
        ) as response:
            if response.status_code == 200:
                positions = response.json().get("data", [])
                if positions:
                    self.user.position_ids = [p["id"] for p in positions[:10]]
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(2)
    def view_position_detail(self):
        """View single position details."""
        if not self.user.position_ids:
            return

        position_id = random.choice(self.user.position_ids)
        with self.client.get(
            f"/api/v1/positions/{position_id}",
            headers=self.user._get_headers(),
            catch_response=True,
            name="/api/v1/positions/{position_id}",
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(2)
    def list_assessments(self):
        """Browse submitted assessments."""
        with self.client.get(
            "/api/v1/assessments?limit=50&offset=0",
            headers=self.user._get_headers(),
            catch_response=True,
            name="/api/v1/assessments",
        ) as response:
            if response.status_code == 200:
                assessments = response.json().get("data", [])
                if assessments:
                    self.user.assessment_ids = [a["id"] for a in assessments[:10]]
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(1)
    def view_assessment_detail(self):
        """View single assessment with full details."""
        if not self.user.assessment_ids:
            return

        assessment_id = random.choice(self.user.assessment_ids)
        with self.client.get(
            f"/api/v1/assessments/{assessment_id}",
            headers=self.user._get_headers(),
            catch_response=True,
            name="/api/v1/assessments/{assessment_id}",
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(1)
    def create_position(self):
        """Create new job position."""
        position_data = {
            "title": random.choice(TEST_POSITIONS),
            "description": "This is a test job posting for load testing",
            "company_id": f"company-{random.randint(1, 10)}",
            "department": random.choice(["Engineering", "Sales", "Product", "Operations"]),
            "location": random.choice(["Singapore", "Remote", "New York", "London"]),
            "seniority": random.choice(["Entry", "Mid", "Senior", "Lead"]),
        }

        with self.client.post(
            "/api/v1/positions",
            json=position_data,
            headers=self.user._get_headers(),
            catch_response=True,
            name="/api/v1/positions",
            timeout=15,
        ) as response:
            if response.status_code in [201, 200]:
                position = response.json().get("data", {})
                if position.get("id"):
                    self.user.position_ids.append(position["id"])
                response.success()
            elif response.status_code in [400, 422]:
                response.success()  # Expected validation errors
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(1)
    def list_queue(self):
        """Check approval queue status."""
        with self.client.get(
            "/api/v1/agents/queue?limit=50&status=pending",
            headers=self.user._get_headers(),
            catch_response=True,
            name="/api/v1/agents/queue",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")


class RecruiterUser(AuthenticatedUser):
    """Recruiter user with task set."""
    tasks = {RecruiterTaskSet: 1}


# ===== USER BEHAVIOR: CANDIDATES =====

class CandidateTaskSet(TaskSet):
    """Candidate-specific workflows."""

    @task(5)
    def list_available_positions(self):
        """Browse available positions."""
        with self.client.get(
            "/api/v1/positions?status=open&limit=20",
            headers=self.user._get_headers(),
            catch_response=True,
            name="/api/v1/positions",
        ) as response:
            if response.status_code == 200:
                positions = response.json().get("data", [])
                if positions:
                    self.user.position_ids = [p["id"] for p in positions[:5]]
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(3)
    def view_position(self):
        """View job posting details."""
        if not self.user.position_ids:
            return

        position_id = random.choice(self.user.position_ids)
        with self.client.get(
            f"/api/v1/positions/{position_id}",
            headers=self.user._get_headers(),
            catch_response=True,
            name="/api/v1/positions/{position_id}",
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(2)
    def submit_assessment(self):
        """Submit assessment for position."""
        if not self.user.position_ids:
            return

        position_id = random.choice(self.user.position_ids)
        assessment_data = {
            "position_id": position_id,
            "cv_file_id": f"cv-{random.randint(1, 10000)}",
            "cover_letter": "I'm very interested in this opportunity.",
            "answers": {
                "q1": "Answer 1",
                "q2": "Answer 2",
            }
        }

        with self.client.post(
            "/api/v1/assessments",
            json=assessment_data,
            headers=self.user._get_headers(),
            catch_response=True,
            name="/api/v1/assessments",
            timeout=20,
        ) as response:
            if response.status_code in [201, 200]:
                assessment = response.json().get("data", {})
                if assessment.get("id"):
                    self.user.assessment_ids.append(assessment["id"])
                response.success()
            elif response.status_code in [400, 422]:
                response.success()  # Validation errors expected
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(1)
    def check_assessment_status(self):
        """Check assessment status/results."""
        if not self.user.assessment_ids:
            return

        assessment_id = random.choice(self.user.assessment_ids)
        with self.client.get(
            f"/api/v1/assessments/{assessment_id}",
            headers=self.user._get_headers(),
            catch_response=True,
            name="/api/v1/assessments/{assessment_id}",
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")


class CandidateUser(AuthenticatedUser):
    """Candidate user with task set."""
    tasks = {CandidateTaskSet: 1}


# ===== USER BEHAVIOR: OPERATORS =====

class OperatorTaskSet(TaskSet):
    """Operator/Admin approval workflows."""

    @task(4)
    def check_queue(self):
        """Check pending items in queue."""
        with self.client.get(
            "/api/v1/agents/queue?limit=100&status=pending",
            headers=self.user._get_headers(),
            catch_response=True,
            name="/api/v1/agents/queue",
        ) as response:
            if response.status_code == 200:
                items = response.json().get("data", [])
                if items:
                    # Store for approval tasks
                    self.user.queue_item_ids = [item["id"] for item in items[:10]]
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(3)
    def approve_item(self):
        """Approve item from queue."""
        if not hasattr(self.user, 'queue_item_ids') or not self.user.queue_item_ids:
            return

        item_id = random.choice(self.user.queue_item_ids)
        action_data = {
            "action": "approve",
            "reason": "Meets all requirements",
            "notes": "Good fit for the role"
        }

        with self.client.post(
            f"/api/v1/agents/queue/{item_id}/action",
            json=action_data,
            headers=self.user._get_headers(),
            catch_response=True,
            name="/api/v1/agents/queue/{item_id}/action",
            timeout=10,
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            elif response.status_code in [400, 404]:
                response.success()  # Expected errors
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(2)
    def reject_item(self):
        """Reject item from queue with reason."""
        if not hasattr(self.user, 'queue_item_ids') or not self.user.queue_item_ids:
            return

        item_id = random.choice(self.user.queue_item_ids)
        action_data = {
            "action": "reject",
            "reason": "Insufficient experience",
            "notes": "Does not meet minimum requirements"
        }

        with self.client.post(
            f"/api/v1/agents/queue/{item_id}/action",
            json=action_data,
            headers=self.user._get_headers(),
            catch_response=True,
            name="/api/v1/agents/queue/{item_id}/action",
            timeout=10,
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            elif response.status_code in [400, 404]:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(1)
    def view_queue_analytics(self):
        """View queue analytics."""
        with self.client.get(
            "/api/v1/agents/queue/analytics",
            headers=self.user._get_headers(),
            catch_response=True,
            name="/api/v1/agents/queue/analytics",
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")


class OperatorUser(AuthenticatedUser):
    """Operator/Admin user with approval workflow."""
    tasks = {OperatorTaskSet: 1}


# ===== FAST/STRESS TESTING =====

class APIStressUser(FastHttpUser):
    """Direct API stress test without user wait times."""

    wait_time = constant_pacing(0.1)  # 100ms between requests (10 RPS per user)

    def on_start(self):
        """Quick login for stress test."""
        try:
            response = self.client.post(
                "/api/v1/auth/login",
                json={
                    "email": TEST_EMAILS[0],
                    "password": "password123"
                }
            )
            if response.status_code == 200:
                data = json.loads(response.content.decode())
                self.token = data.get("access_token")
        except Exception as e:
            logger.error(f"Stress test auth failed: {e}")
            self.token = None

    @task
    def simple_api_call(self):
        """Minimal API call for pure throughput testing."""
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        self.client.get(
            "/api/v1/health",
            headers=headers,
            name="/api/v1/health"
        )

    @task
    def assessment_list(self):
        """List assessments (common operation)."""
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        self.client.get(
            f"/api/v1/assessments?limit={random.randint(10, 100)}",
            headers=headers,
            name="/api/v1/assessments"
        )


# ===== REALISTIC MULTI-STEP WORKFLOWS =====

class RealisticScenarioUser(AuthenticatedUser):
    """Simulate realistic complex workflows combining multiple operations."""

    wait_time = between(2, 5)

    @task
    def recruiter_workflow(self):
        """Complete recruiter workflow: Create position, review assessments, approve."""
        # Step 1: Create position
        position_data = {
            "title": "Senior Backend Engineer",
            "description": "We're looking for an experienced backend engineer...",
            "department": "Engineering",
        }
        response = self.client.post(
            "/api/v1/positions",
            json=position_data,
            headers=self.user._get_headers(),
        )

        if response.status_code not in [200, 201]:
            return

        position_id = response.json().get("data", {}).get("id")
        time.sleep(1)

        # Step 2: List assessments for position
        response = self.client.get(
            f"/api/v1/assessments?position_id={position_id}",
            headers=self.user._get_headers(),
        )

        if response.status_code != 200:
            return

        assessments = response.json().get("data", [])
        time.sleep(1)

        # Step 3: Approve top assessment
        if assessments:
            assessment_id = assessments[0].get("id")
            approval_data = {
                "action": "approve",
                "notes": "Strong candidate"
            }
            self.client.post(
                f"/api/v1/assessments/{assessment_id}/approve",
                json=approval_data,
                headers=self.user._get_headers(),
            )

    @task
    def candidate_workflow(self):
        """Complete candidate workflow: Find position, submit assessment."""
        # Step 1: List positions
        response = self.client.get(
            "/api/v1/positions?status=open&limit=20",
            headers=self.user._get_headers(),
        )

        if response.status_code != 200:
            return

        positions = response.json().get("data", [])
        if not positions:
            return

        position_id = positions[0].get("id")
        time.sleep(1)

        # Step 2: View position details
        self.client.get(
            f"/api/v1/positions/{position_id}",
            headers=self.user._get_headers(),
        )
        time.sleep(1)

        # Step 3: Submit assessment
        assessment_data = {
            "position_id": position_id,
            "cv_file_id": f"cv-{random.randint(1, 10000)}",
        }
        self.client.post(
            "/api/v1/assessments",
            json=assessment_data,
            headers=self.user._get_headers(),
            timeout=20,
        )


# ===== LOCUST CONFIGURATION =====

class SmokeTest(HttpUser):
    """Quick smoke test: 1-5 users, basic endpoints."""
    wait_time = between(2, 5)
    tasks = {
        RecruiterTaskSet: 1,
        CandidateTaskSet: 1,
    }


class LoadTest(HttpUser):
    """Standard load test: 10-100 users, realistic behavior."""
    wait_time = between(1, 3)
    tasks = {
        RecruiterTaskSet: 3,
        CandidateTaskSet: 2,
        OperatorTaskSet: 1,
    }


class StressTest(HttpUser):
    """Stress test: 100-1000+ users, aggressive load."""
    wait_time = between(0.5, 2)
    tasks = {
        RecruiterTaskSet: 2,
        CandidateTaskSet: 2,
        APIStressUser: 2,
    }


class SpikeTest(HttpUser):
    """Spike test: Sudden load increase."""
    wait_time = between(0.1, 1)
    tasks = {
        RecruiterTaskSet: 2,
        CandidateTaskSet: 2,
        APIStressUser: 3,
    }


# ===== CUSTOM SHAPE (OPTIONAL) =====
# Uncomment to use custom load profile

# from locust import LoadTestShape
#
# class CustomLoadProfile(LoadTestShape):
#     """
#     Custom load profile: Ramp up, sustain, spike, ramp down.
#     """
#
#     def tick(self):
#         run_time = self.get_run_time()
#
#         if run_time < 60:
#             # Ramp up: 0-60 seconds
#             return (int(run_time / 2), 1)
#         elif run_time < 300:
#             # Sustain: 60-300 seconds
#             return (30, 1)
#         elif run_time < 360:
#             # Spike: 300-360 seconds
#             return (100, 1)
#         else:
#             # Ramp down
#             return None


if __name__ == "__main__":
    print("""
    TrueMatch Load Testing Suite

    Usage:
      locust -f load-tests/locustfile.py --host=http://localhost:8000

    Web UI: http://localhost:8089

    Test Profiles Available:
    - SmokeTest: 1-5 users
    - LoadTest: 10-100 users
    - StressTest: 100-1000+ users
    - SpikeTest: Sudden load increase
    - APIStressUser: Direct API stress
    - RealisticScenarioUser: Complex workflows
    """)
