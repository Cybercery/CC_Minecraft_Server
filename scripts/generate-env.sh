#!/bin/bash
if [ -f .env ]; then
    echo ".env already exists. Aborting."
    exit 1
fi

echo "Generating .env from .env.example..."
cp .env.example .env

# Generate random secrets
if command -v openssl &> /dev/null; then
    RAND_RCON=$(openssl rand -base64 12)
    RAND_API=$(openssl rand -base64 24)
    RAND_HMAC=$(openssl rand -base64 32)
else
    RAND_RCON="RconSecret$(date +%s)"
    RAND_API="ApiSecret$(date +%s)"
    RAND_HMAC="HmacSecret$(date +%s)"
fi

sed -i "s/^RCON_PASSWORD=.*/RCON_PASSWORD=$RAND_RCON/" .env
sed -i "s/^PLUGIN_API_KEY=.*/PLUGIN_API_KEY=$RAND_API/" .env
sed -i "s/^CODE_HMAC_SECRET=.*/CODE_HMAC_SECRET=$RAND_HMAC/" .env

# Try to find docker GID
DOCKER_GID=$(stat -c %g /var/run/docker.sock 2>/dev/null)
if [ -z "$DOCKER_GID" ] && command -v getent &> /dev/null; then
    DOCKER_GID=$(getent group docker | cut -d: -f3)
fi
if [ -n "$DOCKER_GID" ]; then
    sed -i "s/^DOCKER_GID=.*/DOCKER_GID=$DOCKER_GID/" .env
    echo "Set DOCKER_GID to $DOCKER_GID"
else
    echo "Warning: Could not detect docker GID automatically. Please set DOCKER_GID in .env manually."
fi

echo ".env created successfully."
