package session

import (
	"encoding/base64"
	"log"

	"vcaas-network-gateway/internal/audio"
	"vcaas-network-gateway/internal/bridge"
	"vcaas-network-gateway/internal/telephony"
)

type CallSession struct {
	vcaas *bridge.VCaaSClient
}

// New creates a new CallSession, opening a connection to the VCaaS Python backend.
// Each incoming call should get its own session — Go's scheduler makes per-goroutine
// sessions cheap enough to scale to hundreds of concurrent calls.
func New(backendURL string) (*CallSession, error) {
	client, err := bridge.Connect(backendURL)
	if err != nil {
		return nil, err
	}
	go client.Listen(func(verdict map[string]interface{}) {
		// TODO: replace with real delivery — webhook, dashboard push, message queue
		log.Printf("[session] verdict: %+v\n", verdict)
	})
	return &CallSession{vcaas: client}, nil
}

// HandleMessage processes one incoming WebSocket message from the CPaaS partner.
// It ignores all non-media events (connected, start, stop) and for media events:
//  1. base64-decodes the mu-law payload
//  2. decodes mu-law → 16-bit PCM at 8kHz
//  3. upsamples 8kHz → 16kHz via linear interpolation
//  4. forwards raw PCM bytes to the VCaaS backend
func (s *CallSession) HandleMessage(raw []byte) error {
	msg, err := telephony.ParseMessage(raw)
	if err != nil {
		return err
	}
	if msg.Event != "media" {
		return nil // ignore connected/start/stop events
	}
	mulaw, err := base64.StdEncoding.DecodeString(msg.Media.Payload)
	if err != nil {
		return err
	}
	pcm8k := audio.DecodeMuLawBuffer(mulaw)
	pcm16k := audio.UpsampleLinear2x(pcm8k)
	return s.vcaas.SendAudio(audio.ToPCMBytes(pcm16k))
}

func (s *CallSession) Close() {
	s.vcaas.Close()
}
