/**
 * AudioWorkletProcessor that downsamples input audio to 16 kHz 16-bit PCM (Int16Array)
 * and streams ArrayBuffers to the main thread for real-time WebSocket transport.
 * Maintains phase and boundary sample interpolation across 128-sample blocks to prevent clicking.
 */
class PCMProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.targetSampleRate = 16000;
    this.bufferSize = 2048; // ~128ms chunks at 16kHz
    this.pcmBuffer = new Int16Array(this.bufferSize);
    this.pcmIndex = 0;
    this.phase = 0;
    this.lastSample = 0;
  }

  process(inputs) {
    const input = inputs[0];
    if (!input || !input[0] || input[0].length === 0) return true;

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
      this.lastSample = inputData[inputData.length - 1];
    } else {
      // Linear resampling with inter-block phase persistence
      const ratio = inputSampleRate / this.targetSampleRate;
      let pos = this.phase;

      while (pos < inputData.length) {
        let val;
        if (pos < 0) {
          const weight = pos + 1;
          val = this.lastSample * (1 - weight) + inputData[0] * weight;
        } else {
          const index = Math.floor(pos);
          const nextIndex = index + 1;
          const weight = pos - index;
          const s0 = inputData[index];
          const s1 = nextIndex < inputData.length ? inputData[nextIndex] : inputData[index];
          val = s0 * (1 - weight) + s1 * weight;
        }

        const s = Math.max(-1, Math.min(1, val));
        this.pcmBuffer[this.pcmIndex++] = s < 0 ? s * 0x8000 : s * 0x7fff;

        if (this.pcmIndex >= this.bufferSize) {
          const chunk = this.pcmBuffer.slice().buffer;
          this.port.postMessage(chunk, [chunk]);
          this.pcmIndex = 0;
        }

        pos += ratio;
      }

      this.phase = pos - inputData.length;
      this.lastSample = inputData[inputData.length - 1];
    }

    return true;
  }
}

registerProcessor('pcm-processor', PCMProcessor);
