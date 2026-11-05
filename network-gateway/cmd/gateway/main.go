package main

import (
	"log"
	"net/http"
	"os"

	"github.com/gorilla/websocket"
	"vcaas-network-gateway/internal/session"
)

var upgrader = websocket.Upgrader{
	// Restrict origin in production — open only for local development.
	// TODO: replace with an allowlist of your CPaaS partner's IPs/origins before going live.
	CheckOrigin: func(r *http.Request) bool { return true },
}

func main() {
	backendURL := os.Getenv("VCAAS_BACKEND_WS_URL")
	if backendURL == "" {
		backendURL = "ws://localhost:8000/api/v1/verify/stream"
	}

	// /media-stream — CPaaS partner connects here per call via WebSocket
	http.HandleFunc("/media-stream", func(w http.ResponseWriter, r *http.Request) {
		conn, err := upgrader.Upgrade(w, r, nil)
		if err != nil {
			log.Println("[gateway] upgrade failed:", err)
			return
		}
		defer conn.Close()

		sess, err := session.New(backendURL)
		if err != nil {
			log.Println("[gateway] could not connect to backend:", err)
			return
		}
		defer sess.Close()

		for {
			_, raw, err := conn.ReadMessage()
			if err != nil {
				log.Println("[gateway] partner disconnected:", err)
				return
			}
			if err := sess.HandleMessage(raw); err != nil {
				log.Println("[gateway] message error:", err)
			}
		}
	})

	// /incoming-call — plain HTTP webhook; returns TwiML that instructs the CPaaS
	// partner to open a media stream back to this service.
	http.HandleFunc("/incoming-call", func(w http.ResponseWriter, r *http.Request) {
		host := r.Host
		w.Header().Set("Content-Type", "text/xml")
		w.Write([]byte(`<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Connect>
    <Stream url="wss://` + host + `/media-stream" />
  </Connect>
</Response>`))
	})

	// /health — simple liveness probe for Docker/load-balancer health checks
	http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"status":"ok"}`))
	})

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	log.Printf("[gateway] listening on :%s\n", port)
	log.Fatal(http.ListenAndServe(":"+port, nil))
}
