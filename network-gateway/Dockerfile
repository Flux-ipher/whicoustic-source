# Stage 1: build
FROM golang:1.27-alpine AS build
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN go build -o gateway ./cmd/gateway

# Stage 2: minimal runtime image
FROM alpine:latest
RUN apk add --no-cache ca-certificates
COPY --from=build /app/gateway /gateway
EXPOSE 8080
CMD ["/gateway"]
