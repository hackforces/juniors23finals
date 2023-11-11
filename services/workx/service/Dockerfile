# Use an official Golang runtime as a parent image
FROM golang:latest as builder

RUN apt update && apt install libz-dev -y
# Set the working directory inside the container
WORKDIR /app

# Copy go.mod and go.sum if they exist
COPY src/go.mod src/go.sum ./

# Download dependencies
# This layer is cached if the go.mod and go.sum files are unchanged
RUN go mod download

# Copy the source code
COPY src/. .

# Build the binary
# -o specifies the output file
# You can add other build flags if needed
RUN CGO_ENABLED=1 GOOS=linux go build -a -installsuffix cgo -o /workx3 .

WORKDIR /companion

COPY src_companion_app/. .
RUN bash build.sh