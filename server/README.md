# Server Deployment

Deploy the LEGO Factory Chatbot on your remote server at `195.231.61.196`.

## Quick Start

### 1. Create Environment File

```bash
cd server/
cp .env.server.template .env.server
nano .env.server  # Edit with your actual API keys
```

### 2. Build and Run

```bash
cd server/
docker-compose -f docker-compose.server.yml up -d --build
```

### 3. Access the Chatbot

Open in browser: `http://195.231.61.196:7860`

## Commands

```bash
# Check status
docker-compose -f docker-compose.server.yml ps

# View logs
docker-compose -f docker-compose.server.yml logs -f chatbot

# Stop services
docker-compose -f docker-compose.server.yml down

# Restart chatbot only
docker-compose -f docker-compose.server.yml restart chatbot

# Rebuild after code changes
docker-compose -f docker-compose.server.yml up -d --build chatbot
```

## Files

| File | Purpose |
|------|---------|
| `docker-compose.server.yml` | Server deployment config |
| `Dockerfile.chatbot` | Chatbot container build |
| `.env.server.template` | Template for credentials |
| `.env.server` | Your credentials (**gitignored**) |
