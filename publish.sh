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

# Pin every pack URL to this exact commit on jsDelivr. A commit URL never changes, so
# learners can never get a stale pack, while the manifest itself is read from
# raw.githubusercontent.com (cached for at most 5 minutes).
SHA="$(git rev-parse HEAD)"
node -e '
  const fs = require("fs");
  const [repo, sha] = process.argv.slice(1);
  const pin = (file) => `https://cdn.jsdelivr.net/gh/${repo}@${sha}/${file.replace(/^https?:\/\/[^]*?@[0-9a-f]+\//, "")}`;
  const courses = JSON.parse(fs.readFileSync("manifest.json", "utf8"));
  for (const pack of courses.packs) pack.file = pin(pack.file);
  fs.writeFileSync("manifest.json", JSON.stringify(courses, null, 2) + "\n");
  if (fs.existsSync("i18n/manifest.json")) {
    const i18n = JSON.parse(fs.readFileSync("i18n/manifest.json", "utf8"));
    for (const language of i18n.languages) {
      if (!/^https?:/.test(language.file)) language.file = pin(`i18n/${language.file}`);
    }
    fs.writeFileSync("i18n/manifest.json", JSON.stringify(i18n, null, 2) + "\n");
  }
' "$REPO" "$SHA"
git add manifest.json i18n/manifest.json 2>/dev/null || git add manifest.json
git commit --quiet -m "Pin pack URLs to $SHA"
git push --quiet origin "$BRANCH"
echo "Published to https://github.com/$REPO"
echo "Course list: https://raw.githubusercontent.com/$REPO/$BRANCH/manifest.json (live within 5 minutes)"
