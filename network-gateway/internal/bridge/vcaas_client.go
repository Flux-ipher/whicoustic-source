package bridge

import (
	"encoding/json"
	"log"

	"github.com/gorilla/websocket"
)

type VCaaSClient struct {
	conn *websocket.Conn
}

// Connect opens a WebSocket connection to the Python detection backend.
// url example: "ws://localhost:8000/api/v1/verify/stream"
func Connect(url string) (*VCaaSClient, error) {
	conn, _, err := websocket.DefaultDialer.Dial(url, nil)
	if err != nil {
		return nil, err
	}
	return &VCaaSClient{conn: conn}, nil
}

// SendAudio forwards a raw PCM byte slice as a binary WebSocket frame.
func (c *VCaaSClient) SendAudio(pcm []byte) error {
	return c.conn.WriteMessage(websocket.BinaryMessage, pcm)
}

// Listen reads verdict JSON from the backend and calls onVerdict for each.
// Runs until the connection closes — call in a goroutine.
func (c *VCaaSClient) Listen(onVerdict func(verdict map[string]interface{})) {
	for {
		_, data, err := c.conn.ReadMessage()
		if err != nil {
			log.Println("[bridge] backend connection closed:", err)
			return
		}
		var v map[string]interface{}
		if json.Unmarshal(data, &v) == nil {
			onVerdict(v)
		}
	}
}

func (c *VCaaSClient) Close() {
	_ = c.conn.Close()
}
