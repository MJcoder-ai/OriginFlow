import { API_BASE_URL } from '../config';

export async function fetchTenantSettings(tenantId: string) {
  const res = await fetch(`${API_BASE_URL}/tenant/${tenantId}/settings`, {
    credentials: 'include',
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function updateTenantSettings(tenantId: string, body: any) {
  const res = await fetch(`${API_BASE_URL}/tenant/${tenantId}/settings`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function listApprovals(
  tenantId: string,
  status?: 'pending' | 'approved' | 'rejected',
  projectId?: string,
) {
  const qs = new URLSearchParams();
  if (status) qs.set('status', status);
  if (projectId) qs.set('project_id', projectId);
  const res = await fetch(
    `${API_BASE_URL}/tenant/${tenantId}/approvals?${qs.toString()}`,
    { credentials: 'include' },
  );
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function approveAction(pendingId: number, reason?: string) {
  const res = await fetch(`${API_BASE_URL}/approvals/${pendingId}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ reason }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function rejectAction(pendingId: number, reason?: string) {
  const res = await fetch(`${API_BASE_URL}/approvals/${pendingId}/reject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ reason }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

