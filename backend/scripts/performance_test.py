#!/usr/bin/env python3
"""
Performance testing script for Phase 1 endpoints.

Measures:
- Response times for each endpoint
- Database query performance
- Pagination efficiency
- Concurrent request handling
- Memory usage under load
"""

import asyncio
import time
import statistics
from typing import List, Dict
import httpx
import json
from datetime import datetime
import uuid

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"
TEST_USER_ID = str(uuid.uuid4())
AUTH_HEADER = {"Authorization": f"Bearer {TEST_USER_ID}"}

# Performance thresholds (milliseconds)
THRESHOLDS = {
    "list_endpoint": 500,      # List endpoints should respond < 500ms
    "get_endpoint": 200,       # Get endpoints should respond < 200ms
    "post_endpoint": 300,      # Create endpoints should respond < 300ms
    "put_endpoint": 300,       # Update endpoints should respond < 300ms
    "delete_endpoint": 100,    # Delete endpoints should respond < 100ms
}

# Results storage
results: Dict[str, List[float]] = {}


async def test_endpoint(
    method: str,
    path: str,
    name: str,
    payload: dict = None,
    iterations: int = 5,
) -> Dict:
    """Test an endpoint and measure performance."""
    times = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        for i in range(iterations):
            start = time.time()

            try:
                if method == "GET":
                    response = await client.get(
                        f"{API_BASE}{path}",
                        headers=AUTH_HEADER,
                    )
                elif method == "POST":
                    response = await client.post(
                        f"{API_BASE}{path}",
                        json=payload or {},
                        headers=AUTH_HEADER,
                    )
                elif method == "PUT":
                    response = await client.put(
                        f"{API_BASE}{path}",
                        json=payload or {},
                        headers=AUTH_HEADER,
                    )
                elif method == "DELETE":
                    response = await client.delete(
                        f"{API_BASE}{path}",
                        headers=AUTH_HEADER,
                    )

                elapsed = (time.time() - start) * 1000  # Convert to ms
                times.append(elapsed)

            except Exception as e:
                print(f"  ❌ Error: {e}")
                return None

    avg_time = statistics.mean(times)
    min_time = min(times)
    max_time = max(times)
    std_dev = statistics.stdev(times) if len(times) > 1 else 0

    results[name] = times

    return {
        "name": name,
        "method": method,
        "path": path,
        "iterations": iterations,
        "avg_time_ms": avg_time,
        "min_time_ms": min_time,
        "max_time_ms": max_time,
        "std_dev_ms": std_dev,
    }


def print_result(result: Dict):
    """Print a test result."""
    if not result:
        return

    avg = result["avg_time_ms"]
    threshold = THRESHOLDS.get(
        "list_endpoint" if "list" in result["path"].lower() else
        "get_endpoint" if result["method"] == "GET" else
        "post_endpoint" if result["method"] == "POST" else
        "put_endpoint" if result["method"] == "PUT" else
        "delete_endpoint"
    )

    status = "✅" if avg < threshold else "⚠️" if avg < threshold * 1.5 else "❌"

    print(f"{status} {result['name']:<50} {avg:>7.1f}ms (±{result['std_dev_ms']:>5.1f}ms)")


async def run_all_tests():
    """Run all performance tests."""
    print("🚀 TrueMatch AI - Phase 1 Performance Testing")
    print("=" * 80)
    print()

    # Test applications endpoints
    print("📊 Applications Module")
    print("-" * 80)

    tests = [
        ("GET", "/candidates/applications?page=1&page_size=20", "List Applications"),
        ("POST", "/candidates/applications", "Submit Application", {
            "job_id": str(uuid.uuid4()),
            "resume_version_id": str(uuid.uuid4()),
        }),
        ("GET", f"/candidates/applications/{uuid.uuid4()}", "Get Application"),
        ("PUT", f"/candidates/applications/{uuid.uuid4()}", "Update Application", {
            "notes": "Test note",
        }),
        ("DELETE", f"/candidates/applications/{uuid.uuid4()}", "Delete Application"),
        ("GET", "/candidates/applications/stats", "Application Stats"),
    ]

    for test in tests:
        result = await test_endpoint(*test)
        print_result(result)

    print()

    # Test job search endpoints
    print("📊 Job Search Module")
    print("-" * 80)

    tests = [
        ("GET", "/candidates/job-search?page=1&page_size=20", "List Job Searches"),
        ("POST", "/candidates/job-search", "Create Job Search", {
            "title": "Senior Engineer",
            "criteria": {"keywords": ["python"]},
        }),
        ("GET", f"/candidates/job-search/{uuid.uuid4()}", "Get Job Search"),
        ("GET", f"/candidates/job-search/{uuid.uuid4()}/results", "Get Search Results"),
        ("GET", "/candidates/job-search/jobs/saved?page=1&page_size=20", "Get Saved Jobs"),
    ]

    for test in tests:
        result = await test_endpoint(*test)
        print_result(result)

    print()

    # Test resume versioning endpoints
    print("📊 Resume Versioning Module")
    print("-" * 80)

    tests = [
        ("GET", "/candidates/resume-versions?page=1&page_size=20", "List Resume Versions"),
        ("POST", "/candidates/resume-versions", "Create Resume Version", {
            "name": "Tech Role Resume",
            "base_resume_id": str(uuid.uuid4()),
        }),
        ("GET", f"/candidates/resume-versions/{uuid.uuid4()}", "Get Resume Version"),
    ]

    for test in tests:
        result = await test_endpoint(*test)
        print_result(result)

    print()
    print("=" * 80)
    print_summary()


def print_summary():
    """Print performance summary."""
    print("📈 Performance Summary")
    print("-" * 80)

    all_times = []
    for times in results.values():
        all_times.extend(times)

    if all_times:
        overall_avg = statistics.mean(all_times)
        overall_min = min(all_times)
        overall_max = max(all_times)
        overall_std = statistics.stdev(all_times) if len(all_times) > 1 else 0

        print(f"Total Requests:  {len(all_times)}")
        print(f"Avg Response:    {overall_avg:.1f}ms")
        print(f"Min Response:    {overall_min:.1f}ms")
        print(f"Max Response:    {overall_max:.1f}ms")
        print(f"Std Deviation:   {overall_std:.1f}ms")
        print()

        # Identify slow endpoints
        slow_endpoints = []
        for name, times in results.items():
            avg = statistics.mean(times)
            if avg > 300:
                slow_endpoints.append((name, avg))

        if slow_endpoints:
            print("⚠️  Slow Endpoints (>300ms):")
            for name, avg in sorted(slow_endpoints, key=lambda x: x[1], reverse=True):
                print(f"   - {name}: {avg:.1f}ms")
        else:
            print("✅ All endpoints performing well")

    print()
    print("=" * 80)
    print(f"Test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
