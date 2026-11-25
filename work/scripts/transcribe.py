import json, sys
from faster_whisper import WhisperModel
m = WhisperModel('large-v3', device='cpu', compute_type='int8', cpu_threads=4)
import wave, numpy as np
wf=wave.open(sys.argv[1]); audio=np.frombuffer(wf.readframes(wf.getnframes()),dtype=np.int16).astype(np.float32)/32768.0
segs, info = m.transcribe(audio, language='es', word_timestamps=True, beam_size=5,
    condition_on_previous_text=False, vad_filter=False,
    initial_prompt="Son las 2 de la mañana, otra vez te cortaron la luz. Planes de respaldo eléctrico: USD 1.500, 3.100, 5.150. kWh, BTU, aire acondicionado, nevera, router, Elite 6000.")
out = []
for s in segs:
    w = [dict(w=x.word, s=round(x.start,3), e=round(x.end,3), p=round(x.probability,3)) for x in s.words]
    out.append(dict(s=round(s.start,3), e=round(s.end,3), t=s.text, words=w))
    print(f"[{s.start:7.2f}-{s.end:7.2f}] {s.text}", flush=True)
json.dump(out, open(sys.argv[2],'w'), ensure_ascii=False, indent=1)
