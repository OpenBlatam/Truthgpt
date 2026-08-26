# Scheduled Tasks & Distributed Tracing

The **OpenClaw Orchestration Subsystem** includes a high-precision cron task scheduler (`AgentScheduler`) and distributed OpenTelemetry-compatible tracing (`global_tracer`).

---

## ⏰ Recurring Agent Scheduler (`AgentScheduler`)

Schedule agents to execute tasks periodically (e.g. hourly metric summaries, daily dataset scrapes):

```python
import asyncio
from openclaw import AgentClient
from optimization_core.agents.orchestration.scheduler import AgentScheduler

async def main():
    client = AgentClient(use_swarm=True)
    scheduler = AgentScheduler(client)
    
    # 1. Add recurring task (every 3600 seconds = 1 hour)
    scheduler.add_recurring(
        task_id="daily_gpu_report",
        user_id="ops_admin",
        prompt="Check cluster GPU status and post an anomaly summary to Slack.",
        interval_seconds=3600
    )
    
    # 2. Start scheduler background loop
    await scheduler.start()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🔭 Distributed Tracing & Observability

OpenClaw includes an integrated span tracer for debugging deeply nested multi-agent handoffs and tool calls:

```python
from agents.observability import global_tracer

# 1. Start root trace span
trace_id = global_tracer.start_trace("user_query_workflow", agent_name="SwarmRouter")

# 2. Start child span for tool execution
span = global_tracer.start_span(trace_id, "python_eval", kind="tool_call")
try:
    # ... execute tool ...
    span.finish(output={"status": "success", "result": 42})
except Exception as e:
    span.record_error(str(e))
```

### Trace Inspection REST Endpoints

| Endpoint | Description |
| :--- | :--- |
| `GET /v1/traces/stats` | Summary of active traces, latency percentiles (p50, p95, p99). |
| `GET /v1/traces/recent` | List the most recent 100 trace sessions. |
| `GET /v1/traces/{trace_id}` | Detailed waterfall visualization tree for a specific trace. |
