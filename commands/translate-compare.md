---
name: translate-compare
description: >
  Multi-agent translation with comparison and optimization for GL.iNet product manuals. Spawns
  3 agents per target language (2 Sonnet with distinct style briefs — faithful vs. idiomatic —
  plus 1 Opus polished) to translate in parallel using v2.1 hardcoded decisions, then runs a
  per-language Opus merger, and finally a cross-language Opus coordinator. Hardcoded with both
  v2.0 product-team decisions (business/brand/compliance) and v2.1 specialist-agent decisions
  (linguistic competence, native typography). Invoke this command
  (`/data-team-skills:translate-compare`) for high-quality release-grade translation; does not
  pause to ask the user mid-translation.
---

> **Spec metadata** — v2.1, effective 2026-04-29.
> - **Decisions**: v2.0 product team Q1–Q18 (business / brand / compliance / regional) + v2.1 specialist agents Q19–Q24 (linguistic competence, native typography, Slavic grammar)
> - **Linguist specialists**: De (Duden / DIN 5008) · Fr (Académie / AFNOR / Imprimerie nationale) · Sp (RAE / Fundéu / AENOR) · Pl (PWN / industry corpus)

# Multi-Agent Translation with Comparison (v2.1 Hardcoded-Decisions Edition)

Translate a GL.iNet product manual using three independent agents per target language, compare and merge into one optimized final version per language, then verify cross-language consistency.

**Key changes**:
- **v2.0**: removed user-confirmation Step 2; hardcoded 18 product-team decisions
- **v2.1**: added 4 specialist-agent linguistic decisions (Q19–Q24) covering case handling, native typography, Slavic grammar; reversed Spanish heading from Title Case to sentence case (RAE/Fundéu authoritative)

## Input: $ARGUMENTS

`<source-file-path> <target-language-1> [target-language-2] ...`

If no arguments provided, ask only for source path and target language(s). Do NOT ask about UI strings, EU directive localization, capitalization, terminology, typography — all pre-decided.

## Workflow Overview

| Step | Action | Agents | User confirmation? |
|---|---|---|---|
| 1 | Parse input, set up output dirs | 0 | No |
| 2 | Pre-flight gap-detection scan; log any NEW UI category to `_unhandled-categories.md` and proceed | 0 | No |
| 3 | Spawn 3 translation agents per language | 3 × N | No |
| 4 | Spawn 1 Opus merger per language | N | No |
| 5 | Spawn 1 Opus cross-language coordinator (multi-language only) | 1 | No |
| 6 | Report | 0 | No |

For N target languages, total agents = `3N + N + (1 if N>1 else 0)`.

---

### Step 1: Parse Input and Set Up

Determine source file path, target languages, product name, source language code (default `Eng`).

Build target language code:

| Language | Code |
|---|---|
| German / Deutsch | De |
| Spanish / Español / Spanish-Peninsular | Sp |
| French / Français | Fr |
| Polish / Polski | Pl |
| Italian / Italiano | It |
| Portuguese | Po |
| Japanese | Ja |
| Korean | Ko |
| Chinese | Cn |
| Arabic | Ar |
| Thai | Th |
| Turkish | Tr |
| Dutch | Nl |
| Russian | Ru |

Other languages: first two letters (Cap+lower).

For each target create: `{source-file-directory}/{Product}-{SourceLangCode}2{TargetLangCode}/`

Example: `/path/to/BE3600-Eng2Fr/`, `/path/to/BE3600-Eng2De/`, etc.

---

### Step 2: Pre-Flight Scan (Decisions are Hardcoded — Skip Confirmation)

#### 2a. Scan source for KNOWN categories
Confirm source contains only categories already covered:
- ✅ Web admin panel UI references → handled (English)
- ✅ App button names → handled (English in single quotes)
- ✅ Touchscreen text → handled (English in double quotes, lowercase `to`)
- ✅ System dialog buttons → handled (translated per OS)
- ✅ Physical hardware labels → handled (English)
- ✅ Numeric specs (2.5G, 2.8") → handled (English form)
- ✅ EU directive references → handled (per-language EU/UE)
- ✅ DoC bracket descriptors → handled (full localization, model verbatim)
- ✅ Product adjectives (Portable / Tri-band / Travel etc.) → handled (full localization, Travel added v2.1)
- ✅ Warranty period → handled (translate as-is)
- ✅ Company name → handled (verbatim)
- ✅ Support URL → handled (English URL shared)
- ✅ Common-noun loanwords (firmware) → handled (per-language v2.1 casing rules)
- ✅ Unit spacing (USB3.0, 5V) → handled (typography pass v2.1)

#### 2b. If NEW category appears, log and proceed
Log to `{output-dir-1}/_unhandled-categories.md`. Apply closest existing decision. Flag in final report. **NEVER stop and ask the user.**

#### 2c. Hardcoded Translation Decisions block (v2.1)

> **Cross-file maintenance note**: The block below is a compressed mirror of `translate-manual.md` Decision Blocks 1–7. Any edit to a decision in either file MUST be mirrored to the other — otherwise the multi-agent command (this file) and the single-agent command will diverge. There is no automated parity check.

The following block is **inlined verbatim** into every translation agent's prompt at Step 3.

```
## TRANSLATION DECISIONS (HARDCODED — NEVER OVERRIDE)
Source: hardcoded inline below (v2.0 product team Q1–Q18 + v2.1 specialist agents Q19–Q24, signed off 2026-04-29; full audit retained out-of-band by maintainer).

### Terminology (apply to the 4 approved languages: De / Fr / Sp / Pl; for other target languages — It / Pt / Ja / Ko / Zh / Ar / Th / Tr / Nl / Ru — apply structural rules only and log to `{output-dir-1}/_unhandled-categories.md` so the maintainer can decide whether to commission a specialist round)
- Wi-Fi → Wi-Fi (verbatim)
- Router → German "Router", French "routeur", Spanish "Router", Polish "Router"
- Email → German "E-Mail", French "E-mail", Spanish "Correo", Polish "E-mail"
- Firmware → Firmware (verbatim, all languages); Polish has v2.1 case fallback (see below)
- SSID / LAN / WAN / USB / LED / IP / DHCP / DNS / VPN / OpenVPN / WireGuard / MAC / APN → English (verbatim)
- Wi-Fi 7 / Wi-Fi 6 / 5G NR / 5G / 4G LTE / Nano-SIM / Bluetooth / QR Code / Ethernet / PCBA → English (verbatim)
- Product names (Flint 2, Mudi 7, GL-E5800, GL-BE3600 etc.) → verbatim, never translate, never reorder
- Support URLs (link.gl-inet.com/...) → same English URL in every language

### v2.1 Polish Slavic case handling for kept-English nouns
- Router declines without apostrophe: Router (Nom) / Routera (Gen/Acc) / Routerowi (Dat) / Routerem (Instr) / Routerze (Loc)
- Firmware: nominative-only or UI-label only → keep "Firmware". Oblique cases → fall back to "oprogramowanie układowe":
    Genitive: oprogramowania układowego (NOT oprogramowania Firmware — that's a wrong hybrid)
    Accusative: oprogramowanie układowe
    Instrumental: oprogramowaniem układowym
    Locative: o oprogramowaniu układowym
- Wi-Fi / SSID / LAN / WAN / USB / LED / DHCP / DNS / VPN / MAC / APN: invariant; carrier noun carries grammar
    (sieć Wi-Fi, do sieci Wi-Fi, port LAN, adres MAC, identyfikator SSID)
- Ethernet / Bluetooth: decline regularly without apostrophe (Ethernetu, Bluetootha, Bluetoothem)
- FORBIDDEN: apostrophe-declension of common-noun anglicisms (Router'a, Firmware'u, Ethernet'em — all WRONG)

### UI Strings
- Web admin panel paths → KEEP ENGLISH (e.g., `Network > Ethernet Ports`, `MAC Mode`)
- GL.iNet App button names → KEEP ENGLISH in single quotes (e.g., `'Add a New Device'`)
- Touchscreen display text → KEEP ENGLISH in ASCII double quotes (`"Release to Reset Mode"`); normalize to lowercase `to`
- Physical printed text on hardware (POWER / RESET / USB-C / PUSH) → KEEP ENGLISH verbatim
- System-level dialog buttons (iOS/Android Wi-Fi popup) → TRANSLATE per target OS standard:
    German `'Verbinden'`, French `'Rejoindre'`, Spanish `'Unirse'`, Polish `'Dołącz'`

### v2.1 UI Quote scope clarification
ASCII-quote rule applies ONLY to UI categories above. Prose-quoted native-language text (status string in flowing prose, term in apposition) uses target-language native typography:
- French: `« texte »` with U+202F inside both guillemets
- Polish: `„texte"` (low-9 + high-9 pair)
- Spanish: ASCII per stability lock
- German: ASCII acceptable for cross-language stability

### Formatting
- Numbers and units: keep English form (`2.5G`, `2.8"`, `1.2 GHz`) — never `2,5G` / `2,8 Zoll`
- Heading capitalization per-language convention:
    German → sentence case + nouns capitalized per Duden §57 orthography (kept-English nouns inherit auto)
    French → sentence case, only first word + proper nouns capitalized
    Spanish (v2.1 REVERSAL) → sentence case (NOT Title Case — Title Case is Anglicism per RAE/Fundéu)
    Polish → sentence case, only first word capitalized; kept-English tokens retain capitalization
- Markdown format: preserve byte-for-byte (don't swap `**bold**` for `# heading` or vice versa)
- Quotes for UI strings: ASCII straight quotes (`"..."` and `'...'`)

### v2.1 Cross-language kept-English token rule
Kept-English tokens (Router, Wi-Fi, Firmware, Bluetooth, Ethernet, SSID, LAN, WAN, USB, LED, IP, DHCP, DNS, VPN, OpenVPN, WireGuard, MAC, APN, Nano-SIM, QR Code, PCBA, 5G, 5G NR, 4G LTE, Wi-Fi 7, Wi-Fi 6) are treated as proper-noun-like product/spec anchors. Retain Decision-Block-1 canonical capitalization in ALL positions — sentence-initial, mid-sentence, mid-heading — regardless of surrounding heading/sentence case rules.

### Compliance / Legal
- EU Directive numbering:
    German → keep "EU" (e.g., `Richtlinie 2014/53/EU`)
    French → "UE" (e.g., `directive 2014/53/UE`)
    Spanish → "UE" (e.g., `Directiva 2014/53/UE`)
    Polish → "UE" (e.g., `dyrektywa 2014/53/UE`)
- DoC bracket descriptors: FULLY LOCALIZE the description, model number stays verbatim
    German example (v2.1 compound order): `[Dualband-Wi-Fi 7-Reise-Router, GL-BE3600]`
    Order: [Tragbar/Mobil if present] + [BandClass: Dualband/Dreiband] + [Wi-Fi standard] + [Use prefix: Reise- if Travel] + Router
- DoC descriptor must be BYTE-IDENTICAL to any other occurrence of the same descriptor (e.g., front product card)
- Product adjectives (per Rule 7c v2.1):
    Portable → Tragbar / portable / portátil / przenośny
    Tri-band → Dreiband / tri-bande / tribanda / trójzakresowy
    Dual-band → Dualband / bi-bande / doble banda / dwuzakresowy
    Mobile → Mobil / mobile / móvil / mobilny
    Compact → Kompakt / compact / compacto / kompaktowy
    Travel → Reise- / de voyage / de viaje / podróżny  (NEW v2.1)
- Warranty period clauses: translate as-is, NO market-specific differentiation
- Company name `GL TECHNOLOGIES (HONG KONG) LIMITED` → never translate

### Tone
- All four languages: formal address (German Sie, French vous, Spanish usted, Polish Pan/Pani)
- Imperative instructions: formal-imperative (Drücken Sie / Appuyez / Pulse / Naciśnij)

### Spanish Variant (v2.0 + v2.1 two-class casing)
- Use Peninsular Spanish (Spain), NOT LatAm
- ordenador (not computadora), vídeo (not video), portátil (not laptop), móvil (not celular), vale (not okay)
- v2.1 Spanish loanword two-class casing:
    Brand-style class (always cap): Wi-Fi, Bluetooth, Ethernet, Router, SSID, LAN, WAN, USB, LED, IP, DHCP, DNS, VPN, OpenVPN, WireGuard, MAC, APN, Nano-SIM, QR Code, PCBA, 5G, 5G NR, 4G LTE, Wi-Fi 7, Wi-Fi 6, GL.iNet, GL-<model>, App Store, Google Play
    Common-noun class (lowercase mid-sentence; capital only at sentence start): firmware, software, hardware, streaming, malware
    Examples: ✅ "uso de firmware de terceros" / ❌ "uso de Firmware de terceros" (v2.0 BE3600 line 207 was wrong)
- v2.1 Spanish: `internet` lowercase mid-sentence and in headings (RAE 2014 / Fundéu)

### v2.1 Per-Language Typography (mandatory pass before save)

#### German (DIN 5008)
1. Insert space between value and unit: USB3.0 → USB 3.0, 2.5GHz → 2.5 GHz, 100m → 100 m, standalone 5V → 5 V. EXCEPTION: networking spec tokens (2.5G, 5G NR, 4G LTE, Wi-Fi 7) excluded — Q10 prevails.
2. Collapse soft line break mid-clause to single space.
3. Stray U+00A0 NBSP → regular space (except DIN 5008 NBSP between value and unit).

#### French (AFNOR / Imprimerie nationale)
1. U+202F (narrow no-break space) before `:` `;` `?` `!`, after `«`, before `»`.
2. U+00A0 between number+unit and inside inseparable expressions (M. Dupont, n° 4).
3. USB3.0 → USB 3.0.
4. Merge mid-clause line breaks (heuristic: line ends without terminal punctuation AND next line starts lowercase).
5. Apostrophes in prose: ASCII `'` → curly `’` (U+2019). Exception: keep ASCII inside ASCII-quoted UI strings, URLs, code blocks.
6. Ellipsis: `...` → `…` (U+2026).
7. Em-dash with non-breaking spaces ` — ` for parenthetical inserts.
8. Prose-quoted French uses guillemets `« »` with U+202F; UI-categorized strings use ASCII.
9. Common-noun loanwords (firmware, software, hardware, streaming) lowercase mid-sentence per French orthography (Académie française + Grevisse §97). Capital only sentence-initial.

#### Spanish (RAE / Fundéu / AENOR UNE 50132)
1. Space between number and SI unit: 5V → 5 V, 220V → 220 V, 2.4GHz → 2.4 GHz. Exception: Q10 spec tokens.
2. USB3.0 → USB 3.0. Hyphenated connector types (USB-C, USB-A) keep hyphen.
3. Inverted opening punctuation `¿` `¡` mandatory: scan for closing `?`/`!` and add opener if missing.
4. `internet` lowercase mid-sentence and in headings (RAE 2014 / Fundéu).
5. Em-dash for parenthetical: `—texto—` (no internal spaces, RAE convention).
6. ASCII straight quotes for UI strings; ASCII for prose by default.
7. Decimal separator: keep `.` per Q10.
8. Apply Spanish two-class loanword casing (per Spanish Variant section).

#### Polish (PWN / Microsoft+Apple Polish style)
1. USB N.M with space: USB3.0 → USB 3.0. Do NOT split USB-C.
2. Em-dash flanked by single regular spaces for parenthetical: `słowo — słowo`. NOT hyphen, NOT en-dash.
3. Polish typographic quotes `„...”` for native Polish quoted text; ASCII straight quotes for UI-categorized strings.
4. Quoted UI status strings start with capital letter: `„Połączono, ale sieć jest niedostępna"`.
5. Prefer em-dash over semicolon for clausal interruption.

### Source Text Fidelity Exceptions
- Source typos: silently fix in translation, log to `_source-typos.md`
- Case inconsistency in source (e.g., `to` vs `To`): normalize to lowercase `to`, log
- Markdown structure: preserve byte-for-byte
- Source typographic artifacts (USB3.0 missing space, mid-clause line breaks): apply per-language typography pass per Decision Block 7; log fixes to `_source-typos.md`
```

This block is large but it is the **single source of truth** for every agent. Do not paraphrase it.

---

### Step 3: Launch Translation Agents in Parallel

Read the full translation rules from the sibling `translate-manual` command file. To locate it, try these paths in order until one resolves:

1. `${CLAUDE_PLUGIN_ROOT}/commands/translate-manual.md` — when running under a plugin install (env var set by Claude Code)
2. `~/.claude/plugins/cache/HS-Jack-YZY/data-team-skills/commands/translate-manual.md` — marketplace cache fallback
3. `.claude/commands/translate-manual.md` — local-project install
4. `commands/translate-manual.md` (relative to repo root) — dev-clone of `data-team-skills`

The "Translation Workflow", "Hardcoded Decision Blocks 1–7", "Translation Rules 1–7", and "Quality Checklist" sections of that file are the canonical source — paste them verbatim into each Step-3 agent prompt below; do not paraphrase. If none of the paths resolve, hard-stop and surface `ERROR: cannot locate translate-manual.md sibling file` to the user rather than silently proceeding with the Step 2c block alone.

For each target language, spawn 3 agents (**2 Sonnet + 1 Opus**) in a single message.

**Per-language agent configuration:**

| Agent | Model | Style brief | Output file |
|---|---|---|---|
| Agent-{Lang}-A | sonnet | **Faithful**: stay close to source structure, preserve original phrasing, conservative word choice | `{output-dir}/translation-A.md` |
| Agent-{Lang}-B | sonnet | **Idiomatic**: prioritize natural native flow, allow restructuring, native technical-writer phrasing | `{output-dir}/translation-B.md` |
| Agent-{Lang}-C | opus | **Polished**: highest quality native-level translation, balance accuracy and elegance, deeper judgment for nuanced sections | `{output-dir}/translation-C.md` |

Each agent's prompt MUST include:
1. Style Brief
2. Full content of `translate-manual.md` Translation Rules
3. The full Hardcoded Translation Decisions block from Step 2c verbatim
4. Full source document content
5. Output file path

Use this structure:

```
You are translating a GL.iNet product manual to {target language}.

## Style Brief
{Faithful / Idiomatic / Polished}

## Translation Rules
{paste full content of translate-manual.md rules section here}

## Hardcoded Translation Decisions (NEVER OVERRIDE)
{paste full Hardcoded Translation Decisions block from Step 2c}

These decisions have been confirmed by product team (v2.0) and specialist linguistic agents (v2.1) on 2026-04-29.
They take precedence over any general translation rule.

## Formatting Requirements
- Use the SAME heading/formatting style as source document
- Preserve EXACT document structure: same sections, same order, same spacing

## Source Document
{paste full source document content}

## Task
1. Read and understand source structure
2. Translate following ALL rules above; Hardcoded Decisions take priority
3. Apply v2.1 typography pass per target language (Decision Block 7)
4. Style Brief guides stylistic choices within constraints
5. Run quality checklist
6. Save result to: {output-file-path}

Output ONLY the translated document.
```

---

### Step 4: Per-Language Opus Merger

After all 3 translation agents for a language complete, spawn 1 Opus merger per target language. For multi-language runs, spawn all per-language mergers in a single message.

Each merger:
1. Reads rules + source + 3 candidates
2. Section-by-section best-of-3 selection
3. Verifies Hardcoded Decisions compliance (especially v2.1 items: Spanish sentence case, Polish Firmware fallback, per-language typography pass)
4. Saves Final + brief `_report.md`

Save Final as: `{output-dir}/{Product}-{TargetLangCode}-Final.md` (use the language **code** from the Step 1 table — e.g., `BE3600-Fr-Final.md`, not `BE3600-French-Final.md` — to stay consistent with the `{Product}-{SourceLangCode}2{TargetLangCode}/` directory scheme)

---

### Step 5: Cross-Language Consistency Coordinator (Opus, multi-language only)

For multi-language runs, spawn 1 Opus coordinator after all per-language mergers complete.

#### 5a. Coordinator agent prompt structure

```
You are the cross-language consistency coordinator for a GL.iNet multi-language manual translation.

## Your Inputs
- Final translations: {list of per-language Final files}
- English source: {source-file-path}
- Hardcoded Decisions block: {paste from Step 2c}

## Decision-by-decision checks
For EVERY decision item, verify each language handled it identically (where applicable):
- Brand/model/IP/URL occurrence counts must match across languages
- EU/UE per language: De keeps "EU", Fr/Sp/Pl use "UE"
- DoC bracket descriptor: byte-identical to any product-card occurrence within each language
- Numbers: no `2,5G` / `2,8 Zoll` / `Gbit/s` / `Zoll` / `pouces` (locale leak)
- System dialog buttons: localized per language (Verbinden / Rejoindre / Unirse / Dołącz)
- v2.1 Spanish: sentence case headings (NOT Title Case); `firmware` lowercase mid-sentence; `internet` lowercase
- v2.1 Polish: no apostrophe-declined forms (`Router'a`, `Firmware'u`); `Firmware` falls back to `oprogramowanie układowe` in oblique cases
- v2.1 Per-language typography: `USB 3.0` (not `USB3.0`); German `5 V`; French U+202F before `:?!»`; Polish em-dash flanked by spaces
- v2.1 Travel adjective: De=Reise- / Fr=de voyage / Sp=de viaje / Pl=podróżny

## Spot-check counts (must match across languages)
- Brand names, model numbers, IPs, fixed strings → identical occurrence count
- Headings count → match
- Numbered/bulleted list items → match
- `'Add a New Device'` (App label) → 1× per file
- `"Release to Reset Mode"` and `"Release to Repair Mode"` (touchscreen) → consistent count

## Action: when inconsistency found
Use Edit directly on offending Final file(s). Align to Hardcoded Decisions. If genuinely ambiguous, align to majority interpretation and flag.

## Re-verify after fixes.

## Save report to: {source-dir}/_cross-language-report.md
- Decision compliance table (rows = decisions, cols = languages)
- Inconsistencies found and how fixed
- Final occurrence counts of brand/model/fixed strings

Output ONLY "Done" after writing report and applying fixes.
```

#### 5b. Trust-but-verify
After "Done", main assistant briefly reads `_cross-language-report.md` and 1-2 touched Final files for spot-check.

---

### Step 6: Report

**The first line of this report MUST be**:

```
UNHANDLED CATEGORIES: N
```

where `N` is the number of entries logged to `_unhandled-categories.md` during this run (output `0` if the file is empty or absent). When `N > 0`, append on the same line: ` — STATUS: REQUIRES MAINTAINER REVIEW`. This makes the unhandled-category signal the loudest output, not a buried bullet.

Then provide a concise summary covering each target language:
- Which agent contributed most (A=sonnet/faithful, B=sonnet/idiomatic, C=opus/polished)
- Key A-vs-B-vs-C differences (from `_report.md`)
- v2.1 Hardcoded Decisions compliance: confirm each of Q19–Q24 was applied per `_cross-language-report.md`
- Cross-language inconsistencies the coordinator fixed
- Source typos and typography normalizations (`_source-typos.md`)
- Path to all output directories and Final files

---

## Agent Count Summary

For N target languages:
- Step 3: `3 × N` translation agents (parallel)
- Step 4: `N` per-language Opus mergers (parallel)
- Step 5: `1` cross-language coordinator (only N>1)

Total for N=4: 12 + 4 + 1 = **17 agents**.

---

## Decision Provenance

v2.0 (product team, 2026-04-29) + v2.1 (specialist agents: De Duden/DIN, Fr Académie/AFNOR, Sp RAE/Fundéu, Pl PWN, 2026-04-29).

详细决策审计文档由 maintainer 私存，未随 marketplace 分发。如需翻阅决策细节或就单条决策提出 clinic round 升级，联系 GL.iNet 数据组 maintainer。

If a future translation surfaces a case **not covered** by the decisions above:
1. Apply closest existing decision and proceed
2. Log to `_unhandled-categories.md`
3. Recommend follow-up Q in next clinic round (Tier 1 product team OR Tier 2 specialist agent)

Do NOT pause translation to ask the user.
