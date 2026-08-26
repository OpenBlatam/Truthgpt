# Multi-Channel Messaging Integrations

The **OpenClaw Messaging Subsystem** (`agents/messaging/`) connects autonomous agents directly to team chat platforms via production-ready webhook adapters.

---

## 🌐 Supported Platforms

| Platform | Adapter Location | Required Environment Variables | Setup Details |
| :--- | :--- | :--- | :--- |
| **Telegram** | `agents/messaging/telegram.py` | `TELEGRAM_BOT_TOKEN` | Create bot via **@BotFather**. Webhook points to `/webhooks/telegram`. |
| **WhatsApp** | `agents/messaging/whatsapp.py` | `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_FROM` | Twilio Sandbox webhook points to `/webhooks/whatsapp`. |
| **Discord** | `agents/messaging/discord.py` | `DISCORD_BOT_TOKEN`, `DISCORD_APP_ID` | Discord Developer Portal Interactions URL points to `/webhooks/discord`. |
| **Slack** | `agents/messaging/slack.py` | `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET` | Slack API Dashboard Events Subscription points to `/webhooks/slack`. |
| **Microsoft Teams** | `agents/messaging/teams.py` | `TEAMS_APP_ID`, `TEAMS_APP_PASSWORD` | Azure Bot Service Messaging Endpoint points to `/webhooks/teams`. |
| **Signal** | `agents/messaging/signal.py` | `SIGNAL_CLI_API_URL`, `SIGNAL_SENDER_NUMBER` | `signal-cli-rest-api` container forwarding to `/webhooks/signal`. |

---

## 🚀 Running the Webhook Gateway

Start the OpenClaw multi-channel webhook gateway:

```bash
# Launch webhook server on port 8000
openclaw serve --webhooks --port 8000
```

### Headless In-Code Execution

You can also instantiate adapters directly without launching the HTTP server:

```python
from agents.messaging.telegram import TelegramAdapter

adapter = TelegramAdapter(token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
await adapter.send_message(chat_id="987654321", text="Training job step 5000 complete!")
```
