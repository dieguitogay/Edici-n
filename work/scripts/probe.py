import wave, numpy as np, sys, json
from faster_whisper import WhisperModel
wf=wave.open('audio16k.wav'); a=np.frombuffer(wf.readframes(wf.getnframes()),dtype=np.int16).astype(np.float32)/32768
m=WhisperModel('large-v3',device='cpu',compute_type='int8',cpu_threads=4)
for c in [float(x) for x in sys.argv[1:]]:
    s,e=c-2.0,c+2.0
    seg=a[int(s*16000):int(e*16000)]
    # RMS envelope 20 ms
    hop=320; env=[20*np.log10(np.sqrt(np.mean(seg[i:i+hop]**2))+1e-6) for i in range(0,len(seg)-hop,hop)]
    print(f'== {c}  ({s:.2f}-{e:.2f}) dB/40ms:')
    print(' '.join(f'{s+i*0.02:.2f}:{v:.0f}' for i,v in enumerate(env) if i%2==0))
    r,_=m.transcribe(seg,language='es',word_timestamps=True,vad_filter=False,condition_on_previous_text=False,beam_size=5,temperature=0)
    for x in r:
        print('  ', ' '.join(f"{w.word.strip()}[{s+w.start:.2f}-{s+w.end:.2f} p{w.probability:.2f}]" for w in x.words))
