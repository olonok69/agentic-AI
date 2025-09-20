# SupportWise AI Co-pilot Technical Design Document

## Executive Summary

This document outlines the technical architecture for SupportWise's AI Co-pilot, a natural language interface that empowers our Head of Support to extract actionable insights from millions of Zendesk tickets. The system prioritizes pragmatic choices for rapid MVP delivery while maintaining a foundation for scale and evolution.

---

## 1. System Architecture Overview

### Core Components

The architecture follows a modular, service-oriented design with clear separation of concerns:

**Data Ingestion Layer**
- Zendesk API Connector: Manages incremental data synchronization from Zendesk to our data warehouse
- Change Data Capture (CDC) Pipeline: Tracks updates to tickets and comments in near real-time
- Data Validation Service: Ensures data quality and consistency before storage

**Storage Layer**
- Operational Data Store: PostgreSQL database for hot data (last 90 days)
- Data Warehouse: Snowflake for historical data and complex analytics
- Vector Database: Pinecone for semantic search across comment text
- Cache Layer: Redis for frequently accessed data and query results

**Processing Layer**
- Query Parser: Converts natural language to structured intent and parameters
- Query Router: Determines optimal execution path based on query complexity
- Analytics Engine: Handles SQL generation and execution against appropriate data stores
- ML Pipeline: Manages sentiment analysis, categorization, and embedding generation

**AI Layer**
- LLM Gateway: Abstraction layer for multiple LLM providers (OpenAI GPT-4, Claude)
- Prompt Management: Version-controlled prompt templates with A/B testing capability
- Context Builder: Assembles relevant context from multiple data sources

**API & Interface Layer**
- GraphQL API: Flexible query interface for the frontend
- WebSocket Server: Real-time updates for long-running queries
- Visualization Service: Chart generation using D3.js server-side rendering

**Frontend**
- React-based chat interface with real-time updates
- Interactive visualization components
- Saved query management interface

### Component Interactions

The system operates on an event-driven architecture where:
1. User queries trigger events that flow through the Query Parser
2. The Query Router determines whether to use cached results, query hot data, or initiate background processing
3. Results are assembled by the Context Builder and formatted by the LLM
4. Visualizations are generated on-demand and cached for reuse

---

## 2. Data Flow Description

### Ingestion Flow (Zendesk → Storage)

1. **Initial Historical Load**
   - Bulk export of historical data via Zendesk API
   - Parallel processing using Apache Spark for transformation
   - Load into Snowflake staging tables

2. **Incremental Updates**
   - Webhook listeners for real-time ticket/comment events
   - 5-minute polling for missed webhooks (fallback)
   - CDC pipeline updates both PostgreSQL (hot) and Snowflake (cold)

3. **Text Processing Pipeline**
   - Comments flow through sentiment analysis model
   - Generate embeddings for semantic search
   - Store vectors in Pinecone with metadata pointers

### Query Flow (User → Response)

1. **Simple Query Path** (e.g., "How many urgent tickets today?")
   - Natural language → Query Parser → SQL generation
   - Check Redis cache (TTL: 5 minutes for real-time metrics)
   - Query PostgreSQL if cache miss
   - Format response and return

2. **Complex Query Path** (e.g., "Why are customers unhappy with auto-sync?")
   - Natural language → Query Parser → Intent classification
   - Parallel execution:
     - Vector search in Pinecone for relevant comments
     - SQL aggregation in Snowflake for metrics
     - Sentiment analysis on filtered results
   - LLM synthesizes findings into coherent response
   - Generate visualization if applicable

3. **Background Processing Path** (Large historical analyses)
   - Job queued in task queue (Celery + RabbitMQ)
   - Progress updates via WebSocket
   - Results stored in S3 with pre-signed URL
   - Notification sent when complete

---

## 3. Technology Choices

### Data Storage
- **PostgreSQL**: ACID compliance for operational data, excellent query performance for structured data under 1TB
- **Snowflake**: Scalable data warehouse with separation of compute/storage, native semi-structured data support
- **Pinecone**: Purpose-built vector database with metadata filtering, crucial for semantic search at scale
- **Redis**: Sub-millisecond latency for caching, supports complex data structures

### Processing & Analytics
- **Apache Airflow**: Mature orchestration for data pipelines, extensive monitoring capabilities
- **dbt**: SQL-based transformation framework, version control for data models
- **Python (FastAPI)**: High-performance async framework for API services
- **Apache Spark**: Distributed processing for initial historical load and batch jobs

### AI/ML Stack
- **OpenAI GPT-4**: Primary LLM for complex reasoning and synthesis
- **Claude (Anthropic)**: Fallback LLM and for specific use cases requiring larger context
- **Sentence Transformers**: Open-source embedding generation for cost efficiency
- **scikit-learn**: Lightweight ML for sentiment analysis and classification

### Infrastructure
- **AWS**: Primary cloud provider for reliability and service breadth
- **Kubernetes (EKS)**: Container orchestration for microservices
- **Terraform**: Infrastructure as code for reproducibility
- **Datadog**: Comprehensive monitoring and alerting

### Frontend
- **React + TypeScript**: Type safety and component reusability
- **D3.js**: Flexible, powerful visualization library
- **Socket.io**: WebSocket abstraction for real-time updates

---

## 4. Data Schema Structures

### Core Data Models

**Operational Database (PostgreSQL)**

The tickets table stores core ticket information including:
- Unique identifiers (internal and external)
- Status and priority fields
- Temporal data (created, updated, resolved timestamps)
- JSON fields for flexible tags and custom fields
- Foreign keys for assignee and requester relationships
- Optimized indexes on commonly queried fields

The comments table maintains:
- Comment-to-ticket relationships
- Author tracking
- Comment body and visibility flags
- Derived fields for sentiment scores
- References to vector embeddings

**Analytics Warehouse (Snowflake)**

The fact_tickets table provides:
- Denormalized ticket data for fast aggregation
- Pre-calculated metrics (resolution time, response time)
- Dimensional keys for time-based analysis
- Semi-structured data in VARIANT columns for flexibility

Dimensional tables include:
- Date dimensions with calendar attributes
- User dimensions with role and team information
- Status and priority dimensions with business definitions

**Cache Schema (Redis)**

Query results cached with:
- SHA256 hash as key
- Full result payload
- Metadata including execution time and data sources
- TTL based on query type and data freshness requirements

**Saved Queries (PostgreSQL)**

Persistent storage for:
- Named query templates
- Natural language and structured query representations
- Parameter definitions for dynamic execution
- Scheduling configuration
- Visualization preferences

### API Contracts

**Query Request Structure**
- Natural language query string
- Optional context (time range, filters, conversation history)
- Execution options (visualization preferences, timeout, cache control)

**Query Response Structure**
- Unique query identifier
- Execution status (complete, processing, failed)
- Result payload with answer, data, and optional visualization
- Metadata including execution metrics and confidence scores
- Error details for failed queries

**WebSocket Events**
- Progress updates with percentage completion
- Stage indicators (parsing, querying, processing, visualizing)
- Estimated time remaining for long-running queries

---

## 5. Detailed Technical Explanations

### 5.1 User Experience Flow

When Brenda types "How many urgent tickets did we get last week?" the following sequence occurs:

**Phase 1: Input Processing (50-100ms)**
- WebSocket connection transmits query to API Gateway
- Rate limiting check (10 queries/minute per user)
- Query logged for audit trail

**Phase 2: Intent Recognition (100-200ms)**
- Query Parser uses fine-tuned BERT model to extract intent and parameters
- Intent classified as COUNT_TICKETS with priority and time filters
- Confidence score evaluated against threshold (0.85)

**Phase 3: Query Execution (200-500ms)**
- Query Router checks cache using hash of normalized query
- Cache miss triggers SQL generation based on extracted parameters
- Query executed against PostgreSQL read replica
- Results retrieved and validated

**Phase 4: Response Formation (50-100ms)**
- Numerical result wrapped with natural language template
- Response cached with appropriate TTL
- WebSocket pushes response to client

**Key Technical Challenges:**
- **Latency optimization**: Multi-tier caching, query result precomputation for common patterns
- **Intent ambiguity**: Fallback to clarification prompts when confidence below threshold
- **Connection reliability**: Automatic reconnection with exponential backoff, request deduplication

### 5.2 Historical Data Challenges

Managing millions of tickets while maintaining sub-second response times requires a sophisticated data architecture:

**Tiered Storage Strategy:**
- **Hot Tier** (PostgreSQL): Last 90 days, approximately 500K tickets, optimized indexes for fast access
- **Warm Tier** (Snowflake): 90 days to 2 years, columnar storage with automatic clustering
- **Cold Tier** (S3 Parquet): Beyond 2 years, compressed format accessed via Athena for rare queries

**Query Optimization Techniques:**
- **Materialized Views**: Pre-aggregated daily, weekly, and monthly summaries
- **Partition Pruning**: Data partitioned by creation date for efficient scanning
- **Query Rewriting**: Complex queries automatically simplified when possible
- **Adaptive Execution**: Query planner chooses between real-time and batch based on estimated cost

**Pre-computation Pipeline:**
- Nightly jobs calculate common metrics across dimensions
- Rolling windows maintained for time-series queries
- Incremental updates rather than full recalculations
- Smart invalidation of affected aggregates on data changes

When handling "Show me ticket trends for the past year", the system:
- Retrieves pre-computed monthly aggregates (instant response)
- Avoids scanning millions of raw tickets (would take 30+ seconds)
- Provides drill-down capability into specific periods if needed

### 5.3 Business Data Risks

**Data Security Measures:**
- **Encryption**: AES-256 at rest across all storage systems, TLS 1.3 for all data in transit
- **Access Control**: Row-level security in PostgreSQL, column masking for PII fields
- **Audit Logging**: Comprehensive query logging with user, timestamp, and accessed data
- **Data Classification**: Automatic PII detection and redaction before display

**Operational Safety:**
- **Query Complexity Limits**: Maximum execution time of 30 seconds, result size cap of 100MB
- **Resource Isolation**: Separate compute pools for interactive versus batch queries
- **Circuit Breakers**: Automatic query termination on resource exhaustion
- **Rollback Capability**: All data modifications versioned and reversible

**AI Safety Guardrails:**
- **Prompt Injection Protection**: Input sanitization and prompt structure validation
- **Output Validation**: LLM responses checked for PII and inappropriate content
- **Hallucination Prevention**: Statistical claims verified against actual data
- **Human-in-the-loop**: Critical insights flagged for manual review

**Compliance Considerations:**
- **GDPR**: Customer data deletion workflows with cascade effects, consent tracking
- **SOC 2**: Automated compliance reporting and regular access reviews
- **Data Residency**: Regional data storage options for regulatory requirements

### 5.4 Complex Business Questions

Enabling answers to questions like "Why are customers unhappy with our new feature?" requires sophisticated analysis:

**Multi-Modal Analysis Pipeline:**

1. **Feature Identification**
   - Named Entity Recognition identifies feature mentions in text
   - Fuzzy matching handles variations in naming
   - Tag correlation analysis finds related tickets

2. **Sentiment Analysis**
   - Fine-tuned RoBERTa model trained on support ticket corpus
   - Aspect-based sentiment for feature-specific analysis
   - Confidence scoring with human review for low-confidence results

3. **Theme Extraction**
   - LDA topic modeling on filtered comments
   - Clustering of similar issues using embeddings
   - Trend detection for emerging problems

4. **Synthesis Process**
   - Find relevant tickets through vector search
   - Extract sentiments using batch processing
   - Identify themes from negative feedback
   - Generate insights through LLM synthesis

**Derived Metrics System:**
- **Customer Satisfaction Score**: Weighted sentiment across all interactions
- **Issue Resolution Velocity**: Trending analysis of time-to-resolution
- **Feature Adoption Health**: Combination of volume, sentiment, and resolution rate
- **Problem Clustering**: Automatic grouping of similar issues

### 5.5 Workflow Efficiency

Solving Brenda's repetitive reporting needs:

**Saved Query System:**
- Natural language queries converted to reusable templates
- Parameter extraction for dynamic values (dates, filters)
- Version control for query evolution
- Sharing capabilities for team collaboration

**Query Lifecycle:**
1. **Creation**: User saves query with memorable name
2. **Storage**: Query structure, visualization config, and parameters persisted
3. **Execution**: Named query executed with parameter substitution
4. **Scheduling**: Optional cron-based automation with delivery preferences

**Smart Suggestions:**
- ML model learns from query patterns
- Proactive suggestions based on time and context
- Query completion using historical patterns
- Recommended visualizations based on data characteristics

**Automation Features:**
- Scheduled report generation and distribution
- Alert triggers on threshold breaches
- Batch execution of related queries
- Export to various formats (PDF, Excel, CSV)

### 5.6 Data Visualization Needs

**Server-Side Rendering Pipeline:**
1. Query results formatted for visualization requirements
2. D3.js generates SVG on Node.js server
3. SVG converted to PNG using Puppeteer
4. Image cached in S3 with CDN delivery

**Visualization Intelligence:**
- Automatic chart type selection based on data characteristics
- Smart axis scaling and labeling algorithms
- Responsive design for various screen sizes
- Color scheme optimization for accessibility

**Interactive Options:**
- Static images for immediate chat display
- Interactive HTML5 charts for exploration
- Export functionality to multiple formats
- Drill-down capabilities for detailed analysis

**Supported Visualizations:**
- Time series (line, area charts)
- Comparisons (bar, column charts)
- Distributions (histograms, box plots)
- Relationships (scatter plots, heatmaps)
- Proportions (pie, donut charts)

### 5.7 Operational Cost Management

**Cost Optimization Strategy:**

**Query Classification System:**
- **Tier 1** (Cache/Simple): Under $0.001 per query
  - Direct cache hits
  - Simple aggregations on hot data
- **Tier 2** (Moderate): $0.01-0.05 per query
  - Complex SQL on warm data
  - Small-scale LLM operations
- **Tier 3** (Complex): $0.10-0.50 per query
  - Historical analysis across years
  - Large-scale embedding searches
  - Multiple LLM calls with extensive context

**Cost Control Mechanisms:**

1. **Smart Caching**
   - Query result caching with intelligent TTL
   - Semantic similarity matching for approximate cache hits
   - Predictive pre-caching for common morning queries
   - Shared cache across similar queries

2. **Query Optimization**
   - Automatic query rewriting for efficiency
   - Sampling for approximate answers when acceptable
   - Progressive disclosure (quick estimate followed by full analysis)
   - Batch processing for similar queries

3. **Resource Limits**
   - User-level quotas (queries per day, compute minutes per month)
   - Automatic downgrade to simpler analysis when limits approached
   - Cost visibility in UI with estimates before execution
   - Budget alerts and automatic throttling

4. **Model Selection**
   - GPT-3.5 for simple responses and clarifications
   - GPT-4 only for complex reasoning and synthesis
   - Local models for standard operations (sentiment, classification)
   - Cached embeddings to avoid recomputation

**Cost Monitoring:**
- Real-time cost tracking dashboard
- Daily/monthly budget tracking
- Per-user and per-query-type analytics
- Optimization recommendations based on usage patterns

### 5.8 Technology Evolution

**Future-Proofing Architecture:**

**Abstraction Layers:**
- LLM provider abstraction allowing seamless switching
- Standardized interfaces for all AI operations
- Plugin architecture for new capabilities
- Version-agnostic prompt management

**Version Management:**
- API versioning with backward compatibility guarantees
- Feature flags for gradual rollout of new capabilities
- A/B testing framework for model comparison
- Automated regression testing for changes

**Adaptation Strategies:**

1. **Provider Independence**
   - No hard dependencies on specific AI providers
   - Standardized prompt formats with provider-specific adapters
   - Regular benchmarking of alternative providers
   - Multi-provider support with automatic failover

2. **Capability Detection**
   - Runtime detection of model capabilities
   - Graceful degradation when features unavailable
   - Automatic routing to appropriate models
   - Feature compatibility matrix maintenance

3. **Migration Patterns**
   - Blue-green deployments for model updates
   - Parallel running for result comparison
   - Automated quality assurance for model changes
   - Rollback capabilities with version pinning

4. **Knowledge Preservation**
   - Prompt library with comprehensive versioning
   - Fine-tuning datasets maintained independently
   - Business logic separated from AI implementation
   - Documentation of model-specific optimizations

**Monitoring for Evolution:**
- Performance metrics across model versions
- Cost-effectiveness tracking
- User satisfaction measurements
- Automatic alerts for degradation

---

## Implementation Roadmap

### Phase 1: MVP (Weeks 1-6)
- Basic data ingestion from Zendesk
- Simple SQL query generation
- Text-based responses only
- Core saved query functionality

### Phase 2: Intelligence (Weeks 7-12)
- Sentiment analysis integration
- Complex question handling
- Basic visualizations
- Performance optimizations

### Phase 3: Scale (Weeks 13-18)
- Full historical data processing
- Advanced caching strategies
- Scheduling and automation
- Multi-user support

### Phase 4: Evolution (Ongoing)
- A/B testing framework
- Additional data sources
- Advanced ML features
- Self-learning capabilities

---

## Conclusion

This architecture provides a pragmatic path to delivering value quickly while maintaining flexibility for future growth. By focusing on modular design, intelligent caching, and abstraction layers, we can build a system that meets Brenda's immediate needs while preparing for enterprise-scale deployment.

The key success factors will be:
- Rapid iteration on the query understanding layer
- Careful attention to response latency
- Building trust through accurate, verifiable insights
- Maintaining operational excellence as we scale

This design balances the immediate need for an MVP with the long-term vision of a comprehensive analytics platform, ensuring SupportWise can truly understand and serve its customers better.