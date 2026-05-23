#!/bin/bash
# SessionStart hook for Claude Code on the web.
# Installs the runtime dependency and sets a headless environment so
# THRESHOLD (a pygame app) can run its tests / render scripts in a
# session that has no display or audio device.
set -euo pipefail

# Web sessions only: local sessions manage their own environment (and
# have a real display, so the dummy SDL drivers below would break it).
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Install pygame. `pip install -r` is idempotent and the resulting
# container state is cached, so re-runs are cheap.
python -m pip install -q --root-user-action=ignore -r "$CLAUDE_PROJECT_DIR/requirements.txt"

# Persist a headless environment for the whole session: dummy SDL
# video/audio so pygame initialises without a display, and the repo
# root on PYTHONPATH so ad-hoc scripts can `import systems`/`scenes`.
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  {
    echo 'export SDL_VIDEODRIVER=dummy'
    echo 'export SDL_AUDIODRIVER=dummy'
    echo 'export PYTHONPATH=.'
  } >> "$CLAUDE_ENV_FILE"
fi
