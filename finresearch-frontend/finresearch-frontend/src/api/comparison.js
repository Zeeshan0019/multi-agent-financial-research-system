import client from "./client";

// POST /sessions/:id/compare { document_ids: [id1, id2, ...] }
// -> { companies: [{ document_id, company_name, revenue, net_profit, debt, margin }], summary }
export const compareCompanies = (sessionId, documentIds) =>
  client
    .post(`/sessions/${sessionId}/compare`, { document_ids: documentIds })
    .then((r) => r.data);
