import { Composition, Still, type CalculateMetadataFunction } from "remotion";
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
  type ResumeCrimeSceneProps,
} from "./ResumeCrimeScene";
import { ResumeDeskReview } from "./ResumeDeskReview";
import {
  TeardownEpisode,
  teardownEpisodeSchema,
  defaultTeardownEpisodeProps,
  type TeardownEpisodeProps,
} from "./TeardownEpisode";
import {
  SignalThumbnail,
  signalThumbnailSchema,
  defaultSignalThumbnailProps,
} from "./SignalThumbnail";
import {
  SignalJourneyImageVideo,
  signalJourneyImageVideoSchema,
  defaultSignalJourneyImageVideoProps,
  type SignalJourneyImageVideoProps,
} from "./SignalJourneyImageVideo";

const FPS = 30;
const SCORE_REVEAL_DURATION = 16;
const AVATAR_REVEAL_DURATION = 17; // 17 seconds @ 30 FPS = 510 frames
const ATS_REVEAL_DURATION = 74; // 74 seconds @ 30 FPS = 2220 frames
const SIGNAL_VIRAL_DURATION = 30;
const SIGNAL_BREAKTHROUGH_DURATION = 30;
const SIGNAL_JOURNEY_IMAGE_DURATION = 28;
const RESUME_CRIME_SCENE_DURATION = 28;
const TEARDOWN_EPISODE_DURATION = 8 * 60;
const TEARDOWN_REVIEW_CUT_DURATION = 2 * 60;

const teardownEpisodeMetadata: CalculateMetadataFunction<TeardownEpisodeProps> = async ({
  props,
}) => ({
  durationInFrames: Math.max(
    TEARDOWN_REVIEW_CUT_DURATION * FPS,
    Math.min(12 * 60 * FPS, Number(props.durationInFrames || TEARDOWN_EPISODE_DURATION * FPS)),
  ),
});

const resumeCrimeSceneMetadata: CalculateMetadataFunction<ResumeCrimeSceneProps> = async ({
  props,
}) => {
  const captionEndMs = Math.max(
    0,
    ...((props.captions || []).map((caption) => Number(caption.endMs || 0))),
  );
  const fromCaptions = captionEndMs > 0 ? Math.ceil((captionEndMs / 1000 + 2.2) * FPS) : 0;
  const fromProps = props.durationSeconds ? Math.ceil(props.durationSeconds * FPS) : 0;
  const desired = fromProps || fromCaptions || RESUME_CRIME_SCENE_DURATION * FPS;
  return {
    durationInFrames: Math.max(18 * FPS, Math.min(32 * FPS, desired)),
  };
};

const signalJourneyImageMetadata: CalculateMetadataFunction<SignalJourneyImageVideoProps> = async ({
  props,
}) => {
  const captionEndMs = Math.max(
    0,
    ...((props.captions || []).map((caption) => Number(caption.endMs || 0))),
  );
  const fromCaptions = captionEndMs > 0 ? Math.ceil((captionEndMs / 1000 + 2.4) * FPS) : 0;
  const fromProps = props.durationSeconds ? Math.ceil(props.durationSeconds * FPS) : 0;
  const desired = fromProps || fromCaptions || SIGNAL_JOURNEY_IMAGE_DURATION * FPS;
  return {
    durationInFrames: Math.max(20 * FPS, Math.min(34 * FPS, desired)),
  };
};

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
        id="SignalJourneyImageVideo"
        component={SignalJourneyImageVideo}
        durationInFrames={SIGNAL_JOURNEY_IMAGE_DURATION * FPS}
        fps={FPS}
        width={1280}
        height={720}
        schema={signalJourneyImageVideoSchema}
        defaultProps={defaultSignalJourneyImageVideoProps}
        calculateMetadata={signalJourneyImageMetadata}
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
        calculateMetadata={resumeCrimeSceneMetadata}
      />
      <Composition
        id="ResumeDeskReview"
        component={ResumeDeskReview}
        durationInFrames={RESUME_CRIME_SCENE_DURATION * FPS}
        fps={FPS}
        width={1080}
        height={1920}
        schema={resumeCrimeSceneSchema}
        defaultProps={{
          ...defaultResumeCrimeSceneProps,
          visualStyle: "stickyNote",
          seriesLabel: "Live resume review",
        }}
        calculateMetadata={resumeCrimeSceneMetadata}
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
        calculateMetadata={teardownEpisodeMetadata}
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
