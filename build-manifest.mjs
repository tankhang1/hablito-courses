#!/usr/bin/env node
/**
 * Checks every course pack in ./packs and writes ./manifest.json.
 * Run it after editing or adding a pack, then upload this whole folder.
 *
 *   node content/courses/build-manifest.mjs
 */
import { createHash } from 'node:crypto';
import { existsSync, readdirSync, readFileSync, statSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const packDir = join(here, 'packs');
const SCHEMA_VERSION = 1;
const errors = [];
const warnings = [];

const fail = (file, message) => errors.push(`${file}: ${message}`);
const isText = (value) => value && typeof value === 'object' && typeof value.en === 'string' && value.en.trim();

function checkText(file, value, where) {
  if (!isText(value)) fail(file, `${where} needs { "en": "...", "vi": "..." }`);
  else if (!value.vi) warnings.push(`${file}: ${where} has no Vietnamese ("vi") text`);
}

const entries = [];
const seenIds = new Set();

// ── Automatic versioning ─────────────────────────────────────────────────────
// Each manifest entry records a hash of its file's content (ignoring "version").
// When the content changes since the last build, the version goes up by one
// automatically, so apps that downloaded the old copy fetch the new one.
const hashOf = (value) => createHash('sha256').update(JSON.stringify(value)).digest('hex').slice(0, 16);
const readPrevious = (file, key) => {
  try {
    return Object.fromEntries(JSON.parse(readFileSync(file, 'utf8'))[key].map((entry) => [entry.id ?? entry.code, entry]));
  } catch {
    return {};
  }
};
const previousPacks = readPrevious(join(here, 'manifest.json'), 'packs');
const previousLanguages = readPrevious(join(here, 'i18n', 'manifest.json'), 'languages');
const bumped = [];
/** Returns the version to publish, raising it when the content changed. */
function nextVersion(previous, hash, current = 1) {
  if (!previous?.contentHash || previous.contentHash === hash) return Math.max(current, previous?.version ?? current);
  return Math.max(current, (previous.version ?? 1) + 1);
}

for (const name of readdirSync(packDir).filter((file) => file.endsWith('.json')).sort()) {
  const path = join(packDir, name);
  let pack;
  try {
    pack = JSON.parse(readFileSync(path, 'utf8'));
  } catch (error) {
    fail(name, `invalid JSON (${error.message})`);
    continue;
  }
  if (pack.schemaVersion !== SCHEMA_VERSION) fail(name, `schemaVersion must be ${SCHEMA_VERSION}`);
  if (!pack.id) fail(name, 'missing "id"');
  if (seenIds.has(pack.id)) fail(name, `duplicate pack id "${pack.id}"`);
  seenIds.add(pack.id);
  if (typeof pack.level !== 'number') fail(name, '"level" must be a number');
  checkText(name, pack.title, 'title');
  checkText(name, pack.description, 'description');

  if (pack.kind !== 'practice' && !pack.lessons?.length) fail(name, 'a level pack needs lessons');
  if (pack.kind === 'practice' && !pack.conversations?.length) fail(name, 'a practice pack needs conversations');
  const lessons = Array.isArray(pack.lessons) ? pack.lessons : (fail(name, '"lessons" must be a list'), []);
  let phraseCount = 0;
  lessons.forEach((lesson, i) => {
    const at = `lessons[${i}]`;
    if (!lesson.id) fail(name, `${at} missing "id"`);
    checkText(name, lesson.title, `${at}.title`);
    checkText(name, lesson.description, `${at}.description`);
    if (lesson.focus !== undefined) checkText(name, lesson.focus, `${at}.focus`);
    (lesson.phrases ?? []).forEach((phrase, j) => {
      if (!phrase.es || !phrase.en) fail(name, `${at}.phrases[${j}] needs "es" and "en"`);
      if (!phrase.vi) warnings.push(`${name}: ${at}.phrases[${j}] has no "vi"`);
    });
    if (!lesson.phrases?.length) fail(name, `${at} has no phrases`);
    phraseCount += lesson.phrases?.length ?? 0;
  });

  const conversations = pack.conversations ?? [];
  conversations.forEach((conversation, i) => {
    const at = `conversations[${i}]`;
    checkText(name, conversation.title, `${at}.title`);
    const nodeIds = new Set((conversation.nodes ?? []).map((node) => node.id));
    if (!nodeIds.has(conversation.start)) fail(name, `${at}.start "${conversation.start}" is not a node id`);
    (conversation.nodes ?? []).forEach((node) => {
      if (!node.prompt) fail(name, `${at} node "${node.id}" missing "prompt"`);
      checkText(name, node.translation, `${at}.${node.id}.translation`);
      checkText(name, node.hint, `${at}.${node.id}.hint`);
      if (!node.choices?.some((choice) => choice.correct)) fail(name, `${at} node "${node.id}" needs a correct choice`);
      (node.choices ?? []).forEach((choice) => {
        if (choice.next && !nodeIds.has(choice.next)) fail(name, `${at} choice "${choice.id}" → missing node "${choice.next}"`);
        if (!choice.es || !choice.response) fail(name, `${at} choice "${choice.id}" needs "es" and "response"`);
        if (!choice.correct && !choice.correction) warnings.push(`${name}: ${at} wrong choice "${choice.id}" has no "correction"`);
      });
    });
  });

  const { version: _ignored, ...packContent } = pack;
  const contentHash = hashOf(packContent);
  const version = nextVersion(previousPacks[pack.id], contentHash, pack.version ?? 1);
  if (version !== (pack.version ?? 1)) {
    pack.version = version;
    writeFileSync(path, `${JSON.stringify(pack, null, 2)}\n`);
    bumped.push(`${pack.id} → v${version}`);
  }
  entries.push({
    id: pack.id,
    kind: pack.kind === 'practice' ? 'practice' : 'level',
    version,
    contentHash,
    level: pack.level,
    cefr: pack.cefr ?? '',
    title: pack.title,
    description: pack.description,
    file: `packs/${name}`,
    lessonCount: lessons.length,
    conversationCount: conversations.length,
    phraseCount,
    sizeKb: Math.max(1, Math.round(statSync(path).size / 1024)),
  });
}

// ── UI languages ─────────────────────────────────────────────────────────────
// i18n/languages.json lists the languages; each i18n/<code>.json maps English
// source text to its translation. Placeholders like {count} must match exactly.
const i18nDir = join(here, 'i18n');
const languageEntries = [];
let languagesChanged = false;
const placeholders = (text) => (text.match(/\{\w+\}/g) ?? []).sort().join(',');
let languages = [];
try {
  languages = JSON.parse(readFileSync(join(i18nDir, 'languages.json'), 'utf8'));
} catch (error) {
  fail('i18n/languages.json', `unreadable (${error.message})`);
}
for (const language of languages) {
  const file = `${language.code}.json`;
  let strings;
  try {
    strings = JSON.parse(readFileSync(join(i18nDir, file), 'utf8'));
  } catch (error) {
    fail(`i18n/${file}`, `missing or invalid JSON (${error.message})`);
    continue;
  }
  for (const [source, translated] of Object.entries(strings)) {
    if (typeof translated !== 'string' || !translated.trim()) fail(`i18n/${file}`, `empty translation for "${source}"`);
    else if (placeholders(source) !== placeholders(translated)) {
      fail(`i18n/${file}`, `placeholders differ for "${source}"`);
    }
  }
  const contentHash = hashOf(strings);
  const version = nextVersion(previousLanguages[language.code], contentHash, language.version ?? 1);
  if (version !== (language.version ?? 1)) {
    language.version = version;
    languagesChanged = true;
    bumped.push(`${language.code} → v${version}`);
  }
  languageEntries.push({
    code: language.code,
    name: language.name,
    nativeName: language.nativeName,
    version,
    contentHash,
    // Relative to i18n/manifest.json itself.
    file,
    stringCount: Object.keys(strings).length,
    sizeKb: Math.max(1, Math.round(statSync(join(i18nDir, file)).size / 1024)),
  });
}

warnings.forEach((message) => console.warn(`warning  ${message}`));
if (errors.length) {
  errors.forEach((message) => console.error(`error    ${message}`));
  console.error(`\n${errors.length} error(s). manifest.json was not written.`);
  process.exit(1);
}

entries.sort((a, b) => a.level - b.level);
const manifest = { schemaVersion: SCHEMA_VERSION, updatedAt: new Date().toISOString().slice(0, 10), packs: entries };
writeFileSync(join(here, 'manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`);
console.log(`manifest.json written with ${entries.length} pack(s).`);
const i18nManifest = { schemaVersion: SCHEMA_VERSION, updatedAt: manifest.updatedAt, languages: languageEntries };
writeFileSync(join(i18nDir, 'manifest.json'), `${JSON.stringify(i18nManifest, null, 2)}\n`);
console.log(`i18n/manifest.json written with ${languageEntries.length} language(s).`);
if (languagesChanged) {
  writeFileSync(join(i18nDir, 'languages.json'), `${JSON.stringify(languages, null, 2)}\n`);
}
console.log(bumped.length ? `Version bumped: ${bumped.join(', ')}` : 'No content changes; versions unchanged.');
