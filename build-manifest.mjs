#!/usr/bin/env node
/**
 * Checks every course pack in ./packs and writes ./manifest.json.
 * Run it after editing or adding a pack, then upload this whole folder.
 *
 *   node content/courses/build-manifest.mjs
 */
import { readdirSync, readFileSync, statSync, writeFileSync } from 'node:fs';
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

  const lessons = Array.isArray(pack.lessons) ? pack.lessons : (fail(name, '"lessons" must be a list'), []);
  let phraseCount = 0;
  lessons.forEach((lesson, i) => {
    const at = `lessons[${i}]`;
    if (!lesson.id) fail(name, `${at} missing "id"`);
    checkText(name, lesson.title, `${at}.title`);
    checkText(name, lesson.description, `${at}.description`);
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

  entries.push({
    id: pack.id,
    version: pack.version ?? 1,
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

warnings.forEach((message) => console.warn(`warning  ${message}`));
if (errors.length) {
  errors.forEach((message) => console.error(`error    ${message}`));
  console.error(`\n${errors.length} error(s). manifest.json was not written.`);
  process.exit(1);
}

entries.sort((a, b) => a.level - b.level);
const manifest = { schemaVersion: SCHEMA_VERSION, updatedAt: new Date().toISOString().slice(0, 10), packs: entries };
writeFileSync(join(here, 'manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`);
console.log(`manifest.json written with ${entries.length} level(s).`);
