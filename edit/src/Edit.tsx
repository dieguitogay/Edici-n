import React from 'react';
import {AbsoluteFill, Audio, OffthreadVideo, Sequence, staticFile, useCurrentFrame} from 'remotion';
import edl from './edl.json';

type Clip = {src: number; out: number; dur: number; scale: number};
type AClip = {src: number; out: number; dur: number; fin: number; fout: number};
type Gfx = {id: string; sf: number; df: number; full: boolean};
type Cue = {text: string; sf: number; ef: number};

const FULL = (edl.gfx as Gfx[]).filter((g) => g.full);
const inFull = (f: number) => FULL.some((g) => f >= g.sf && f < g.sf + g.df);

// Plano base: cada tramo conserva su sincronía con el audio de origen.
const BaseClip: React.FC<{c: Clip}> = ({c}) => {
	const f = useCurrentFrame() + c.out; // fotograma absoluto de salida
	const full = inFull(f);
	return (
		<OffthreadVideo
			src={staticFile('master30.mp4')}
			trimBefore={c.src}
			muted
			style={{
				width: 1080,
				height: 1920,
				transformOrigin: '50% 36%',
				transform: `scale(${full ? c.scale * 1.12 : c.scale})`,
				filter: full ? 'blur(26px) brightness(0.5) saturate(0.8)' : undefined,
			}}
		/>
	);
};

const AudioClip: React.FC<{a: AClip}> = ({a}) => (
	<Audio
		src={staticFile('audio_norm.wav')}
		trimBefore={a.src}
		volume={(f) => {
			let v = 1;
			if (a.fin) v = Math.min(v, (f + 1) / a.fin);
			if (a.fout) v = Math.min(v, (a.dur - f) / a.fout);
			return Math.max(0, Math.min(1, v));
		}}
	/>
);

// Superposiciones de Hyperframes (ProRes 4444 con alfa)
const Overlay: React.FC<{g: Gfx}> = ({g}) => {
	const f = useCurrentFrame() + g.sf;
	const hidden = !g.full && inFull(f);
	return (
		<AbsoluteFill style={{opacity: hidden ? 0 : 1}}>
			{g.full ? <AbsoluteFill style={{background: 'rgba(6,12,40,0.42)'}} /> : null}
			{g.id === 'drama' ? (
				<OffthreadVideo src={staticFile('gfx/drama.mp4')} muted />
			) : (
				<OffthreadVideo src={staticFile(`gfx/${g.id}.mov`)} transparent muted />
			)}
		</AbsoluteFill>
	);
};

const renderCue = (t: string) =>
	t.split(/(\*[^*]+\*)/g).map((p, i) =>
		p.startsWith('*') ? (
			<span key={i} style={{color: '#ffc46b', fontWeight: 700}}>
				{p.slice(1, -1)}
			</span>
		) : (
			<React.Fragment key={i}>{p}</React.Fragment>
		),
	);

const Subtitles: React.FC = () => {
	const f = useCurrentFrame();
	const cue = (edl.cues as Cue[]).find((c) => f >= c.sf && f <= c.ef);
	if (!cue) return null;
	const k = f - cue.sf;
	const opacity = Math.min(1, (k + 1) / 3, (cue.ef - f + 1) / 2);
	return (
		<AbsoluteFill>
			<div
				style={{
					position: 'absolute',
					left: 110,
					right: 130,
					bottom: 470,
					textAlign: 'center',
					fontFamily: 'Inter',
					fontWeight: 600,
					fontSize: 52,
					lineHeight: 1.2,
					letterSpacing: '-0.005em',
					color: '#fff4e6',
					textWrap: 'balance' as any,
					textShadow: '0 2px 12px rgba(0,0,0,0.55), 0 1px 3px rgba(0,0,0,0.45)',
					opacity,
				}}
			>
				{renderCue(cue.text)}
			</div>
		</AbsoluteFill>
	);
};

export const Edit: React.FC = () => (
	<AbsoluteFill style={{background: '#000'}}>
		{(edl.video as Clip[]).map((c, i) => (
			<Sequence key={`v${i}`} from={c.out} durationInFrames={c.dur} premountFor={30}>
				<BaseClip c={c} />
			</Sequence>
		))}
		{(edl.audio as AClip[]).map((a, i) => (
			<Sequence key={`a${i}`} from={a.out} durationInFrames={a.dur}>
				<AudioClip a={a} />
			</Sequence>
		))}
		{(edl.gfx as Gfx[])
			.slice()
			.sort((x, y) => Number(x.id !== 'drama') - Number(y.id !== 'drama') || Number(x.full) - Number(y.full))
			.map((g) => (
				<Sequence key={g.id} from={g.sf} durationInFrames={g.df} premountFor={30}>
					<Overlay g={g} />
				</Sequence>
			))}
		{/* Diseño sonoro de la apertura: siempre por debajo de la voz */}
		<Sequence from={0} durationInFrames={606}>
			<Audio src={staticFile('sfx.wav')} />
		</Sequence>
		<Subtitles />
	</AbsoluteFill>
);
