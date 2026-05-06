import type { Analytics, Catalog, Lead, LeadInput } from './types';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    }
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export function getApiBaseUrl(): string {
  return API_BASE_URL;
}

export async function fetchCatalog(): Promise<Catalog> {
  return request<Catalog>('/api/catalog');
}

export async function createLead(payload: LeadInput): Promise<{ ok: boolean; lead: Lead; next_actions: { whatsapp_url: string; payment_link?: string; recommended_offer: string } }> {
  return request('/api/leads', { method: 'POST', body: JSON.stringify(payload) });
}

export async function trackEvent(event_type: string, payload: Record<string, unknown> = {}): Promise<void> {
  try {
    await request('/api/events', { method: 'POST', body: JSON.stringify({ event_type, page: window.location.pathname, offer_id: String(payload.offer_id || ''), value: Number(payload.value || 0), payload }) });
  } catch {
    // Tracking must never break the funnel.
  }
}

export async function fetchAnalytics(adminToken: string): Promise<Analytics> {
  return request<Analytics>('/api/admin/analytics', { headers: { 'X-Admin-Token': adminToken } });
}

export async function fetchLeads(adminToken: string): Promise<Lead[]> {
  return request<Lead[]>('/api/admin/leads?limit=200', { headers: { 'X-Admin-Token': adminToken } });
}

export async function updateLeadStatus(adminToken: string, leadId: number, status: string): Promise<void> {
  await request(`/api/admin/leads/${leadId}`, { method: 'PATCH', headers: { 'X-Admin-Token': adminToken }, body: JSON.stringify({ status }) });
}

export async function downloadLeadsCsv(adminToken: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/admin/export/leads.csv`, { headers: { 'X-Admin-Token': adminToken } });
  if (!res.ok) throw new Error(await res.text());
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'puglia-profit-leads.csv';
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
