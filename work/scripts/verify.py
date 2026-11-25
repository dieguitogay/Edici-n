import wave, numpy as np, sys
from faster_whisper import WhisperModel
wf=wave.open('audio16k.wav'); a=np.frombuffer(wf.readframes(wf.getnframes()),dtype=np.int16).astype(np.float32)/32768
m=WhisperModel('large-v3',device='cpu',compute_type='int8',cpu_threads=4)
wins=[(23.8,30.4),(38.9,43.6),(43.6,48.0),(47.8,52.8),(52.9,56.3),(56.5,60.4),(60.9,64.6),(68.3,71.7),(74.3,78.7),(78.4,82.4),(82.5,87.2),(87.3,93.0),(97.2,103.7)]
for s,e in wins:
    seg=a[int(s*16000):int(e*16000)]
    for temp_prompt in [None]:
        r,_=m.transcribe(seg,language='es',vad_filter=False,condition_on_previous_text=False,beam_size=5,temperature=0,initial_prompt=temp_prompt)
        print(f'[{s}-{e}]',''.join(x.text for x in r))
