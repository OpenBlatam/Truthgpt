# Autonomous Agent Task Scheduler

The TruthGPT Agent Scheduler (`agents/orchestration/scheduler/`) provides enterprise cron, interval, and delayed task automation for autonomous agents, backed by a persistent SQLite storage layer.

---

## ⏰ Scheduler Capabilities

- **Cron Expressions**: Schedule tasks at specific times (e.g. `0 9 * * 1-5` for 9:00 AM weekdays).
- **Interval Triggers**: Periodic execution every $N$ seconds.
- **Persistent State**: Scheduled tasks, failure counts, and last execution results survive server restarts in `agent_core_memory.db`.
- **Automatic Retry & Circuit Breaking**: Retries failed agent invocations with exponential backoff.

---

## 🛠️ Python Scheduler Example

```python
import asyncio
from agents.framework.client import AgentClient
from agents.orchestration.scheduler.scheduler_api import AgentScheduler

async def main():
    client = AgentClient(use_swarm=True)
    scheduler = AgentScheduler(agent_client=client)

    # 1. Schedule a recurring market & research report every 2 hours
    scheduler.add_recurring(
        task_id="market_intel_report",
        user_id="executive_1",
        prompt="Synthesize the top AI breakthroughs published in the last 24h and notify the team.",
        interval_seconds=7200
    )

    # 2. Schedule a daily 8:00 AM diagnostic job
    scheduler.add_cron(
        task_id="daily_health_audit",
        user_id="devops_admin",
        prompt="Check cluster GPU health, VRAM allocations, and disk capacity.",
        cron_expression="0 8 * * *"
    )

    # 3. Start the background scheduler loop
    await scheduler.start()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 📡 REST Endpoints for Scheduling

| Endpoint | Method | Action |
| :--- | :--- | :--- |
| `/v1/scheduler/tasks` | `GET` | List all active scheduled jobs and execution stats |
| `/v1/scheduler/tasks` | `POST` | Create a new scheduled recurring or cron task |
| `/v1/scheduler/tasks/{id}` | `DELETE` | Cancel and remove a scheduled task |
| `/v1/scheduler/start` | `POST` | Start the scheduler background runner |
| `/v1/scheduler/stop` | `POST` | Pause the scheduler background runner |
