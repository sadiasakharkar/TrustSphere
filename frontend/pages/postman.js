import { useMemo, useState } from 'react';
import Layout from '../components/Layout';
import RequireAuth from '../components/RequireAuth';
import PageContainer from '../components/soc/PageContainer';
import PageHeader from '../components/soc/PageHeader';
import StatusBadge from '../components/soc/StatusBadge';
import { apiRequest, getApiBaseUrl, isDemoMode } from '../services/api/apiClient';

function buildMockResponse({ method, endpoint, body, error = null }) {
  return {
    status: error ? 'DEMO_FALLBACK' : 'OK',
    method,
    endpoint,
    baseUrl: getApiBaseUrl(),
    timestamp: new Date().toISOString(),
    mode: isDemoMode() ? 'offline-demo' : 'local-runtime',
    requestBody: body || null,
    message: error
      ? 'Live request was not available, so TrustSphere returned a local demo response.'
      : 'TrustSphere processed the request in the embedded Postman workspace.',
    error: error || null,
  };
}

export default function PostmanPage() {
  const [method, setMethod] = useState('POST');
  const [endpoint, setEndpoint] = useState('/api/email/analyze');
  const [payload, setPayload] = useState('{\n  "input": "Click here urgently to verify your bank password."\n}');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [response, setResponse] = useState(null);

  const formattedBaseUrl = useMemo(() => getApiBaseUrl(), []);

  const handleSend = async () => {
    if (!endpoint.trim()) {
      setError('Enter an API endpoint before sending the request.');
      return;
    }

    let parsedBody = null;
    if (!['GET', 'HEAD'].includes(method) && payload.trim()) {
      try {
        parsedBody = JSON.parse(payload);
      } catch {
        setError('Request body must be valid JSON.');
        return;
      }
    }

    setLoading(true);
    setError('');
    try {
      const result = await apiRequest(endpoint.trim(), {
        method,
        body: ['GET', 'HEAD'].includes(method) ? undefined : JSON.stringify(parsedBody || {}),
        fallbackData: () => buildMockResponse({
          method,
          endpoint: endpoint.trim(),
          body: parsedBody,
          error: 'Endpoint unavailable in demo mode',
        }),
      });

      setResponse({
        status: result.meta?.fallback ? 'DEMO_FALLBACK' : 'SUCCESS',
        method,
        endpoint: endpoint.trim(),
        timestamp: result.meta?.timestamp || new Date().toISOString(),
        data: result.data,
        meta: result.meta,
      });
    } catch (err) {
      setResponse({
        status: 'DEMO_FALLBACK',
        method,
        endpoint: endpoint.trim(),
        timestamp: new Date().toISOString(),
        data: buildMockResponse({
          method,
          endpoint: endpoint.trim(),
          body: parsedBody,
          error: err.message || 'Request failed',
        }),
        meta: { fallback: true },
      });
      setError(err.message || 'Unable to reach the requested endpoint.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <RequireAuth>
      <Layout>
        <PageContainer>
          <PageHeader
            kicker="Workspace Tool"
            title="Postman"
            description="Use this built-in request console to test local TrustSphere endpoints with a Postman-style input and output workflow."
          />

          <section className="grid gap-6 xl:grid-cols-[0.95fr,1.05fr]">
            <section className="soc-panel">
              <p className="soc-kicker">Request Builder</p>
              <h2 className="mt-2 text-lg font-semibold text-white">Compose API request</h2>
              <p className="mt-2 text-sm leading-6 soc-text-muted">
                Base URL: <span className="text-white">{formattedBaseUrl}</span>
              </p>

              <div className="mt-5 grid gap-4 md:grid-cols-[160px,1fr]">
                <div>
                  <label className="mb-2 block text-[11px] font-bold uppercase tracking-[0.18em] text-[rgba(193,198,215,0.6)]">Method</label>
                  <select className="soc-input" value={method} onChange={(event) => setMethod(event.target.value)}>
                    {['GET', 'POST', 'PUT', 'PATCH', 'DELETE'].map((item) => (
                      <option key={item} value={item}>{item}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="mb-2 block text-[11px] font-bold uppercase tracking-[0.18em] text-[rgba(193,198,215,0.6)]">Endpoint</label>
                  <input className="soc-input" value={endpoint} onChange={(event) => setEndpoint(event.target.value)} placeholder="/api/email/analyze" />
                </div>
              </div>

              <div className="mt-5">
                <label className="mb-2 block text-[11px] font-bold uppercase tracking-[0.18em] text-[rgba(193,198,215,0.6)]">JSON Body</label>
                <textarea
                  className="min-h-[260px] w-full rounded-2xl border border-[rgba(65,71,85,0.45)] bg-[rgba(16,20,26,0.86)] px-4 py-4 font-mono text-sm leading-7 text-white outline-none transition focus:border-[#4b8eff]"
                  value={payload}
                  onChange={(event) => setPayload(event.target.value)}
                  placeholder='{\n  "input": "Paste request JSON here"\n}'
                />
              </div>

              {error ? <p className="mt-4 text-sm text-[#ffb3ad]">{error}</p> : null}

              <div className="mt-5 flex flex-wrap gap-3">
                <button type="button" className="soc-btn-primary" onClick={handleSend} disabled={loading}>
                  <span className="material-symbols-outlined text-base">send</span>
                  {loading ? 'Sending...' : 'Send Request'}
                </button>
                <button
                  type="button"
                  className="soc-btn-secondary"
                  onClick={() => {
                    setMethod('POST');
                    setEndpoint('/api/email/analyze');
                    setPayload('{\n  "input": "Click here urgently to verify your bank password."\n}');
                    setError('');
                  }}
                >
                  Reset Example
                </button>
              </div>
            </section>

            <section className="soc-panel">
              <p className="soc-kicker">Response Viewer</p>
              <h2 className="mt-2 text-lg font-semibold text-white">Output</h2>

              {!response ? (
                <p className="mt-4 text-sm leading-6 soc-text-muted">
                  Send a request to see the response payload, request status, and timestamp here.
                </p>
              ) : (
                <div className="mt-4 space-y-4">
                  <div className="flex flex-wrap gap-2">
                    <StatusBadge tone={response.status === 'SUCCESS' ? 'default' : 'medium'}>{response.status}</StatusBadge>
                    <StatusBadge tone="default">{response.method}</StatusBadge>
                    <StatusBadge tone="default">{response.endpoint}</StatusBadge>
                  </div>

                  <div className="soc-panel-muted">
                    <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">Response timestamp</p>
                    <p className="mt-2 text-sm text-white">{response.timestamp}</p>
                  </div>

                  <div className="soc-panel-muted">
                    <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">Payload</p>
                    <pre className="mt-3 overflow-x-auto whitespace-pre-wrap rounded-2xl bg-[rgba(10,14,20,0.88)] p-4 font-mono text-xs leading-6 text-[rgba(223,226,235,0.88)]">
                      {JSON.stringify(response.data, null, 2)}
                    </pre>
                  </div>
                </div>
              )}
            </section>
          </section>
        </PageContainer>
      </Layout>
    </RequireAuth>
  );
}
