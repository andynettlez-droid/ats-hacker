import { Composition, Still } from "remotion";
import { ScoreReveal, scoreRevealSchema, defaultScoreRevealProps } from "./ScoreReveal";
import { AvatarReveal, avatarRevealSchema, defaultAvatarRevealProps } from "./AvatarReveal";
import { SignalReveal, signalRevealSchema, defaultSignalRevealProps } from "./SignalReveal";
import { SignalViralAd, signalViralAdSchema, defaultSignalViralAdProps } from "./SignalViralAd";
import {
  SignalBreakthroughAd,
  signalBreakthroughAdSchema,
  defaultSignalBreakthroughAdProps,
} from "./SignalBreakthroughAd";
import {
  ResumeCrimeScene,
  resumeCrimeSceneSchema,
  defaultResumeCrimeSceneProps,
} from "./ResumeCrimeScene";
import {
  TeardownEpisode,
  teardownEpisodeSchema,
  defaultTeardownEpisodeProps,
} from "./TeardownEpisode";
import {
  SignalThumbnail,
  signalThumbnailSchema,
  defaultSignalThumbnailProps,
} from "./SignalThumbnail";

const FPS = 30;
const SCORE_REVEAL_DURATION = 16;
const AVATAR_REVEAL_DURATION = 17; // 17 seconds @ 30 FPS = 510 frames
const ATS_REVEAL_DURATION = 74; // 74 seconds @ 30 FPS = 2220 frames
const SIGNAL_VIRAL_DURATION = 30;
const SIGNAL_BREAKTHROUGH_DURATION = 30;
const RESUME_CRIME_SCENE_DURATION = 45;
const TEARDOWN_EPISODE_DURATION = 8 * 60;
const TEARDOWN_REVIEW_CUT_DURATION = 2 * 60;

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
      <Composition
        id="SignalReveal"
        component={SignalReveal}
        durationInFrames={ATS_REVEAL_DURATION * FPS}
        fps={FPS}
        width={1080}
        height={1920}
        schema={signalRevealSchema}
        defaultProps={defaultSignalRevealProps}
      />
      <Composition
        id="SignalViralAd"
        component={SignalViralAd}
        durationInFrames={SIGNAL_VIRAL_DURATION * FPS}
        fps={FPS}
        width={1080}
        height={1920}
        schema={signalViralAdSchema}
        defaultProps={defaultSignalViralAdProps}
      />
      <Composition
        id="SignalBreakthroughAd"
        component={SignalBreakthroughAd}
        durationInFrames={SIGNAL_BREAKTHROUGH_DURATION * FPS}
        fps={FPS}
        width={1080}
        height={1920}
        schema={signalBreakthroughAdSchema}
        defaultProps={defaultSignalBreakthroughAdProps}
      />
      <Composition
        id="ResumeCrimeScene"
        component={ResumeCrimeScene}
        durationInFrames={RESUME_CRIME_SCENE_DURATION * FPS}
        fps={FPS}
        width={1080}
        height={1920}
        schema={resumeCrimeSceneSchema}
        defaultProps={defaultResumeCrimeSceneProps}
      />
      <Composition
        id="TeardownEpisode"
        component={TeardownEpisode}
        durationInFrames={TEARDOWN_EPISODE_DURATION * FPS}
        fps={FPS}
        width={1920}
        height={1080}
        schema={teardownEpisodeSchema}
        defaultProps={defaultTeardownEpisodeProps}
      />
      <Composition
        id="TeardownEpisodeReviewCut"
        component={TeardownEpisode}
        durationInFrames={TEARDOWN_REVIEW_CUT_DURATION * FPS}
        fps={FPS}
        width={1920}
        height={1080}
        schema={teardownEpisodeSchema}
        defaultProps={{
          ...defaultTeardownEpisodeProps,
          durationInFrames: TEARDOWN_REVIEW_CUT_DURATION * FPS,
        }}
      />
      <Still
        id="SignalThumbnail"
        component={SignalThumbnail}
        width={1280}
        height={720}
        schema={signalThumbnailSchema}
        defaultProps={defaultSignalThumbnailProps}
      />
    </>
  );
};
