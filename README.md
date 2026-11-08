# Hablito course packs

Downloadable course content for the mobile app. Nothing in this folder is bundled into
the app: the app reads `manifest.json` from a URL, lists the levels, and downloads a
level's JSON file when the learner taps it. Downloaded levels are saved in the
on-device SQLite database and work offline.

```
content/courses/
├── manifest.json        generated: the list of levels the app shows
├── build-manifest.mjs   checks every pack and regenerates manifest.json
└── packs/
    ├── level-01.json    one file per level
    └── …
```

## Where it's hosted

Published to the public repo [tankhang1/hablito-courses](https://github.com/tankhang1/hablito-courses)
and served by jsDelivr at `https://raw.githubusercontent.com/tankhang1/hablito-courses/main/manifest.json`.
This folder is the source of truth; never edit the public repo directly.

## Publishing changes

**Quick path:** `bash content/courses/publish.sh "What changed"` validates, rebuilds the
manifest, syncs to the public repo, rewrites every pack URL to a commit-pinned jsDelivr
URL, and pushes. Learners see changes within 5 minutes.

The manifest is read from `raw.githubusercontent.com` (5-minute cache, CORS `*`). Pack
files are served by jsDelivr at `@<commit>` URLs, which never go stale. Don't point the
app at a jsDelivr `@main` URL: branch-level caching there can serve files up to 12
hours old.


1. Edit or add a file in `packs/`. To publish a change to an existing level, raise its
   `"version"` so learners see "Update available".
2. Check the packs and rebuild the list:
   ```bash
   node content/courses/build-manifest.mjs
   ```
   It stops with an error if a pack is broken, and warns about missing Vietnamese text.
3. Upload the whole `content/courses/` folder, keeping the same layout, so that
   `manifest.json` and `packs/` sit next to each other.
4. Set the app's course list URL to the uploaded `manifest.json` (see below).

Any static file host works if it serves files over **HTTPS** and allows cross-origin
requests (needed only for the web preview). Good free options:

| Host | Manifest URL looks like |
| --- | --- |
| GitHub repo + jsDelivr CDN | `https://cdn.jsdelivr.net/gh/<user>/<repo>@main/content/courses/manifest.json` |
| Cloudflare Pages / R2 | `https://<project>.pages.dev/manifest.json` |
| Firebase Hosting | `https://<project>.web.app/manifest.json` |

jsDelivr caches files for up to 12 hours; purge the cache after publishing if you need
changes to appear immediately.

## Pointing the app at the list

Set `EXPO_PUBLIC_COURSE_MANIFEST_URL` in `artifacts/mobile/.env`, then restart Expo:

```bash
EXPO_PUBLIC_COURSE_MANIFEST_URL=https://cdn.jsdelivr.net/gh/<user>/<repo>@main/content/courses/manifest.json
```

The value is baked into the app at build time, so set it before building a release.

### Local testing

```bash
python3 -m http.server 8787 --directory content/courses
```

and use `http://localhost:8787/manifest.json` (iOS simulator and web), or
`http://10.0.2.2:8787/manifest.json` (Android emulator). Real phones need your
computer's LAN IP, e.g. `http://192.168.1.20:8787/manifest.json`.

## Pack format

Every text a learner reads is an object with `"en"` (required) and `"vi"` (optional,
falls back to English). Spanish text (`es`, `prompt`, `response`, `correction`) is a
plain string.

```jsonc
{
  "schemaVersion": 1,
  "id": "level-01",            // unique and permanent; used to track progress
  "version": 1,                // raise to publish an update
  "level": 1,                  // order in the library
  "cefr": "A1",
  "title": { "en": "Starter 1: First words", "vi": "Khởi đầu 1: Những từ đầu tiên" },
  "description": { "en": "…", "vi": "…" },
  "lessons": [
    {
      "id": "feelings",
      "title": { "en": "How I feel", "vi": "Cảm xúc của tôi" },
      "description": { "en": "…", "vi": "…" },
      "icon": "smile",         // any Feather icon name
      "phrases": [
        { "es": "Tengo hambre", "en": "I'm hungry", "vi": "Tôi đói",
          "note": { "en": "Optional tip", "vi": "Mẹo (không bắt buộc)" } }
      ]
    }
  ],
  "conversations": [
    {
      "id": "classmate",
      "title": { "en": "…", "vi": "…" },
      "description": { "en": "…", "vi": "…" },
      "icon": "heart",         // coffee | briefcase | compass | map-pin | heart
      "duration": "3 min",
      "start": "hi",           // id of the first node
      "nodes": [
        {
          "id": "hi",
          "prompt": "¡Hola! ¿Cómo estás?",
          "translation": { "en": "Hi! How are you?", "vi": "Chào bạn! Bạn khỏe không?" },
          "hint": { "en": "Answer with “Estoy…”.", "vi": "Trả lời bằng “Estoy…”." },
          "choices": [
            { "id": "fine", "es": "Estoy bien.", "translation": { "en": "I'm fine.", "vi": "Mình ổn." },
              "correct": true, "response": "¡Qué bueno!", "responseTranslation": { "en": "Great!", "vi": "Tốt quá!" },
              "next": "hungry" },  // omit "next" to end the conversation
            { "id": "thanks", "es": "De nada.", "translation": { "en": "You're welcome.", "vi": "Không có gì." },
              "correct": false, "correction": "Estoy bien.",
              "response": "¿Pero cómo estás?", "responseTranslation": { "en": "But how are you?", "vi": "Nhưng bạn khỏe không?" } }
          ]
        }
      ]
    }
  ]
}
```

Wrong answers are saved to the learner's Review cards. Every lesson gets an automatic
quiz; passing it marks the lesson as learned.
