import { API_BASE_URL } from '@/config';

export interface SalaryData {
  role_title: string;
  level: string;
  location: string;
  min_salary: number;
  midpoint_salary: number;
  max_salary: number;
  percentile: number;
  source: string;
}

export interface OfferRecommendation {
  recommended_salary: number;
  min_acceptable: number;
  max_acceptable: number;
  win_likelihood: number;
  negotiation_buffer: number;
  justification: string;
}

export interface SalaryBenchmark {
  role_title: string;
  level: string;
  location: string;
  market_data: SalaryData;
  offer_recommendation: OfferRecommendation;
  created_at: string;
}

export interface BenchmarkRequest {
  role_title: string;
  level: string;
  location: string;
  candidate_id?: string;
  skills_match?: number;
}

export interface BulkBenchmarkRequest {
  benchmarks: BenchmarkRequest[];
}

export class SalaryBenchmarkingApiClient {
  private baseUrl = `${API_BASE_URL}/api/v1/salary-benchmarking`;

  async benchmark(request: BenchmarkRequest): Promise<SalaryBenchmark> {
    const response = await fetch(`${this.baseUrl}/benchmark`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!response.ok) throw new Error(`Benchmark failed: ${response.statusText}`);
    return response.json();
  }

  async benchmarkForCandidate(candidateId: string, positionId: string): Promise<SalaryBenchmark> {
    const response = await fetch(`${this.baseUrl}/benchmark/candidate/${candidateId}/${positionId}`);
    if (!response.ok) throw new Error(`Candidate benchmark failed: ${response.statusText}`);
    return response.json();
  }

  async bulkBenchmark(request: BulkBenchmarkRequest): Promise<SalaryBenchmark[]> {
    const response = await fetch(`${this.baseUrl}/benchmark/bulk`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    if (!response.ok) throw new Error(`Bulk benchmark failed: ${response.statusText}`);
    const data = await response.json();
    return data.benchmarks;
  }

  async updateData(): Promise<{ status: string; records_updated: number }> {
    const response = await fetch(`${this.baseUrl}/data/update`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!response.ok) throw new Error(`Data update failed: ${response.statusText}`);
    return response.json();
  }
}

export const salaryBenchmarkingApi = new SalaryBenchmarkingApiClient();
