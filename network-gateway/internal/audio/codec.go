package audio

// DecodeMuLaw converts a single G.711 mu-law byte to a 16-bit linear PCM sample.
// This is the standard ITU-T G.711 algorithm — not an approximation.
func DecodeMuLaw(b byte) int16 {
	b = ^b
	sign := b & 0x80
	exp := (b >> 4) & 0x07
	mantissa := b & 0x0F

	sample := int16(mantissa)<<3 + 0x84
	sample <<= exp
	sample -= 0x84

	if sign != 0 {
		return -sample
	}
	return sample
}

// DecodeMuLawBuffer decodes a full mu-law byte slice to int16 PCM samples.
func DecodeMuLawBuffer(data []byte) []int16 {
	out := make([]int16, len(data))
	for i, b := range data {
		out[i] = DecodeMuLaw(b)
	}
	return out
}

// UpsampleLinear2x doubles the sample count via linear interpolation.
// Correct for 8kHz → 16kHz (exact 2× ratio).
func UpsampleLinear2x(in []int16) []int16 {
	if len(in) == 0 {
		return in
	}
	out := make([]int16, 0, len(in)*2)
	for i := 0; i < len(in)-1; i++ {
		out = append(out, in[i])
		out = append(out, int16((int32(in[i])+int32(in[i+1]))/2))
	}
	out = append(out, in[len(in)-1], in[len(in)-1])
	return out
}

// ToPCMBytes converts int16 samples to little-endian bytes.
// Matches what np.frombuffer(..., dtype=np.int16) expects in Python.
func ToPCMBytes(samples []int16) []byte {
	out := make([]byte, len(samples)*2)
	for i, s := range samples {
		out[i*2] = byte(s)
		out[i*2+1] = byte(s >> 8)
	}
	return out
}
