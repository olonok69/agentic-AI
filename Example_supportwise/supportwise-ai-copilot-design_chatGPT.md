# SupportWise AI Co‑pilot — Technical Design (MVP)

This document proposes an MVP architecture for an AI Co‑pilot that enables SupportWise’s Head of Support, Brenda, to query Zendesk Support data in natural language and receive accurate answers, insights, and visualizations within seconds. The design balances fast interactive queries with deeper analyses that can run asynchronously, while emphasizing reliability, security, and cost control.

---

## 1) System Architecture Overview

Text-based component map and interactions:

- Data Sources
  - Zendesk Support: tickets, ticket fields, comments, users, tags, audit events.

- Ingestion & Transformation
  - Ingestion Connector: A managed connector (e.g., Airbyte Zendesk source or Singer tap) for initial backfill and incremental sync.
  - Orchestrator: Workflow engine (Airflow/Dagster) to schedule backfills, incremental updates, and derived feature jobs (sentiment, topics, embeddings).
  - Transformation Layer: dbt transforms to create clean, analytics-friendly models and pre-aggregations.

- Storage Layer
  - Data Warehouse (DW): Columnar analytics store for fast aggregates and joins (e.g., Snowflake/BigQuery/ClickHouse). Serves SQL for counts, trends, cohorts.
  - Operational DB: Postgres for app metadata (sessions, users, saved reports, jobs, cache metadata).
  - Vector Index: pgvector (in Postgres) or a managed vector DB (Pinecone/Weaviate) for semantic retrieval over comments and summaries.
  - Object Storage: For chart images, CSV exports, model artifacts, and cached result blobs.

- AI & Analytics Services
  - Embeddings Service: Batch and streaming embedding generation for comments and derived summaries.
  - LLM Gateway: Abstraction over one or more LLM providers with routing, retries, cost/latency-aware model selection, and fallbacks.
  - Analytics Services: Topic clustering, sentiment classification, trend detection, summarization; run synchronously for small windows or via queued jobs for large windows.

- Application/API Layer
  - API Gateway: FastAPI/Express service exposing chat, SQL execution, retrieval, visualization, and report management endpoints.
  - Planner/Orchestrator: “Agent” that translates NL into a plan: resolve intent/time window, choose data tools (SQL vs retrieval), request charts, stream partial results.
  - Visualization Renderer: Validates a Vega-Lite spec, renders images (PNG/SVG) server-side, and stores/serves them.
  - Job Queue & Workers: Celery/RQ (Redis-backed) or Cloud queue for long-running analysis; status updates pushed to client.

- Client UX
  - Web App (Chat UI): React/TypeScript app with streaming answers, inline charts, and controls to save and rerun reports.
  - Notifications: Email/Slack/Teams for background job completion.

- Observability & Governance
  - Tracing/Logging/Metrics (OpenTelemetry), Prompt+query audit logs, model eval harness, RBAC, and PII redaction.

Interaction summary:
1) Ingestion keeps DW/vector index up-to-date.
2) Brenda asks a question in chat. The Planner detects intent and picks a path: direct SQL vs semantic retrieval + summarization, or schedules a background job.
3) The system returns a final answer and optional chart; complex queries may stream interim results or notify on completion.

---

## 2) Data Flow Description

End-to-end flows:

- Batch/Incremental Ingestion
  1) Initial Backfill: Airbyte pulls all Zendesk tickets, comments, tags, users into staging tables in DW and raw files in object storage.
  2) Incremental Sync: Run every 5–15 minutes using Zendesk incremental endpoints; apply upserts into DW staging.
  3) Transform: dbt builds curated models, daily aggregates, and materialized views (e.g., ticket counts by priority/status/day).
  4) Derived Features: Workers compute embeddings for new/changed comments, sentiment scores, topic labels; store vectors in pgvector and features back in DW.

- Interactive Query (fast path: seconds)
  1) Chat message hits API Gateway; session context (filters, preferred time window) is loaded from Postgres.
  2) Planner classifies intent and complexity. For simple counts/trends, it uses schema-annotated SQL generation with guardrails, preferring pre-aggregated tables.
  3) SQL executes in DW; results are validated (row caps, type checks), then returned to client. If a chart is requested, a Vega-Lite spec is generated/validated and rendered.

- Insight Query (semantic path)
  1) For “why”/“what were customers complaining about?”: Planner narrows the time window, runs filtered DW query to get candidate comment IDs, retrieves their embeddings, and performs ANN search in vector index.
  2) Cluster or rank top themes; summarization runs over top-k snippets with citations. For large windows, fallback: queue a job and stream a preview, then notify when complete.

- Saved Reports & Scheduling
  1) User saves a chart/report. The system stores a canonical SQL template, parameter bindings, and a validated Vega-Lite spec.
  2) Scheduler runs reports weekly; images/data are generated and linked; user gets a notification and a permalink.

---

## 3) Technology Choices (and rationale)

- Connectors & Orchestration
  - Airbyte (Zendesk source): Reliable, incremental sync, fast to stand up. Alternatives: Singer/Meltano.
  - Dagster/Airflow: Clear DAGs for ingestion, transforms, and feature derivation; strong observability.
  - dbt: Manage transformations, tests, and documentation; enables pre-aggregations and materialized views.

- Storage & Compute
  - Data Warehouse: Snowflake or BigQuery for columnar analytics at scale; sub-second to seconds on million-row scans; time travel; strong governance.
    - Cost/ops alternative: ClickHouse (self-managed) or DuckDB+MotherDuck for quick MVPs.
  - Operational DB: Postgres for app state (sessions, saved reports, jobs, cache metadata).
  - Vector Index: pgvector in Postgres to minimize ops for MVP; scale-out option: Pinecone/Weaviate if vectors exceed tens of millions or require cross-region replication.
  - Object Storage: S3/GCS/Azure Blob for charts/exports and cached artifacts.

- AI/ML
  - LLM Gateway: Abstraction supporting multiple providers (OpenAI/Anthropic/local), retries, cost-aware routing (e.g., “mini” models for intent, larger models for summarization).
  - Embeddings: text-embedding-3-large or smaller variants for cost/latency trade-offs; configurable.
  - Analytics: Light-weight topic modeling (e.g., BERTopic-like approach with embeddings + HDBSCAN) and rule-based heuristics for small windows; background batch for large windows.

- Backend & Visualization
  - API Layer: FastAPI (Python) for strong async I/O, Pydantic contracts, and Python-native data stack.
  - Job Queue: Celery/RQ with Redis for background tasks and progress updates.
  - Visualization: Vega-Lite (validated by JSON Schema) rendered via Altair/vl-convert or Node-based renderer; PNG/SVG stored in object storage.

- Observability & Security
  - OpenTelemetry traces and metrics; Sentry for errors.
  - Secrets: Vault or cloud KMS; row/column-level security in DW.
  - PII redaction pipeline and prompt defenses (prompt injection filtering, allowlisted tools).

Trade-offs are noted throughout the detailed sections.

---

## 4) Data Schema Structures

Key models (DW = Data Warehouse, OP = Operational Postgres):

- DW: tickets
  - ticket_id (PK)
  - created_at, updated_at, resolved_at, first_response_at
  - status (open, pending, on_hold, solved, closed)
  - priority (low, normal, high, urgent)
  - requester_id, assignee_id, group_id
  - tags ARRAY<STRING>
  - custom_fields JSON (flatten selected fields into typed columns where high-value)
  - product_area, issue_type (derived from custom fields where applicable)

- DW: comments
  - comment_id (PK)
  - ticket_id (FK)
  - author_id
  - public BOOLEAN
  - created_at
  - body_text STRING
  - body_html STRING (optional)
  - token_count INT (derived)
  - sentiment_score FLOAT (derived)
  - topic_labels ARRAY<STRING> (derived)

- DW: comment_embeddings (optional if not using pgvector in OP)
  - comment_id (PK/FK)
  - embedding VECTOR(1536) or ARRAY<FLOAT>
  - model_name STRING
  - created_at TIMESTAMP

- DW: users, groups, tags (dimension tables)

- DW: fact_ticket_daily (pre-aggregated)
  - date
  - priority, status
  - product_area, issue_type
  - tickets_created INT
  - tickets_resolved INT
  - first_response_sla_breaches INT
  - avg_first_response_minutes FLOAT
  - PRIMARY KEY (date, priority, status, product_area, issue_type)

- OP: sessions
  - session_id (PK), user_id (FK), created_at, last_active_at
  - context JSONB (default filters, time horizon)

- OP: saved_reports
  - report_id (PK), name, owner_user_id, created_at, updated_at
  - sql_template TEXT (parameterized)
  - default_params JSONB
  - vega_spec JSONB (validated)
  - description TEXT, version INT

- OP: report_runs
  - run_id (PK), report_id (FK), requested_by, requested_at, status ENUM(pending,running,success,failed)
  - params JSONB, result_url TEXT (chart/data), row_count INT, runtime_ms INT, error TEXT

- OP: jobs
  - job_id (PK), type, payload JSONB, status, progress FLOAT, started_at, finished_at, error TEXT

API contracts (sketch):

- POST /chat/query
  Request:
  {
    "session_id": "uuid",
    "message": "How many urgent tickets last week?",
    "prefs": { "visualization": "auto" }
  }
  Response (streamed or final):
  {
    "answer": "We had 132 urgent tickets last week.",
    "data": { "rows": [{"count": 132, "week": "2025-09-08"}] },
    "chart": { "image_url": "https://…/chart.png", "vega_spec": { … } },
    "trace_id": "…", "latency_ms": 850
  }

- POST /reports
  Request:
  {
    "name": "Weekly Ticket Report",
    "sql_template": "SELECT date, COUNT(*) as tickets FROM fact_ticket_daily WHERE date BETWEEN :start AND :end GROUP BY 1 ORDER BY 1",
    "default_params": { "period": "last_week" },
    "vega_spec": { /* vega-lite spec */ }
  }
  Response: { "report_id": "uuid" }

- POST /reports/{id}/run
  Request: { "params": { "start": "2025-09-08", "end": "2025-09-14" } }
  Response: { "run_id": "uuid", "status": "running" }

- GET /jobs/{job_id}
  Response: { "status": "running", "progress": 0.42 }

---

## 5) Detailed Technical Explanations — Key Architectural Considerations

1) User Experience Flow (seamless & reliable)
- Steps
  - Intent Detection: Lightweight model classifies query type (metric, list, comparison, insight/why, visualization request) and extracts constraints (time window, priority, product area).
  - Planning: The agent selects tools: direct SQL on pre-aggregates for counts; retrieval + clustering + summarization for insights; chart renderer if visualization requested.
  - Execution: Safe SQL generation with schema hints/examples; limit/timeout guards; retries with simplified query if needed. For semantic path, restrict to filtered time window and cap k results.
  - Streaming UX: Immediately reflect parsed intent and filters, then stream the numeric result; render the chart as soon as data returns; provide a “Save as Report” CTA.
- Challenges & Mitigations
  - SQL Hallucinations: Constrain via schema registry, example queries, unit tests; validate SQL with a linter and dry-run EXPLAIN for complexity caps.
  - Latency: Prefer pre-aggregated tables; pushdowns to DW; cache recent results; parallelize data fetch + chart render.
  - Robustness: Typed responses; JSON schema validation of tool outputs; graceful fallbacks to simpler answers.

2) Historical Data Challenges (millions of tickets/comments)
- Partition/Cluster by date to prune scans.
- Pre-aggregations (fact_ticket_daily, materialized views) to serve most “count by X over time” in O(ms–s).
- Vector Index sharding/HNSW for ANN; generate embeddings incrementally and in backfill batches.
- For large windows: two-stage approach (sample+preview fast, full job async); notify with permalink when done.
- Use warehouse caches and result set caching; aggressively reuse previous week’s computations for recurring reports.

3) Business Data Risks (safety & production readiness)
- Data Leakage: Strict RBAC; row/column-level security; redact PII before LLM calls; isolate external model providers (egress firewall, approved endpoints).
- Prompt Injection: Sanitize/comment text; strip HTML/script; use allowlisted tools and content filters; scan outputs for sensitive leaks.
- Governance: Audit logs for queries, prompts, and data access; configurable retention; anomaly detection on access patterns.
- Reliability: Circuit breakers for provider outages; provider fallbacks; idempotent jobs; exactly-once ingestion semantics.
- Compliance: Encryption in transit and at rest; key management with KMS; periodic access reviews.

4) Complex Business Questions (beyond counts)
- Derived Signals: Ticket-level sentiment and aspect-based sentiment (feature-specific); topic labels on rolling windows.
- RAG Pipeline: Filter comments by time/priority/product area in DW; retrieve top-k semantically similar comments; summarize with citations and counts per theme.
- Trend Analysis: Compare topic distributions across periods; highlight deltas; correlate spikes with releases.
- Human-in-the-Loop: Allow tagging corrections; feed back to topic models; maintain taxonomy for product areas.
- Evaluation: Keep a gold set of questions/answers; measure precision of topics, sentiment accuracy, and summary faithfulness.

5) Workflow Efficiency (reusable weekly reports)
- Report Templates: Persisted SQL + validated Vega-Lite spec + default parameters; one-click “Save as Report”.
- Scheduling: Cron-like scheduler runs weekly; parametrization for “last full week”; delivers image + CSV.
- Versioning: Update reports safely with version bump and preview; rollback on failure.
- Catalog & Sharing: Searchable report list with owners, tags; RBAC for visibility; permalinks for stakeholders.

6) Data Visualization Needs (chart generation)
- Deterministic Spec Generation: LLM proposes a spec; backend validates via JSON Schema and whitelists mark types/encodings.
- Data Limits: Enforce row caps; if data too large, aggregate in DW before chart render.
- Server-side Render: Headless rendering for consistent images; accessible alt text and colorblind-friendly palettes.
- Reproducibility: Store spec + query + data hash; cache rendered images by content hash for reuse.

7) Operational Cost Management
- Cost-aware Planner: Choose small/cheap models for intent; only escalate model size when needed; cap tokens and context.
- Query Budgets: Per-user/org quotas; warn on expensive scans; require confirmation for very large jobs.
- Storage Tiers: Cold archive old raw data; keep hot pre-aggregates and recent embeddings.
- Right-size Engines: Auto-suspend DW compute when idle; burst only for jobs; batch embeddings.

8) Technology Evolution (future-proof)
- Provider Abstractions: Strategy pattern for LLMs and embeddings; config-driven provider selection; A/B switch.
- Tool Interfaces: Typed tool contracts (run_sql, retrieve_comments, generate_chart) with versioning and tests.
- Feature Flags: Enable/disable new chains; canary rollout; telemetry-driven reversions.
- Schema & ETL: dbt contracts/tests; incremental models; zero-downtime migrations.
- Portability: DW-agnostic SQL in dbt where possible; vector DB interchangeable behind repository interface.

---

## 6) Example Pre-aggregations and Indices

- fact_ticket_daily: clustered by date; materialized; refreshed incrementally.
- comment_embeddings: HNSW index on vector column; filterable by date/product_area via metadata columns.
- Common materialized views:
  - mv_tickets_by_priority_last_30d(priority, day, count)
  - mv_oldest_unresolved(limit=N)

---

## 7) Example Prompts and Guardrails (sketch)

- System constraints for SQL generation: “Use only tables {tickets, fact_ticket_daily, …}. Prefer fact_ticket_daily for counts over time. Never SELECT body_text. Limit 100 rows. Time defaults to last 7 days unless specified.”
- Chart constraints: “Only produce valid Vega-Lite v5 specs. Use fields present in provided data schema. Bar/line/pie only for MVP.”

---

## 8) Operations, Monitoring, and SLOs

- SLOs
  - P50 interactive query latency: < 2s; P95 < 6s
  - Background job completion for 3-month windows: < 30m
  - Ingestion lag: < 10m from Zendesk to DW
- Monitoring
  - Traces for each tool call (planner, SQL, retrieval, render)
  - Model cost and token usage per request
  - Data freshness alerts; failed job alarms; chart validation errors
- Runbooks
  - Provider outage fallback (switch to backup model)
  - DW throttle (reduce concurrency, serve cache)
  - Rebuild embeddings/materialized views

---

## 9) MVP Scope vs. Future Enhancements

- In MVP
  - Basic NL->SQL for counts, lists, top-N
  - Topic clustering + summarization for last 30 days
  - Server-rendered bar/line charts; save & schedule reports
  - Incremental ingestion + pre-aggregations; sentiment scoring
  - Cost-aware model routing; basic RBAC and PII redaction

- Future
  - Cohort analyses, retention, SLA breach root-cause
  - Aspect-based sentiment at product/feature granularity
  - Fine-tuned models, active-learning loop
  - Cross-system joins (product analytics, release notes)
  - Natural language chart editing and dashboarding

---

## 10) Acceptance Criteria (for the MVP)

- Brenda can ask: “How many tickets with ‘urgent’ priority were created last week?” and receive an answer in < 2s, with optional bar chart.
- Brenda can ask: “What are our oldest unresolved tickets?” and receive a list with links to Zendesk tickets.
- Brenda can ask: “We saw a 15% spike in ‘high’ priority tickets last month. What were customers complaining about?” and receive a themed summary with citations; if the full window is large, a preview is shown and the full result arrives via notification.
- Brenda can say: “Save this as ‘Weekly Ticket Report’” and rerun it next week; scheduled delivery works.
- Security controls: PII never leaves our boundary unredacted; audit logs show who accessed what and when.

---

## 11) Appendix — Example SQL and Vega-Lite

- Example SQL (counts by priority last week)
SELECT priority, COUNT(*) AS tickets
FROM tickets
WHERE created_at >= DATEADD('day', -7, CURRENT_DATE)
GROUP BY 1
ORDER BY tickets DESC;

- Vega-Lite (bar chart sketch)
{
  "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
  "mark": "bar",
  "encoding": {
    "x": {"field": "priority", "type": "nominal", "sort": "-y"},
    "y": {"field": "tickets", "type": "quantitative"}
  },
  "data": {"name": "table"}
}

---

This design emphasizes fast paths for simple questions, scalable async paths for deep insights, strong safety and governance, and a modular foundation that evolves with rapidly changing AI tooling.
