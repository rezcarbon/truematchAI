/**
 * TrueMatch Admin API Client
 * Handles all admin-related API calls with error handling and type safety
 */

import { ApiResponse, PaginatedResponse, PaginationParams } from '@/types/admin';
import type {
  User,
  UserRole,
  UserStatus,
  CreateUserRequest,
  UpdateUserRequest,
  InviteUserRequest,
  AuditEvent,
  AuditFilter,
  AuditQueryResponse,
  ComplianceReportResponse,
  GovernanceConfigStatus,
  GovernanceConfigPatch,
  AnalyticsResponse,
  SystemHealthResponse,
  Subscription,
  Invoice,
  EmailTemplate,
  CreateEmailTemplateRequest,
  UpdateEmailTemplateRequest,
} from '@/types/admin';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

class AdminApiClient {
  private async request<T>(
    method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH',
    endpoint: string,
    data?: unknown,
  ): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    const options: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.getToken()}`,
      },
    };

    if (data) {
      options.body = JSON.stringify(data);
    }

    try {
      const response = await fetch(url, options);

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || `API Error: ${response.status}`);
      }

      return response.json();
    } catch (error) {
      console.error(`API request failed: ${method} ${endpoint}`, error);
      throw error;
    }
  }

  private getToken(): string {
    // Get JWT from session storage or local storage
    if (typeof window !== 'undefined') {
      return localStorage.getItem('auth_token') || '';
    }
    return '';
  }

  // ==================== User Management ====================

  async getUsers(params?: PaginationParams): Promise<PaginatedResponse<User>> {
    const query = new URLSearchParams();
    if (params?.page) query.append('page', params.page.toString());
    if (params?.limit) query.append('limit', params.limit.toString());
    if (params?.sort) query.append('sort', params.sort);
    if (params?.order) query.append('order', params.order);

    const endpoint = `/admin/users${query.toString() ? '?' + query.toString() : ''}`;
    return this.request('GET', endpoint);
  }

  async getUserById(userId: string): Promise<User> {
    return this.request('GET', `/admin/users/${userId}`);
  }

  async createUser(data: CreateUserRequest): Promise<User> {
    return this.request('POST', '/admin/users', data);
  }

  async updateUser(userId: string, data: UpdateUserRequest): Promise<User> {
    return this.request('PUT', `/admin/users/${userId}`, data);
  }

  async deleteUser(userId: string): Promise<{ success: boolean }> {
    return this.request('DELETE', `/admin/users/${userId}`);
  }

  async inviteUsers(data: InviteUserRequest): Promise<{ invited: number; failed: number }> {
    return this.request('POST', '/admin/users/invite', data);
  }

  async searchUsers(query: string, limit = 10): Promise<User[]> {
    const endpoint = `/admin/users/search?q=${encodeURIComponent(query)}&limit=${limit}`;
    return this.request('GET', endpoint);
  }

  // ==================== Audit Trail ====================

  async getAuditEvents(filter?: AuditFilter): Promise<AuditQueryResponse> {
    const query = new URLSearchParams();
    if (filter?.startDate) query.append('startDate', filter.startDate);
    if (filter?.endDate) query.append('endDate', filter.endDate);
    if (filter?.eventType) query.append('eventType', filter.eventType);
    if (filter?.actorId) query.append('actorId', filter.actorId);
    if (filter?.search) query.append('search', filter.search);
    if (filter?.limit) query.append('limit', filter.limit.toString());
    if (filter?.offset) query.append('offset', filter.offset.toString());

    const endpoint = `/admin/audit${query.toString() ? '?' + query.toString() : ''}`;
    return this.request('GET', endpoint);
  }

  async exportAuditLog(format: 'csv' | 'pdf' = 'csv'): Promise<Blob> {
    const url = `${API_BASE}/admin/audit/export?format=${format}`;
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${this.getToken()}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to export audit log');
    }

    return response.blob();
  }

  // ==================== Compliance ====================

  async getComplianceReport(): Promise<ComplianceReportResponse> {
    return this.request('GET', '/admin/compliance/report');
  }

  async getGovernanceConfig(): Promise<GovernanceConfigStatus> {
    return this.request('GET', '/admin/governance/config');
  }

  async updateGovernanceConfig(data: GovernanceConfigPatch): Promise<GovernanceConfigStatus> {
    return this.request('PATCH', '/admin/governance/config', data);
  }

  async exportComplianceReport(format: 'csv' | 'pdf' = 'pdf'): Promise<Blob> {
    const url = `${API_BASE}/admin/compliance/export?format=${format}`;
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${this.getToken()}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to export compliance report');
    }

    return response.blob();
  }

  // ==================== Analytics ====================

  async getAnalytics(period: 'day' | 'week' | 'month' = 'month'): Promise<AnalyticsResponse> {
    return this.request('GET', `/admin/analytics?period=${period}`);
  }

  async getPipelineAnalytics(startDate?: string, endDate?: string): Promise<AnalyticsResponse> {
    const query = new URLSearchParams();
    if (startDate) query.append('startDate', startDate);
    if (endDate) query.append('endDate', endDate);

    const endpoint = `/admin/analytics/pipeline${query.toString() ? '?' + query.toString() : ''}`;
    return this.request('GET', endpoint);
  }

  async getSourceAnalytics(): Promise<AnalyticsResponse> {
    return this.request('GET', '/admin/analytics/sources');
  }

  async getThreeSignalAnalytics(): Promise<AnalyticsResponse> {
    return this.request('GET', '/admin/analytics/three-signal');
  }

  async getRecruiterPerformance(): Promise<AnalyticsResponse> {
    return this.request('GET', '/admin/analytics/recruiter-performance');
  }

  async getDEIAnalytics(): Promise<AnalyticsResponse> {
    return this.request('GET', '/admin/analytics/dei');
  }

  // ==================== System Monitoring ====================

  async getSystemHealth(): Promise<SystemHealthResponse> {
    return this.request('GET', '/admin/system/health');
  }

  async getSystemMetrics(): Promise<SystemHealthResponse> {
    return this.request('GET', '/admin/system/metrics');
  }

  async checkServiceStatus(serviceName: string): Promise<{ status: string; message?: string }> {
    return this.request('GET', `/admin/system/services/${serviceName}`);
  }

  // ==================== Billing ====================

  async getSubscriptions(params?: PaginationParams): Promise<PaginatedResponse<Subscription>> {
    const query = new URLSearchParams();
    if (params?.page) query.append('page', params.page.toString());
    if (params?.limit) query.append('limit', params.limit.toString());

    const endpoint = `/admin/billing/subscriptions${query.toString() ? '?' + query.toString() : ''}`;
    return this.request('GET', endpoint);
  }

  async getSubscriptionById(subscriptionId: string): Promise<Subscription> {
    return this.request('GET', `/admin/billing/subscriptions/${subscriptionId}`);
  }

  async getInvoices(subscriptionId: string): Promise<PaginatedResponse<Invoice>> {
    return this.request('GET', `/admin/billing/subscriptions/${subscriptionId}/invoices`);
  }

  async getInvoicePdf(invoiceId: string): Promise<Blob> {
    const url = `${API_BASE}/admin/billing/invoices/${invoiceId}/pdf`;
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${this.getToken()}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch invoice PDF');
    }

    return response.blob();
  }

  // ==================== Email Templates ====================

  async getEmailTemplates(): Promise<EmailTemplate[]> {
    return this.request('GET', '/admin/email-templates');
  }

  async getEmailTemplateById(templateId: string): Promise<EmailTemplate> {
    return this.request('GET', `/admin/email-templates/${templateId}`);
  }

  async createEmailTemplate(data: CreateEmailTemplateRequest): Promise<EmailTemplate> {
    return this.request('POST', '/admin/email-templates', data);
  }

  async updateEmailTemplate(
    templateId: string,
    data: UpdateEmailTemplateRequest,
  ): Promise<EmailTemplate> {
    return this.request('PUT', `/admin/email-templates/${templateId}`, data);
  }

  async deleteEmailTemplate(templateId: string): Promise<{ success: boolean }> {
    return this.request('DELETE', `/admin/email-templates/${templateId}`);
  }

  async testEmailTemplate(templateId: string, testEmail: string): Promise<{ success: boolean }> {
    return this.request('POST', `/admin/email-templates/${templateId}/test`, { testEmail });
  }

  // ==================== Configuration ====================

  async getConfiguration(): Promise<Record<string, unknown>> {
    return this.request('GET', '/admin/configuration');
  }

  async updateConfiguration(config: Record<string, unknown>): Promise<Record<string, unknown>> {
    return this.request('PATCH', '/admin/configuration', config);
  }

  async getFeatureFlags(): Promise<Record<string, boolean>> {
    return this.request('GET', '/admin/configuration/feature-flags');
  }

  async updateFeatureFlag(flag: string, enabled: boolean): Promise<{ success: boolean }> {
    return this.request('PATCH', `/admin/configuration/feature-flags/${flag}`, { enabled });
  }
}

// Export singleton instance
export const adminApi = new AdminApiClient();

// Export client class for testing
export default AdminApiClient;
