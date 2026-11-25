import {Composition} from 'remotion';
import {Edit} from './Edit';
import edl from './edl.json';

export const Root = () => (
	<Composition id="Edit" component={Edit} durationInFrames={edl.frames} fps={30} width={1080} height={1920} />
);
