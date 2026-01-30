# Server Deployment

Deploy the LEGO Factory Chatbot on a remote server.

## Prerequisites

1. **Docker** and **docker-compose** installed on the server
2. **UPPAAL Engine image** built (run `./setup_submodules.sh` from project root, or see manual steps below)
3. **API keys** for Gemini (or other LLM providers)

## Quick Start

### 1. Create Environment File

```bash
cd server/
cp .env.server.template .env.server
nano .env.server  # Edit with your actual API keys
```

### 2. Build UPPAAL Image (if not already done)

The easiest way is to run from the project root:
```bash
./setup_submodules.sh
```

Or manually:
```bash
# Download UPPAAL 5.0.0 for Linux (if not present)
cd src/
wget https://download.uppaal.org/uppaal-5.0/uppaal-5.0.0/uppaal-5.0.0-linux64.zip
unzip uppaal-5.0.0-linux64.zip
mv uppaal-5.0.0-linux64 uppaal

# Build Docker image with your license key
cd uppaal
docker build --build-arg KEY=YOUR_UPPAAL_LICENSE_KEY --tag uppaal-engine -f res/Dockerfile .
```

### 3. Build and Run All Services

```bash
cd server/
docker-compose -f docker-compose.server.yml up -d --build
```

### 4. Access the Chatbot

Open in browser: `http://YOUR_SERVER_IP:7860`

## Services

| Service | Port | Description |
|---------|------|-------------|
| `lego-chatbot` | 7860 | Main chatbot interface |
| `uppaal-engine` | 2350 (internal) | Formal verification engine |
| `extractor-service` | 6662 (internal) | Digital twin extractor |

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

## UPPAAL Setup

UPPAAL requires a license key from [uppaal.veriaal.dk](https://uppaal.veriaal.dk).

The UPPAAL installation should be placed in `src/uppaal/` with this structure:
```
src/uppaal/
├── bin/
│   ├── verifyta
│   ├── verifyta.sh
│   ├── server.sh
│   └── socketserver.sh
├── res/
│   └── Dockerfile
└── ...
```

## Files

| File | Purpose |
|------|---------|
| `docker-compose.server.yml` | Server deployment config |
| `Dockerfile.chatbot` | Chatbot container build |
| `.env.server.template` | Template for credentials |
| `.env.server` | Your credentials (**gitignored**) |
| `requirements.server.txt` | Lightweight API-only dependencies |
