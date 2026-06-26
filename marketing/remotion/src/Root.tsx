import { Composition } from "remotion";
import { ScoreReveal, scoreRevealSchema, defaultScoreRevealProps } from "./ScoreReveal";
import { AvatarReveal, avatarRevealSchema, defaultAvatarRevealProps } from "./AvatarReveal";

const FPS = 30;
const SCORE_REVEAL_DURATION = 16;
const AVATAR_REVEAL_DURATION = 17; // 17 seconds @ 30 FPS = 510 frames

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="ScoreReveal"
        component={ScoreReveal}
        durationInFrames={SCORE_REVEAL_DURATION * FPS}
        fps={FPS}
        width={1080}
        height={1920}
        schema={scoreRevealSchema}
        defaultProps={defaultScoreRevealProps}
      />
      <Composition
        id="AvatarReveal"
        component={AvatarReveal}
        durationInFrames={AVATAR_REVEAL_DURATION * FPS}
        fps={FPS}
        width={1080}
        height={1920}
        schema={avatarRevealSchema}
        defaultProps={defaultAvatarRevealProps}
      />
    </>
  );
};

