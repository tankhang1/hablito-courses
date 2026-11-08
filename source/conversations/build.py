"""Builds the longer conversations from the scripts in this folder.

Each `*.txt` script adds extra turns to the end of existing conversations so
that every path through a conversation is at least 10 turns long.

Script format (one conversation per `@` block, turns in order):

    @coffee                         built-in conversation id
    @level-05/pharmacy              conversation inside a downloadable pack
    N <Spanish prompt> | <English> | <English hint>
    + <Spanish> | <English> | <Spanish reply> | <English reply>
    - <Spanish> | <English> | <better Spanish> | <Spanish reply> | <English reply>

`+` lines are good answers and `-` lines are off-track ones. Each turn leads to
the next; the last turn ends the conversation. Every reply that used to end the
original conversation now leads into the first new turn.

Translations live in `translations/<lang>.json` (English text → translation).

Usage:
    python3 build.py keys   <out-dir>    write the English strings still missing a translation
    python3 build.py import <in-dir>     merge `<lang>.txt` files (`index|text`) for those strings
    python3 build.py apply               write the app file, the UI language files and the packs
"""

import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
COURSES = os.path.normpath(os.path.join(HERE, '..', '..'))
APP_DATA = os.path.normpath(os.path.join(COURSES, '..', '..', 'artifacts', 'mobile', 'data'))
BUILTIN_DUMP = os.path.join(HERE, 'builtin.json')  # snapshot of the original built-in conversations
LANGS = ['vi', 'pt-BR', 'fr', 'de', 'it', 'ja', 'zh-Hans']
MIN_TURNS = 10
DURATION = '6 min'
TR_DIR = os.path.join(HERE, 'translations')

# Built-in conversations that moved out of the app into downloadable practice packs.
PRACTICE_PACKS = {
    'practice-01': {
        'level': 101,
        'cefr': 'A1–A2',
        'title': 'Travel extras',
        'description': 'Bus tickets, hotel stays, a SIM card, laundry, and sightseeing.',
        'conversations': ['bus-ticket', 'hotel-checkout', 'hotel-wifi', 'sim-card', 'laundry', 'museum-ticket', 'guided-tour'],
    },
    'practice-02': {
        'level': 102,
        'cefr': 'A1–A2',
        'title': 'Health, problems & plans',
        'description': 'See a doctor, explain an allergy, report a loss, and handle invitations.',
        'conversations': ['clinic', 'food-allergy', 'lost-phone', 'lost-luggage', 'politely-decline', 'beach-activities'],
    },
}
MOVED = {cid: pack for pack, cfg in PRACTICE_PACKS.items() for cid in cfg['conversations']}


def parse_scripts():
    convos = {}
    for path in sorted(glob.glob(os.path.join(HERE, '*.txt'))):
        current = None
        for raw in open(path, encoding='utf-8'):
            line = raw.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('@'):
                current = {'key': line[1:].strip(), 'nodes': []}
                if current['key'] in convos:
                    sys.exit(f'{path}: {current["key"]} is scripted twice')
                convos[current['key']] = current
                continue
            kind, rest = line[0], [p.strip() for p in line[1:].split('|')]
            if kind == 'N':
                if len(rest) != 3:
                    sys.exit(f'{path}: bad turn line: {line}')
                current['nodes'].append({'prompt': rest[0], 'en': rest[1], 'hint': rest[2], 'choices': []})
            elif kind in '+-':
                want = 4 if kind == '+' else 5
                if len(rest) != want:
                    sys.exit(f'{path}: bad choice line ({len(rest)} parts): {line}')
                choice = {'correct': kind == '+', 'es': rest[0], 'en': rest[1]}
                if kind == '+':
                    choice.update(response=rest[2], responseEn=rest[3])
                else:
                    choice.update(correction=rest[2], response=rest[3], responseEn=rest[4])
                current['nodes'][-1]['choices'].append(choice)
            else:
                sys.exit(f'{path}: unknown line: {line}')
    for key, convo in convos.items():
        for i, node in enumerate(convo['nodes']):
            if len(node['choices']) < 2:
                sys.exit(f'{key} turn {i + 1}: needs at least two answers')
            if not any(c['correct'] for c in node['choices']):
                sys.exit(f'{key} turn {i + 1}: needs a good answer')
    return convos


def min_turns(nodes, start, next_of):
    """Fewest turns on any path from the start to an ending."""
    best = [10 ** 6]

    def go(node_id, depth, seen):
        for choice in nodes[node_id]['choices']:
            nxt = next_of(choice)
            if nxt and nxt not in seen:
                go(nxt, depth + 1, seen | {nxt})
            else:
                best[0] = min(best[0], depth)

    go(start, 1, {start})
    return best[0]


def builtin_scenarios():
    return {s['id']: s for s in json.load(open(BUILTIN_DUMP, encoding='utf-8'))}


def pack_path(level):
    return os.path.join(COURSES, 'packs', f'{level}.json')


def from_builtin(sc):
    """A built-in conversation in pack format (English only; localized on apply)."""
    nodes = []
    for node in sc['nodes'].values():
        choices = []
        for c in node['choices']:
            choice = {'id': c['id'], 'es': c['spanish'], 'translation': c['translation'], 'correct': c['isCorrect']}
            if c.get('correctionSpanish'):
                choice['correction'] = c['correctionSpanish']
            choice['response'] = c['response']
            choice['responseTranslation'] = c['responseTranslation']
            if c.get('nextNodeId'):
                choice['next'] = c['nextNodeId']
            choices.append(choice)
        nodes.append({'id': node['id'], 'prompt': node['prompt'], 'translation': node['translation'], 'hint': node['hint'], 'choices': choices})
    return {'id': sc['id'], 'title': sc['title'], 'description': sc['description'], 'icon': sc['icon'],
            'duration': sc['duration'], 'start': sc['startNodeId'], 'nodes': nodes, 'fromBuiltin': True}


def original_pack_conversation(key):
    level, convo_id = key.split('/')
    if level in PRACTICE_PACKS:
        return None, from_builtin(builtin_scenarios()[convo_id])
    pack = json.load(open(pack_path(level), encoding='utf-8'))
    convo = next(c for c in pack['conversations'] if c['id'] == convo_id)
    convo = dict(convo, nodes=[n for n in convo['nodes'] if not n['id'].startswith('x')])
    return pack, convo


def check_lengths(convos):
    builtins = builtin_scenarios()
    for key, convo in convos.items():
        if '/' in key:
            _, original = original_pack_conversation(key)
            nodes = {n['id']: n for n in original['nodes']}
            base = min_turns(nodes, original['start'], lambda c: c.get('next') if not str(c.get('next', '')).startswith('x') else None)
        else:
            sc = builtins[key]
            base = min_turns(sc['nodes'], sc['startNodeId'], lambda c: c.get('nextNodeId'))
        if base + len(convo['nodes']) < MIN_TURNS:
            sys.exit(f'{key}: {base} + {len(convo["nodes"])} turns is under {MIN_TURNS}')


def english_strings(convos):
    """Every English string the new turns (and built-in originals) need translated."""
    out = []
    builtins = builtin_scenarios()
    for key, convo in convos.items():
        if '/' in key and key.split('/')[0] in PRACTICE_PACKS:
            sc = builtins[key.split('/')[1]]
            out += [sc['title'], sc['description']]
            for node in sc['nodes'].values():
                out += [node['translation'], node['hint']]
                for c in node['choices']:
                    out += [c['translation'], c['responseTranslation']]
        if '/' not in key:
            if key in MOVED:
                sys.exit(f'{key} moved to {MOVED[key]}; script it as @{MOVED[key]}/{key}')
            sc = builtins[key]
            out += [sc['title'], sc['description'], sc['category'], DURATION]
            for node in sc['nodes'].values():
                out += [node['translation'], node['hint']]
                for c in node['choices']:
                    out += [c['translation'], c['responseTranslation']]
        for node in convo['nodes']:
            out += [node['en'], node['hint']]
            for c in node['choices']:
                out += [c['en'], c['responseEn']]
    if any('/' in k and k.split('/')[0] in PRACTICE_PACKS for k in convos):
        for cfg in PRACTICE_PACKS.values():
            out += [cfg['title'], cfg['description']]
    seen, unique = set(), []
    for s in out:
        if s not in seen:
            seen.add(s)
            unique.append(s)
    return unique


def load_translations():
    tr = {}
    for lang in LANGS:
        path = os.path.join(TR_DIR, f'{lang}.json')
        tr[lang] = json.load(open(path, encoding='utf-8')) if os.path.exists(path) else {}
    return tr


def ui_bundle(lang):
    return json.load(open(os.path.join(COURSES, 'i18n', f'{lang}.json'), encoding='utf-8'))


def known(lang, text, tr, bundles):
    return text in tr[lang] or text in bundles[lang]


def cmd_keys(out_dir):
    convos = parse_scripts()
    check_lengths(convos)
    tr, bundles = load_translations(), {l: ui_bundle(l) for l in LANGS}
    strings = english_strings(convos)
    missing = [s for s in strings if any(not known(l, s, tr, bundles) for l in LANGS)]
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, 'keys.txt'), 'w', encoding='utf-8') as f:
        for i, s in enumerate(missing):
            f.write(f'{i}|{s}\n')
    with open(os.path.join(out_dir, 'keys.json'), 'w', encoding='utf-8') as f:
        json.dump(missing, f, ensure_ascii=False)
    need_vi = [i for i, s in enumerate(missing) if not known('vi', s, tr, bundles)]
    print(f'{len(missing)} strings to translate ({len(need_vi)} also need vi)')
    with open(os.path.join(out_dir, 'vi_indexes.txt'), 'w') as f:
        f.write(' '.join(map(str, need_vi)))


SPANISH_IN_QUOTES = re.compile(r'“([^”]*[áéíóúñ¿¡][^”]*)”')


def cmd_import(in_dir):
    keys = json.load(open(os.path.join(in_dir, 'keys.json'), encoding='utf-8'))
    tr, bundles = load_translations(), {l: ui_bundle(l) for l in LANGS}
    problems = 0
    for lang in LANGS:
        path = os.path.join(in_dir, f'{lang}.txt')
        if not os.path.exists(path):
            continue
        got = {}
        for line in open(path, encoding='utf-8'):
            if '|' in line:
                i, text = line.rstrip('\n').split('|', 1)
                got[int(i)] = text.strip()
        for i, english in enumerate(keys):
            if known(lang, english, tr, bundles) and i not in got:
                continue
            if i not in got or not got[i]:
                print(f'{lang}: missing {i}: {english}')
                problems += 1
                continue
            for fragment in SPANISH_IN_QUOTES.findall(english):
                if fragment not in got[i]:
                    print(f'{lang} {i}: Spanish “{fragment}” changed: {got[i]}')
            tr[lang][english] = got[i]
    if problems:
        sys.exit(f'{problems} missing translations; nothing saved')
    os.makedirs(TR_DIR, exist_ok=True)
    for lang in LANGS:
        with open(os.path.join(TR_DIR, f'{lang}.json'), 'w', encoding='utf-8') as f:
            json.dump(tr[lang], f, ensure_ascii=False, indent=0, sort_keys=True)
    print('imported')


def localized(text, tr, bundles):
    out = {'en': text}
    for lang in LANGS:
        value = tr[lang].get(text, bundles[lang].get(text))
        if value is None:
            sys.exit(f'{lang}: no translation for: {text}')
        out[lang] = value
    return out


def cmd_apply():
    convos = parse_scripts()
    check_lengths(convos)
    tr, bundles = load_translations(), {l: ui_bundle(l) for l in LANGS}

    # Built-in conversations: app file + UI language files.
    extensions = {}
    for key, convo in convos.items():
        if '/' in key:
            continue
        nodes = []
        for i, node in enumerate(convo['nodes']):
            node_id = f'x{i + 1}'
            nxt = f'x{i + 2}' if i + 1 < len(convo['nodes']) else None
            choices = []
            for j, c in enumerate(node['choices']):
                choice = {
                    'id': f'{node_id}-{"abcdef"[j]}',
                    'spanish': c['es'],
                    'translation': c['en'],
                    'isCorrect': c['correct'],
                    'response': c['response'],
                    'responseTranslation': c['responseEn'],
                }
                if not c['correct']:
                    choice['correctionSpanish'] = c['correction']
                if nxt:
                    choice['nextNodeId'] = nxt
                choices.append(choice)
            nodes.append({'id': node_id, 'prompt': node['prompt'], 'translation': node['en'], 'hint': node['hint'], 'choices': choices})
        extensions[key] = {'start': 'x1', 'duration': DURATION, 'nodes': nodes}
    body = json.dumps(extensions, ensure_ascii=False, indent=2)
    with open(os.path.join(APP_DATA, 'scenarioExtensions.ts'), 'w', encoding='utf-8') as f:
        f.write(
            '// Generated by content/courses/source/conversations/build.py. Edit the scripts there.\n'
            "import type { ScenarioNode } from './scenarios';\n\n"
            'export const SCENARIO_EXTENSIONS: Record<\n'
            '  string,\n'
            '  { start: string; duration: string; nodes: ScenarioNode[] }\n'
            f'> = {body};\n'
        )
    builtin_strings = english_strings({k: v for k, v in convos.items() if '/' not in k})
    for lang in LANGS:
        bundle = bundles[lang]
        added = 0
        for s in builtin_strings:
            value = tr[lang].get(s, bundle.get(s))
            if value is None:
                sys.exit(f'{lang}: no translation for: {s}')
            if bundle.get(s) != value:
                bundle[s] = value
                added += 1
        with open(os.path.join(COURSES, 'i18n', f'{lang}.json'), 'w', encoding='utf-8') as f:
            json.dump(bundle, f, ensure_ascii=False, indent=2)
            f.write('\n')
        print(f'{lang}: {added} UI strings added')

    # Pack conversations: rewrite the level packs and build the practice packs.
    practice = {pid: {} for pid in PRACTICE_PACKS}
    for key, convo in convos.items():
        if '/' not in key:
            continue
        pack_id = key.split('/')[0]
        pack, original = original_pack_conversation(key)
        new_nodes = []
        for i, node in enumerate(convo['nodes']):
            node_id = f'x{i + 1}'
            nxt = f'x{i + 2}' if i + 1 < len(convo['nodes']) else None
            choices = []
            for j, c in enumerate(node['choices']):
                choice = {
                    'id': f'{node_id}-{"abcdef"[j]}',
                    'es': c['es'],
                    'translation': c['en'],
                    'correct': c['correct'],
                }
                if not c['correct']:
                    choice['correction'] = c['correction']
                choice['response'] = c['response']
                choice['responseTranslation'] = c['responseEn']
                if nxt:
                    choice['next'] = nxt
                choices.append(choice)
            new_nodes.append({'id': node_id, 'prompt': node['prompt'], 'translation': node['en'], 'hint': node['hint'], 'choices': choices})
        for node in original['nodes']:
            for c in node['choices']:
                if not c.get('next'):
                    c['next'] = 'x1'
        original['nodes'] = original['nodes'] + new_nodes
        original['duration'] = DURATION
        # Localize every English string (originals from the app are English-only).
        loc = lambda v: v if isinstance(v, dict) else localized(v, tr, bundles)
        if original.pop('fromBuiltin', False):
            original['title'] = loc(original['title'])
            original['description'] = loc(original['description'])
        for node in original['nodes']:
            node['translation'] = loc(node['translation'])
            node['hint'] = loc(node['hint'])
            for c in node['choices']:
                c['translation'] = loc(c['translation'])
                c['responseTranslation'] = loc(c['responseTranslation'])
        if pack_id in PRACTICE_PACKS:
            practice[pack_id][original['id']] = original
            print(f'{key}: {len(new_nodes)} turns added')
            continue
        pack['conversations'] = [original if c['id'] == original['id'] else c for c in pack['conversations']]
        with open(pack_path(pack_id), 'w', encoding='utf-8') as f:
            json.dump(pack, f, ensure_ascii=False, indent=2)
            f.write('\n')
        print(f'{key}: {len(new_nodes)} turns added')

    for pack_id, cfg in PRACTICE_PACKS.items():
        got = practice[pack_id]
        if not got:
            continue
        missing = [c for c in cfg['conversations'] if c not in got]
        if missing:
            sys.exit(f'{pack_id}: not scripted yet: {", ".join(missing)}')
        path = pack_path(pack_id)
        version = json.load(open(path, encoding='utf-8')).get('version', 1) if os.path.exists(path) else 1
        pack = {
            'schemaVersion': 1,
            'id': pack_id,
            'kind': 'practice',
            'version': version,
            'level': cfg['level'],
            'cefr': cfg['cefr'],
            'title': localized(cfg['title'], tr, bundles),
            'description': localized(cfg['description'], tr, bundles),
            'lessons': [],
            'conversations': [got[c] for c in cfg['conversations']],
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(pack, f, ensure_ascii=False, indent=2)
            f.write('\n')
        print(f'{pack_id}: {len(pack["conversations"])} conversations')


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'keys':
        cmd_keys(sys.argv[2])
    elif cmd == 'import':
        cmd_import(sys.argv[2])
    elif cmd == 'apply':
        cmd_apply()
    else:
        sys.exit(__doc__)
