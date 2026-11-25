"""Transcribe el audio final y lo compara con el guion conservado."""
import json, re, wave, difflib, numpy as np
from faster_whisper import WhisperModel
w = wave.open('/home/user/Edici-n/work/final16k.wav')
a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
m = WhisperModel('large-v3', device='cpu', compute_type='int8', cpu_threads=4)
segs, _ = m.transcribe(a, language='es', word_timestamps=True, vad_filter=False, condition_on_previous_text=False, beam_size=5)
words = [x for s in segs for x in s.words]
norm = lambda t: re.sub(r'[^a-z0-9ñáéíóúü]', '', t.lower())
got = [norm(x.word) for x in words if norm(x.word)]
edl = json.load(open('/home/user/Edici-n/edit/src/edl.json'))
ref = [norm(t) for c in edl['cues'] for t in c['text'].replace('*', '').split() if norm(t)]
sm = difflib.SequenceMatcher(a=ref, b=got, autojunk=False)
print('similitud', round(sm.ratio(), 3), 'ref', len(ref), 'asr', len(got))
for op, i1, i2, j1, j2 in sm.get_opcodes():
    if op != 'equal':
        print(op, ref[i1:i2], '->', got[j1:j2])
json.dump([dict(w=x.word, s=x.start, e=x.end) for x in words], open('/home/user/Edici-n/work/final_words.json', 'w'), ensure_ascii=False)
