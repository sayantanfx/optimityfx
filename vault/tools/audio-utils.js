/* ============================================================
   Shared audio helpers for the Vault tools.
   Everything runs locally in the browser — no uploads.
   ============================================================ */

/** Decode any audio file the browser supports into an AudioBuffer.
 *  Optionally resample to targetRate and/or mix down to mono. */
export async function decodeAudioFile(file, { targetRate = null, mono = false } = {}) {
  const arrayBuf = await file.arrayBuffer();
  const AC = window.AudioContext || window.webkitAudioContext;
  const ac = new AC();
  let decoded;
  try {
    decoded = await ac.decodeAudioData(arrayBuf);
  } finally {
    ac.close();
  }
  if (!targetRate && !mono) return decoded;

  const rate = targetRate || decoded.sampleRate;
  const channels = mono ? 1 : decoded.numberOfChannels;
  const length = Math.ceil(decoded.duration * rate);
  const off = new OfflineAudioContext(channels, length, rate);
  const src = off.createBufferSource();
  src.buffer = decoded;
  src.connect(off.destination);
  src.start(0);
  return off.startRendering();
}

/** 16 kHz mono Float32Array — the input format Whisper expects. */
export async function fileToWhisperInput(file) {
  const buf = await decodeAudioFile(file, { targetRate: 16000, mono: true });
  return buf.getChannelData(0);
}

/** Encode an AudioBuffer as a 16-bit PCM WAV Blob. */
export function audioBufferToWav(buffer) {
  const numCh = buffer.numberOfChannels;
  const rate = buffer.sampleRate;
  const frames = buffer.length;
  const bytesPerSample = 2;
  const blockAlign = numCh * bytesPerSample;
  const dataSize = frames * blockAlign;
  const out = new DataView(new ArrayBuffer(44 + dataSize));

  const writeStr = (off, s) => { for (let i = 0; i < s.length; i++) out.setUint8(off + i, s.charCodeAt(i)); };
  writeStr(0, 'RIFF');
  out.setUint32(4, 36 + dataSize, true);
  writeStr(8, 'WAVE');
  writeStr(12, 'fmt ');
  out.setUint32(16, 16, true);
  out.setUint16(20, 1, true);            // PCM
  out.setUint16(22, numCh, true);
  out.setUint32(24, rate, true);
  out.setUint32(28, rate * blockAlign, true);
  out.setUint16(32, blockAlign, true);
  out.setUint16(34, 16, true);
  writeStr(36, 'data');
  out.setUint32(40, dataSize, true);

  const chans = [];
  for (let c = 0; c < numCh; c++) chans.push(buffer.getChannelData(c));
  let off = 44;
  for (let i = 0; i < frames; i++) {
    for (let c = 0; c < numCh; c++) {
      const s = Math.max(-1, Math.min(1, chans[c][i]));
      out.setInt16(off, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
      off += 2;
    }
  }
  return new Blob([out.buffer], { type: 'audio/wav' });
}

/** Trigger a browser download for a Blob. */
export function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 4000);
}

export function stripExt(name) {
  return name.replace(/\.[^.]+$/, '');
}

export function fmtBytes(n) {
  if (n > 1e6) return (n / 1e6).toFixed(1) + ' MB';
  if (n > 1e3) return (n / 1e3).toFixed(0) + ' KB';
  return n + ' B';
}

export function fmtDuration(sec) {
  const m = Math.floor(sec / 60), s = Math.round(sec % 60);
  return `${m}:${String(s).padStart(2, '0')}`;
}
