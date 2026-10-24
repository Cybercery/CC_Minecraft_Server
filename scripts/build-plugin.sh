#!/usr/bin/env bash
set -e

PLUGIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../minecraft-plugin" && pwd)"
TARGET_DIR="${PLUGIN_DIR}/target"

echo "Building Minecraft verification plugin..."

if command -v mvn &> /dev/null; then
    cd "${PLUGIN_DIR}"
    mvn clean package -DskipTests
    echo "Build successful! Plugin jar is located in ${TARGET_DIR}."
elif command -v docker &> /dev/null; then
    echo "Maven not found locally. Building via Maven Docker container..."
    docker run --rm -v "${PLUGIN_DIR}":/app -w /app maven:3.9.6-eclipse-temurin-21 mvn clean package -DskipTests
    echo "Docker build successful! Plugin jar is located in ${TARGET_DIR}."
else
    echo "Notice: Neither maven nor docker is installed/running on the host system."
    echo "Install Maven or start Docker to compile CloudVerification.jar."
    exit 0
fi
