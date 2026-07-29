/**
 * DataFlow JavaScript SDK — Client library for the DataFlow platform.
 *
 * Installation:
 *   npm install @dataflow/sdk
 *
 * Usage:
 *   import { DataFlowClient } from '@dataflow/sdk';
 *   const client = new DataFlowClient({ apiKey: 'dfk_...', baseUrl: 'http://localhost:8080' });
 *   const dashboards = await client.analytics.listDashboards();
 *   const result = await client.datasets.upload(file);
 *   const answer = await client.ai.ask('What are the top trends?');
 */

class DataFlowClient {
  constructor({ apiKey, baseUrl = 'http://localhost:8080' }) {
    this.apiKey = apiKey || process.env.DATAFLOW_API_KEY || '';
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.datasets = new DatasetsAPI(this);
    this.analytics = new AnalyticsAPI(this);
    this.ai = new AIAPI(this);
    this.workflows = new WorkflowsAPI(this);
    this.reports = new ReportsAPI(this);
  }

  _headers() {
    return { 'X-API-Key': this.apiKey, 'Content-Type': 'application/json' };
  }

  async _get(path) {
    const resp = await fetch(`${this.baseUrl}${path}`, { headers: this._headers() });
    if (!resp.ok) throw new Error(`API error: ${resp.status}`);
    return resp.json();
  }

  async _post(path, data) {
    const resp = await fetch(`${this.baseUrl}${path}`, {
      method: 'POST',
      headers: this._headers(),
      body: data ? JSON.stringify(data) : undefined,
    });
    if (!resp.ok) throw new Error(`API error: ${resp.status}`);
    return resp.json();
  }

  async _upload(path, file) {
    const formData = new FormData();
    formData.append('file', file);
    const resp = await fetch(`${this.baseUrl}${path}`, {
      method: 'POST',
      headers: { 'X-API-Key': this.apiKey },
      body: formData,
    });
    if (!resp.ok) throw new Error(`API error: ${resp.status}`);
    return resp.json();
  }
}

class DatasetsAPI {
  constructor(client) { this.client = client; }
  async upload(file) { return this.client._upload('/public/datasets/upload', file); }
  async list() { return (await this.client._get('/public/datasets')).data || []; }
}

class AnalyticsAPI {
  constructor(client) { this.client = client; }
  async listDashboards() { return (await this.client._get('/public/analytics/dashboards')).data || []; }
  async listKpis() { return (await this.client._get('/public/analytics/kpis')).data || []; }
}

class AIAPI {
  constructor(client) { this.client = client; }
  async ask(question) { return (await this.client._post('/public/ai/ask', { question })).data || {}; }
}

class WorkflowsAPI {
  constructor(client) { this.client = client; }
  async list() { return (await this.client._get('/public/workflows')).data || []; }
}

class ReportsAPI {
  constructor(client) { this.client = client; }
  async list() { return (await this.client._get('/public/reports')).data || []; }
}

module.exports = { DataFlowClient };
