/* ============================================================
   Shared Whisper loader for Transcribe Audio & Voice → SRT.
   Runs OpenAI's Whisper model fully in the browser via
   transformers.js — audio never leaves the visitor's device.
   The model downloads once and is cached by the browser.
   ============================================================ */
import { pipeline } from 'https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.7.6';

export const MODELS = [
  { id: 'onnx-community/whisper-tiny',  label: 'Fast (~40 MB) — quick drafts' },
  { id: 'onnx-community/whisper-base',  label: 'Balanced (~80 MB) — recommended' },
  { id: 'onnx-community/whisper-small', label: 'Accurate (~250 MB) — best quality' },
];

export const LANGUAGES = [
  ['auto', 'Auto-detect'], ['en', 'English'], ['hi', 'Hindi'], ['bn', 'Bengali'],
  ['ta', 'Tamil'], ['te', 'Telugu'], ['mr', 'Marathi'], ['gu', 'Gujarati'],
  ['kn', 'Kannada'], ['ml', 'Malayalam'], ['pa', 'Punjabi'], ['ur', 'Urdu'],
  ['es', 'Spanish'], ['fr', 'French'], ['de', 'German'], ['pt', 'Portuguese'],
  ['it', 'Italian'], ['nl', 'Dutch'], ['ru', 'Russian'], ['uk', 'Ukrainian'],
  ['pl', 'Polish'], ['tr', 'Turkish'], ['ar', 'Arabic'], ['fa', 'Persian'],
  ['ja', 'Japanese'], ['ko', 'Korean'], ['zh', 'Chinese'], ['th', 'Thai'],
  ['vi', 'Vietnamese'], ['id', 'Indonesian'], ['ms', 'Malay'], ['tl', 'Tagalog'],
];

const cache = new Map();

/** Load (and cache) the ASR pipeline. onProgress receives {status,file,progress}. */
export async function getTranscriber(modelId, onProgress) {
  if (cache.has(modelId)) return cache.get(modelId);

  const common = { progress_callback: onProgress };
  let asr;
  if (navigator.gpu) {
    try {
      asr = await pipeline('automatic-speech-recognition', modelId, {
        ...common, device: 'webgpu',
        dtype: { encoder_model: 'fp32', decoder_model_merged: 'q4' },
      });
    } catch (e) {
      console.warn('WebGPU init failed, falling back to WASM:', e);
    }
  }
  if (!asr) {
    asr = await pipeline('automatic-speech-recognition', modelId, {
      ...common, device: 'wasm', dtype: 'q8',
    });
  }
  cache.set(modelId, asr);
  return asr;
}

/** Transcribe 16 kHz mono Float32 audio. Returns transformers.js output
 *  ({text, chunks?}). language 'auto' lets Whisper detect it. */
export async function transcribe(asr, audio, { language = 'auto', timestamps = false } = {}) {
  const opts = {
    chunk_length_s: 30,
    stride_length_s: 5,
    return_timestamps: timestamps,
    task: 'transcribe',
  };
  if (language && language !== 'auto') opts.language = language;
  return asr(audio, opts);
}

/** Aggregate transformers.js download progress into one 0-100 number. */
export function makeProgressAggregator(onPct) {
  const files = new Map();
  return (p) => {
    if (!p || !p.file) return;
    if (p.status === 'progress') files.set(p.file, { loaded: p.loaded || 0, total: p.total || 0 });
    if (p.status === 'done') {
      const f = files.get(p.file);
      if (f) f.loaded = f.total;
    }
    let loaded = 0, total = 0;
    files.forEach((f) => { loaded += f.loaded; total += f.total; });
    if (total > 0) onPct(Math.min(100, Math.round((loaded / total) * 100)));
  };
}
