# Multi-Platform Messaging Integrations

TruthGPT OpenClaw includes webhook proxy adapters (`agents/framework/messaging/`), allowing agents and swarms to interact directly with users across major chat platforms.

---

## 📱 Platform Configuration & Webhook Endpoints

Launch the OpenClaw webhook server:
```bash
openclaw serve --port 8080
```

Configure webhooks to point to `https://your-domain.com/webhooks/{platform}`:

| Messaging Platform | Required Environment Variables | Webhook Endpoint | Setup Notes |
| :--- | :--- | :--- | :--- |
| **Telegram** | `TELEGRAM_BOT_TOKEN` | `/webhooks/telegram` | Created via **@BotFather**. Register webhook via `POST /webhooks/telegram/setup`. |
| **WhatsApp (Twilio)**| `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_FROM` | `/webhooks/whatsapp` | Configure WhatsApp Sandbox endpoint in Twilio Console. |
| **Discord** | `DISCORD_BOT_TOKEN`, `DISCORD_APP_ID`, `DISCORD_PUBLIC_KEY` | `/webhooks/discord` | Configure Interactions Endpoint in Discord Developer Portal. |
| **Slack** | `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET` | `/webhooks/slack` | Subscribe to `message.channels` and `app_mention` events. |
| **Signal** | `SIGNAL_CLI_API_URL`, `SIGNAL_SENDER_NUMBER` | `/webhooks/signal` | Interfaces via `signal-cli-rest-api` Docker bridge. |
| **MS Teams** | `TEAMS_APP_ID`, `TEAMS_APP_PASSWORD` | `/webhooks/teams` | Azure Bot Service endpoint configuration. |

---

## 🛠️ Direct Python Usage (Headless Integration)

You can invoke platform adapters directly in Python scripts without running the full REST server:

```python
from agents.framework.messaging.telegram_adapter import TelegramAdapter

adapter = TelegramAdapter(token="YOUR_TELEGRAM_BOT_TOKEN")

# Process an incoming raw message dictionary
response = await adapter.process_update({
    "message": {
        "chat": {"id": 123456789},
        "from": {"id": 123456789, "first_name": "Dev"},
        "text": "Run an analysis on our latest training loss curve."
    }
})
```
