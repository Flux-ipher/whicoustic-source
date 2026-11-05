package audio

import "testing"

func TestMuLawSilence(t *testing.T) {
	// mu-law 0xFF encodes silence (linear 0) — critical sanity check
	if s := DecodeMuLaw(0xFF); s != 0 {
		t.Errorf("expected 0, got %d", s)
	}
}

func TestUpsampleLength(t *testing.T) {
	in := []int16{100, 200, 300}
	out := UpsampleLinear2x(in)
	if len(out) != len(in)*2 {
		t.Errorf("expected %d samples, got %d", len(in)*2, len(out))
	}
}

func TestUpsampleInterpolation(t *testing.T) {
	in := []int16{100, 200}
	out := UpsampleLinear2x(in)
	// out should be [100, 150, 200, 200]
	if out[0] != 100 {
		t.Errorf("out[0]: expected 100, got %d", out[0])
	}
	if out[1] != 150 {
		t.Errorf("out[1]: expected 150 (midpoint), got %d", out[1])
	}
}

func TestToPCMBytesLength(t *testing.T) {
	samples := []int16{0, 100, -100, 32767}
	b := ToPCMBytes(samples)
	if len(b) != len(samples)*2 {
		t.Errorf("expected %d bytes, got %d", len(samples)*2, len(b))
	}
}

func TestToPCMBytesLittleEndian(t *testing.T) {
	// 0x0100 = 256 → little-endian bytes: [0x00, 0x01]
	b := ToPCMBytes([]int16{256})
	if b[0] != 0x00 || b[1] != 0x01 {
		t.Errorf("expected [0x00, 0x01], got [0x%02x, 0x%02x]", b[0], b[1])
	}
}

func TestDecodeMuLawBuffer(t *testing.T) {
	data := []byte{0xFF, 0x7F} // silence + another byte
	out := DecodeMuLawBuffer(data)
	if len(out) != 2 {
		t.Errorf("expected 2 samples, got %d", len(out))
	}
	if out[0] != 0 {
		t.Errorf("first sample should be silence (0), got %d", out[0])
	}
}
