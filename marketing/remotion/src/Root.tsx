import { Composition } from "remotion";
import { ScoreReveal, scoreRevealSchema, defaultScoreRevealProps } from "./ScoreReveal";

// 1080x1920 vertical, 30fps. Total duration: 16s = 480 frames.
const FPS = 30;
const DURATION_IN_SECONDS = 16;

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="ScoreReveal"
        component={ScoreReveal}
        durationInFrames={DURATION_IN_SECONDS * FPS}
        fps={FPS}
        width={1080}
        height={1920}
        schema={scoreRevealSchema}
        defaultProps={defaultScoreRevealProps}
      />
    </>
  );
};
