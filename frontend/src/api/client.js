const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {})
    },
    ...options
  });

  if (!response.ok) {
    const text = await response.text();
    let message = text;
    let detail = null;
    try {
      const parsed = JSON.parse(text);
      detail = parsed?.detail ?? null;
      message = typeof parsed.detail === "string" ? parsed.detail : JSON.stringify(parsed.detail);
    } catch {
      message = text;
    }
    const error = new Error(message || `Request failed: ${response.status}`);
    error.detail = detail;
    throw error;
  }

  return response.json();
}

export const api = {
  listDatasets: () => request("/api/datasets"),
  getDatasetContext: (datasetId) => request(`/api/datasets/${datasetId}/context`),
  createProposal: (payload) =>
    request("/api/ai/proposals", {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  createProposalJob: (payload) =>
    request("/api/ai/proposals/jobs", {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  getProposalJob: (jobId) => request(`/api/ai/proposals/jobs/${jobId}`),
  getProposal: (proposalId) => request(`/api/ai/proposals/${proposalId}`),
  updateProposal: (proposalId, payload) =>
    request(`/api/ai/proposals/${proposalId}`, {
      method: "PATCH",
      body: JSON.stringify(payload)
    }),
  approveProposal: (proposalId, payload) =>
    request(`/api/ai/proposals/${proposalId}/approve`, {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  rejectProposal: (proposalId, payload) =>
    request(`/api/ai/proposals/${proposalId}/reject`, {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  runExecution: (payload) =>
    request("/api/executions", {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  getLogs: (traceId) => request(`/api/logs/${traceId}`)
};
