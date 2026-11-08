#!/usr/bin/env bash
# Publishes content/courses to the public course repo and refreshes the jsDelivr CDN.
#
#   bash content/courses/publish.sh "Describe what changed"
#
# Source of truth is this folder (content/courses in the app repo). The public repo
# only mirrors it; never edit the public repo directly.
set -euo pipefail

REPO="${COURSE_REPO:-tankhang1/hablito-courses}"
BRANCH="main"
HERE="$(cd "$(dirname "$0")" && pwd)"
MESSAGE="${1:-Update course packs}"

node "$HERE/build-manifest.mjs"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
git clone --quiet --depth 1 --branch "$BRANCH" "https://github.com/$REPO.git" "$WORK"
# Mirror the folder exactly, so deleted packs disappear from the CDN too.
find "$WORK" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
cp -R "$HERE"/. "$WORK"/

cd "$WORK"
if [ -z "$(git status --porcelain)" ]; then
  echo "Nothing changed; already published."
  exit 0
fi
git add -A
git commit --quiet -m "$MESSAGE"
git push --quiet origin "$BRANCH"
echo "Pushed to https://github.com/$REPO"

# jsDelivr caches @main for up to 12 hours; purge so learners see the update now.
for path in manifest.json $(cd "$HERE" && ls packs/*.json); do
  curl -s -o /dev/null "https://purge.jsdelivr.net/gh/$REPO@$BRANCH/$path" || true
done
echo "CDN cache purged: https://cdn.jsdelivr.net/gh/$REPO@$BRANCH/manifest.json"
