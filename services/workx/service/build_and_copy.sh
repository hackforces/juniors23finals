#!/bin/bash

# Define a name for the Docker image
IMAGE_NAME="workworkwork-builder"

# Define a name for the Docker container
CONTAINER_NAME="workworkwork-extract"

# Define the directory on the host to copy the binary to
OUTPUT_DIR="./deploy"

# Build the Docker image
docker build -t "$IMAGE_NAME" .

# Remove any existing container with the same name
docker rm -f "$CONTAINER_NAME" 2>/dev/null || true

# Create a new container without starting it
docker create --name "$CONTAINER_NAME" "$IMAGE_NAME"

# Make sure the output directory exists
mkdir -p "$OUTPUT_DIR"

rm deploy/companion_app
rm deploy/workx3

# Copy the binary from the created container to the host
docker cp "$CONTAINER_NAME:/workx3" "$OUTPUT_DIR"
docker cp "$CONTAINER_NAME:/companion_app" "$OUTPUT_DIR"

chmod 777 deploy/workx3 deploy/companion_app

# Remove the container now that we're done
docker rm -f "$CONTAINER_NAME"

echo "Golang binary copied to: $OUTPUT_DIR/workx3"
echo "Companion binary copied to: $OUTPUT_DIR/companion_app"
