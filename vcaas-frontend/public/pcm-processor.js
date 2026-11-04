/**
 * AudioWorkletProcessor that downsamples input audio to 16 kHz 16-bit PCM (Int16Array)
 * and streams arraybuffers to the main thread for real-time WebSocket transport.
 */
class PCMProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.targetSampleRate = 16000;
    this.bufferSize = 2048; // ~128ms chunks at 16kHz
    this.pcmBuffer = new Int16Array(this.bufferSize);
    this.pcmIndex = 0;
  }

  process(inputs) {
    const input = inputs[0];
    if (!input || !input[0]) return true;

    const inputData = input[0]; // Float32Array mono
    const inputSampleRate = sampleRate; // Global AudioWorklet sampleRate

    if (inputSampleRate === this.targetSampleRate) {
      for (let i = 0; i < inputData.length; i++) {
        const s = Math.max(-1, Math.min(1, inputData[i]));
        this.pcmBuffer[this.pcmIndex++] = s < 0 ? s * 0x8000 : s * 0x7fff;

        if (this.pcmIndex >= this.bufferSize) {
          const chunk = this.pcmBuffer.slice().buffer;
          this.port.postMessage(chunk, [chunk]);
          this.pcmIndex = 0;
        }
      }
    } else {
      // Linear resampling to 16kHz
      const ratio = inputSampleRate / this.targetSampleRate;
      let pos = 0;
      while (pos < inputData.length) {
        const index = Math.floor(pos);
        const nextIndex = Math.min(index + 1, inputData.length - 1);
        const weight = pos - index;
        const val = inputData[index] * (1 - weight) + inputData[nextIndex] * weight;
        const s = Math.max(-1, Math.min(1, val));
        this.pcmBuffer[this.pcmIndex++] = s < 0 ? s * 0x8000 : s * 0x7fff;

        if (this.pcmIndex >= this.bufferSize) {
          const chunk = this.pcmBuffer.slice().buffer;
          this.port.postMessage(chunk, [chunk]);
          this.pcmIndex = 0;
        }

        pos += ratio;
      }
    }

    return true;
  }
}

registerProcessor('pcm-processor', PCMProcessor);
