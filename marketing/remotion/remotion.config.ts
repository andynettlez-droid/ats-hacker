import { Config } from "@remotion/cli/config";

// Remotion configuration for ATSHacker vertical short-form videos.
// CLI flags (e.g. --codec) override these settings.
Config.setVideoImageFormat("jpeg");
Config.setConcurrency(null); // auto based on CPU cores
Config.setOverwriteOutput(true);

// H.264 MP4 is the most compatible output for TikTok / Reels / Shorts.
Config.setCodec("h264");
