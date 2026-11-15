#!/usr/bin/env bash
# Forced command of the CI deploy key on the Oracle VM (installed at /opt/fieldshift/deploy.sh,
# NOT updated by deploys). stdin: `git archive` tarball; SSH_ORIGINAL_COMMAND: full commit sha.
# Builds the new release first (old one keeps serving), swaps, health-checks, rolls back on failure.
set -euo pipefail
ROOT=/opt/fieldshift
SHA=${SSH_ORIGINAL_COMMAND:-}
[[ $SHA =~ ^[0-9a-f]{40}$ ]] || { echo "usage: <40-char commit sha> on the ssh command line" >&2; exit 2; }

NEW=$ROOT/releases/$SHA
rm -rf "$NEW" && mkdir -p "$NEW"
tar -x -C "$NEW"
# The compose file decides ports and mounts on the host, so CI may not change it.
cmp -s "$NEW/infra/compose.oracle.yaml" "$ROOT/compose.pinned.yaml" \
  || { echo "infra/compose.oracle.yaml changed: deploy by hand and update compose.pinned.yaml" >&2; exit 3; }

compose() { sudo docker compose -f "$1/infra/compose.oracle.yaml" -p fieldshift "${@:2}"; }
healthy() {
  for _ in $(seq 30); do
    curl -fsS -o /dev/null http://127.0.0.1:18100/v1/health && curl -fsS -o /dev/null http://127.0.0.1:18101/ && return 0
    sleep 2
  done
  return 1
}

PREV=$(readlink -f "$ROOT/current" || true)
compose "$NEW" build
compose "$NEW" up -d
if ! healthy; then
  echo "health check failed, rolling back to ${PREV:-nothing}" >&2
  [[ -n $PREV && -d $PREV ]] && compose "$PREV" up -d --build
  exit 1
fi
ln -sfn "$NEW" "$ROOT/current"
# Keep the last 3 releases.
ls -1dt "$ROOT"/releases/*/ | tail -n +4 | xargs -r rm -rf
sudo docker image prune -f >/dev/null
echo "deployed $SHA"
