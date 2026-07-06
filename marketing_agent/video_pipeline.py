#!/usr/bin/env python3
"""Retired legacy video pipeline entrypoint.

The old script was intentionally removed after creative QA failed repeated
AI-sounding scripts, arbitrary score reveals, and brittle site-demo timing.
Use signal_growth_pipeline.py instead.
"""

from __future__ import annotations

import sys


MESSAGE = """
marketing_agent/video_pipeline.py is retired.

Use the Signal Growth Engine workflow instead:

  py -3 marketing_agent/signal_growth_pipeline.py init-run --topic "resume teardown"
  py -3 marketing_agent/signal_growth_pipeline.py voice --text-file marketing/growth_runs/<run>/vo.txt --out marketing/growth_runs/<run>/vo.mp3
  py -3 marketing_agent/signal_growth_pipeline.py assemble --work-dir C:\\Users\\andyn\\Downloads --out signal_ad_final_pipeline.mp4
  py -3 marketing_agent/signal_growth_pipeline.py qa --video C:\\Users\\andyn\\Downloads\\signal_ad_final_pipeline.mp4

Live posting stays blocked until the exact reviewed video is approved in Codex chat.
"""


def main() -> int:
    sys.stderr.write(MESSAGE.strip() + "\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
