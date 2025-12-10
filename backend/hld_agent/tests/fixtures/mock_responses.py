"""Mock responses for testing HLD Agent."""

from hld_agent.schemas.models import ArchOutputState


# Mock LLM responses for different scenarios
MOCK_API_GATEWAY_RESPONSE = ArchOutputState(
    explanation="API Gateway handles routing and authentication after load balancer",
    next="api-gateway",
    current_sequence="user req -> load balancer -> api-gateway",
    reasoning="API Gateway provides centralized routing, authentication, and rate limiting for microservices"
)

MOCK_DATABASE_RESPONSE = ArchOutputState(
    explanation="Database is needed to persist application data",
    next="database",
    current_sequence="user req -> load balancer -> api-gateway -> database",
    reasoning="PostgreSQL database provides ACID transactions for reliable data storage"
)

MOCK_END_RESPONSE = ArchOutputState(
    explanation="Architecture is complete with all necessary components",
    next="__end__",
    current_sequence="user req -> load balancer -> api-gateway -> database -> cache",
    reasoning="System has all core components: load balancing, routing, data persistence, and caching"
)

MOCK_JOB_SCHEDULER_FLOW = [
    ArchOutputState(
        explanation="Job scheduler manages task distribution",
        next="job-scheduler", 
        current_sequence="user req -> load balancer -> job-scheduler",
        reasoning="Job scheduler is the core component for distributed task processing"
    ),
    ArchOutputState(
        explanation="Message queue buffers tasks for processing",
        next="message-queue",
        current_sequence="user req -> load balancer -> job-scheduler -> message-queue", 
        reasoning="Message queue provides reliable task buffering and async processing"
    ),
    ArchOutputState(
        explanation="Worker nodes process the queued tasks",
        next="worker-nodes",
        current_sequence="user req -> load balancer -> job-scheduler -> message-queue -> worker-nodes",
        reasoning="Worker nodes execute the actual job processing in parallel"
    ),
    ArchOutputState(
        explanation="Database stores job results and metadata",
        next="database",
        current_sequence="user req -> load balancer -> job-scheduler -> message-queue -> worker-nodes -> database",
        reasoning="Database persists job state, results, and scheduling metadata"
    ),
    ArchOutputState(
        explanation="System architecture is complete",
        next="__end__",
        current_sequence="user req -> load balancer -> job-scheduler -> message-queue -> worker-nodes -> database",
        reasoning="All components for a complete job scheduler system are present"
    )
]

MOCK_ERROR_RESPONSE = Exception("Mocked LLM API error")

# Mock configuration for testing
MOCK_CONFIG_YAML = """
llm:
  provider: "groq"
  models:
    primary: "gemma2-9b-it"
    fallback: "deepseek-r1-distill-llama-70b"
  temperature: 0
  max_iterations: 3
  
api_keys:
  groq_api_key: "${GROQ_API_KEY}"
  langsmith_api_key: "${LANGSMITH_API_KEY}"
  
langsmith:
  tracing: false
  project: "test-hld-agent"
  
logging:
  level: "DEBUG"
  format: "text"
  
graph:
  recursion_limit: 10
  memory_enabled: true
"""