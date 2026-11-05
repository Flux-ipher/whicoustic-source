package telephony

import "encoding/json"

// TwilioMessage models Twilio's Media Stream WebSocket frame format.
// Adapt field names for Exotel/Ozonetel when connecting to Indian CPaaS partners.
type TwilioMessage struct {
	Event string `json:"event"` // "connected" | "start" | "media" | "stop"
	Media struct {
		Payload string `json:"payload"` // base64-encoded mu-law audio
	} `json:"media"`
	Start struct {
		CallSid    string `json:"callSid"`
		AccountSid string `json:"accountSid"`
	} `json:"start"`
}

func ParseMessage(raw []byte) (*TwilioMessage, error) {
	var msg TwilioMessage
	if err := json.Unmarshal(raw, &msg); err != nil {
		return nil, err
	}
	return &msg, nil
}
