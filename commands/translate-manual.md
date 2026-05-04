---
name: translate-manual
description: >
  Translate GL.iNet product manuals (quick start guides, user manuals) from English to German,
  French, Spanish (Peninsular), or Polish. Hardcoded with v2.0 product-team-confirmed decisions
  for terminology, UI strings, formatting, compliance text, tone, and product names — plus v2.1
  specialist-confirmed linguistic decisions for case handling, native typography, and Slavic
  grammar interaction. Invoke this command (`/data-team-skills:translate-manual`) whenever the
  user asks to translate a product manual, even if they only mention 'translate' without
  specifying it's a manual — the rules here apply to any GL.iNet product documentation.
---

> **Spec metadata** — v2.1, effective 2026-04-29.
> - **Decisions**: v2.0 product team Q1–Q18 (business / brand / compliance / regional) + v2.1 specialist agents Q19–Q24 (linguistic competence, native typography, Slavic grammar)
> - **Linguist specialists**: De (Duden / DIN 5008) · Fr (Académie / AFNOR / Imprimerie nationale) · Sp (RAE / Fundéu / AENOR) · Pl (PWN / industry corpus)

# GL.iNet Product Manual Translation

Translate a product manual from English to the specified target language. **All decisions are hardcoded** — never ask the user to confirm UI handling, terminology, formatting, compliance, casing, or typography choices. Decisions come from two layers:

- **v2.0 (product team, 2026-04-29)**: business / brand / compliance / regional decisions (Q1–Q18)
- **v2.1 (specialist agents, 2026-04-29)**: linguistic competence — native case rules, RAE/Duden/PWN/AFNOR conventions, per-language typography (Q19–Q24)

Both layers apply unconditionally. v2.1 specialist authority overrides v2.0 only on linguistic-correctness questions where the product team's earlier judgment was made without RAE/Duden/PWN/AFNOR knowledge (notably: Spanish heading case reversed from Title Case to sentence case).

## Supported Target Languages

**Approved (v2.1 hardcoded decisions apply in full)**: German (De), French (Fr), Spanish-Peninsular (Sp), Polish (Pl).

**Other languages** (Italian, Japanese, Portuguese, etc.): apply structural rules + v2.0 business decisions only; v2.1 specialist linguistic rules are NOT approved. The orchestrator MUST log every such run to `_unhandled-categories.md` so the maintainer can decide whether to commission a specialist round for that language.

## Input: $ARGUMENTS

Expected format: `<source-file-path> <target-language>`

Example: `/translate-manual MT6000-English.md Spanish`

If no arguments provided, ask only for source path and target language. Do **NOT** ask about anything else — every other choice is pre-decided.

## Translation Workflow

1. **Read** the source file
2. **Identify** document sections (product name, warranty, setup, hardware labels, support, regulatory)
3. **Translate** applying Decision Blocks 1–7 as absolute constraints + Rules 1–7 as craft guidance
4. **Apply Rule 5d typography auto-fix pass** (per-language, mandatory before save)
5. **Self-check** against the Quality Checklist
6. **Save** as `<source-dir>/<source-name>-<lang>.md`
7. **Emit Final Report** with `UNHANDLED CATEGORIES: N` as its first line (see "Final Report" section near end of this file)

---

## 🔒 Hardcoded Decision Blocks (NEVER OVERRIDE)

> **Cross-file maintenance note**: Decision Blocks 1–7 below are duplicated (in a compressed form) inside `translate-compare.md` Step 2c's "Hardcoded Translation Decisions" block. Any edit to a decision here MUST be mirrored there — otherwise the multi-agent command will translate against stale rules. There is no automated parity check.

### Decision Block 1: Terminology Map (v2.0 Q1–Q4, Q17, Q18)

| English term | German | French | Spanish (Peninsular) | Polish |
|---|---|---|---|---|
| **Wi-Fi** | Wi-Fi | Wi-Fi | Wi-Fi | Wi-Fi |
| **Router** | Router | routeur | Router | Router |
| **Email** | E-Mail | E-mail | Correo | E-mail |
| **Firmware** | Firmware | Firmware | Firmware | Firmware (with v2.1 case-fallback per Polish — see sub-table below) |
| **SSID** | SSID | SSID | SSID | SSID |
| **LAN / WAN / USB / LED / IP / DHCP / DNS / VPN / OpenVPN / WireGuard / MAC / APN** | (keep English in all four languages) | | | |
| **Wi-Fi 7 / Wi-Fi 6 / 5G NR / 5G / 4G LTE / Nano-SIM / Bluetooth / QR Code / Ethernet / PCBA** | (keep English in all four languages) | | | |
| **Product names**: Flint 2, Mudi 7, Slate AX, Spitz AX, GL-E5800, GL-MT6000, GL-BE3600 etc. | (verbatim, never translate, never reorder) | | | |
| **Support URL**: link.gl-inet.com/... | (same English URL in every language version) | | | |

#### v2.1 — Polish Slavic case handling for kept-English nouns

| Term | Strategy | Example |
|---|---|---|
| **Router** | Decline as native masculine inanimate noun WITHOUT apostrophe: `Router` (Nom.), `Routera` (Gen./Acc.), `Routerowi` (Dat.), `Routerem` (Instr.), `Routerze` (Loc.). Capital R retained. | `panelu administracyjnego Routera`, `Podłącz Router do zasilania` |
| **Firmware** | Use `Firmware` (capitalized) ONLY in nominative case or as a UI/menu label. For all oblique cases, fall back to native `oprogramowanie układowe`. | Nom: `Firmware jest gotowy.` / Oblique: `oprogramowania układowego firm trzecich` (NOT `oprogramowania Firmware`) |
| **Wi-Fi / SSID / LAN / WAN / USB / LED / DHCP / DNS / VPN / MAC / APN** | Invariant. Use carrier noun for grammar. | `sieć Wi-Fi`, `do sieci Wi-Fi`, `port LAN`, `adres MAC`, `identyfikator SSID` |
| **Ethernet / Bluetooth** | Decline regularly without apostrophe. | `Ethernetu`, `Bluetootha`, `Bluetoothem` |
| **OpenVPN / WireGuard** | Brand-style; keep undeclined, decline carrier noun. | `protokół OpenVPN`, `przez WireGuard` |
| **Nano-SIM** | Compound; decline carrier noun. | `karta Nano-SIM`, `kartę Nano-SIM` |

**Forbidden in Polish**: apostrophe-declension of common-noun anglicisms (`Router'a`, `Firmware'u`, `Ethernet'em`). Apostrophe declension is reserved by PWN for personal proper nouns ending in a silent letter (`Mike'a`, `Steve'a`, `iPhone'a`) — it is wrong for `Router`, `Firmware`, `Ethernet`, etc.

### Decision Block 2: UI String Handling (v2.0 Q6–Q9)

| UI source | Handling | Quote style | Example |
|---|---|---|---|
| **Web admin panel** menu paths and labels | KEEP ENGLISH | ASCII `"..."` or backtick `Foo > Bar` | `Network > Ethernet Ports`, `MAC Mode`, `Clone` |
| **GL.iNet App** button names, screen titles | KEEP ENGLISH | ASCII single quotes `'...'` | `Tippen Sie auf 'Add a New Device'` |
| **Touchscreen display text** (E5800, X3000, XE3000) | KEEP ENGLISH | ASCII double quotes `"..."` | `"Release to Reset Mode"` (lowercase `to` enforced — Rule 5b) |
| **Physical printed text** on hardware (POWER / RESET / USB-C / PUSH) | KEEP ENGLISH | no quote modification | (verbatim) |
| **System-level dialog buttons** (iOS/Android Wi-Fi popup) | TRANSLATE per OS standard | ASCII single quotes `'...'` | German: `'Verbinden'`, French: `'Rejoindre'`, Spanish: `'Unirse'`, Polish: `'Dołącz'` |

**v2.1 scope clarification**: ASCII-quote rule applies ONLY to UI categories above. **Prose-quoted native-language text** (e.g., quoting a status string in flowing prose, defining a term in apposition, emphasizing a term) uses target-language native typography per Decision Block 7:
- French prose-quote: `« texte »` with U+202F inside both guillemets
- Polish prose-quote: `„texte"` (low-9 + high-9 pair)
- Spanish prose-quote: ASCII per stability lock (or `«...»` if downstream supports)
- German prose-quote: native `„texte"` per Duden but ASCII acceptable for cross-language stability

### Decision Block 3: Numbers and Capitalization (v2.0 Q10, Q11 + v2.1 Q21, Q23)

#### Numbers
- Keep English form across all languages: `2.5G`, `2.8"`, `1.2 GHz` — never localize to `2,5G` / `2,8 Zoll` / `2,5 Gbit/s` / `2,8 pouces`. Reasoning: matches the product spec sheet which is the source of truth.

#### Heading capitalization

| Language | Convention |
|---|---|
| **German** | Sentence case + all nouns capitalized per Duden §57 (`Nano-SIM-Karte einsetzen`). Kept-English nouns inherit this rule automatically. |
| **French** | Sentence case — only first word + proper nouns capitalized (`Installer la carte Nano-SIM`). |
| **Spanish (Peninsular)** | **Sentence case** — only first word + proper nouns + kept-English brand tokens capitalized (`Soporte técnico`, `Instalar la tarjeta Nano-SIM`, `Configurar el Router`). **v2.1 REVERSAL**: v2.0 used Title Case which is an Anglicism per RAE *Ortografía* §4.2.4.10.2 + Fundéu BBVA + Telefónica/Movistar/Amazon España corpus. Title Case in Spanish technical manuals signals incorrect localization. |
| **Polish** | Sentence case — only first word capitalized, EXCEPT kept-English tokens which retain capitalization. |

#### v2.1 — Cross-language kept-English token rule

Tokens listed in Decision Block 1 (Router, Wi-Fi, Firmware, Bluetooth, Ethernet, SSID, LAN, WAN, USB, LED, IP, DHCP, DNS, VPN, OpenVPN, WireGuard, MAC, APN, Nano-SIM, QR Code, PCBA, 5G, 5G NR, 4G LTE, Wi-Fi 7, Wi-Fi 6) are treated as **proper-noun-like product/spec anchors**. They retain their Decision-Block-1 canonical capitalization in **all positions** — sentence-initial, mid-sentence, mid-heading — regardless of surrounding heading-case or sentence-case rules.

**Examples** (correct):
- French heading: `Méthode 1 : configurer votre routeur via Wi-Fi` (sentence case + Wi-Fi cap)
- Spanish heading: `Conectar el dispositivo al Router` (sentence case + Router cap)
- Polish heading: `Konfiguracja Routera za pomocą panelu administracyjnego` (sentence case + Routera cap)

### Decision Block 4: Compliance / Legal Text (v2.0 Q12–Q15)

- **EU Directive numbering** (e.g., `Directive 2014/53/EU`):
  - German: keep `EU` → `Richtlinie 2014/53/EU`
  - French: localize to `UE` → `directive 2014/53/UE`
  - Spanish: localize to `UE` → `Directiva 2014/53/UE`
  - Polish: localize to `UE` → `dyrektywa 2014/53/UE`
- **DoC product descriptors in brackets** (e.g., `[5G NR Tri-band Wi-Fi 7 Portable Router, GL-E5800EU]`):
  - **Fully localize** the description; model number stays verbatim. Examples:
    - German: `[Tragbarer 5G NR Dreiband-Wi-Fi 7-Router, GL-E5800EU]`
    - French: `[Routeur portable 5G NR tri-bande Wi-Fi 7, GL-E5800EU]`
    - Spanish: `[Router portátil tribanda 5G NR Wi-Fi 7, GL-E5800EU]`
    - Polish: `[Przenośny router trójzakresowy 5G NR Wi-Fi 7, GL-E5800EU]`
  - **Cross-section consistency**: descriptor must be byte-identical to any product-card occurrence elsewhere.
- **German DoC compound formation order** (v2.1): `[Tragbar/Mobil if present] + [BandClass: Dualband/Dreiband] + [Wi-Fi standard] + [Use prefix: Reise- if Travel] + Router`. Hyphenate each foreign-origin element; preserve internal space of `Wi-Fi 7`. Example: source `[Dual-band Wi-Fi 7 Travel Router, GL-BE3600]` → `[Dualband-Wi-Fi 7-Reise-Router, GL-BE3600]`.
- **Product attribute adjectives**: fully localize per Rule 7c.
- **Warranty period clauses**: translate as-is. Do NOT introduce market-specific differentiation. Flag in `_unhandled-categories.md` that warranty wording is currently market-uniform pending future legal review.
- **Company name** (`GL TECHNOLOGIES (HONG KONG) LIMITED`): never translate, verbatim in all languages.

### Decision Block 5: Tone (v2.0 Q16)

All four languages use **formal address** throughout:

| Language | Pronoun |
|---|---|
| German | Sie / Ihr / Ihnen |
| French | vous / votre |
| Spanish (Peninsular) | usted / su |
| Polish | Pan / Pani / Państwo (or impersonal third-person where natural) |

Imperative form (German `Drücken Sie...`, French `Appuyez...`, Spanish `Pulse...`, Polish `Naciśnij...` — Polish uses second-person singular imperative even with formal noun-of-address; do NOT mix `Pan` with `Naciśnij Pan`).

### Decision Block 6: Spanish Peninsular Variant (v2.0 Q5 + v2.1 Spanish loanword two-class system)

#### v2.0 vocabulary discipline (LatAm avoidance)

Spanish translations target **Peninsular Spanish (Spain)**, not Latin American. Use:

| Concept | Use (Peninsular) | Avoid (LatAm) |
|---|---|---|
| computer | ordenador | computadora |
| video | vídeo (with accent) | video |
| game console | videoconsola | consola de videojuegos |
| laptop | portátil | laptop / computadora portátil |
| cell phone | móvil | celular |
| OK / fine | vale | bueno / okay |
| email | correo electrónico (or `Correo` per Decision 1) | email |

#### v2.1 — Spanish loanword two-class casing system

Spanish common nouns stay lowercase mid-sentence (RAE *Ortografía* §4.2.4: common nouns lowercase, including unadapted foreignisms). For kept-English tokens, distinguish two classes:

**Brand-style class** (always capitalized regardless of position):
`Wi-Fi`, `Bluetooth`, `Ethernet`, `Router`, `SSID`, `LAN`, `WAN`, `USB`, `LED`, `IP`, `DHCP`, `DNS`, `VPN`, `OpenVPN`, `WireGuard`, `MAC`, `APN`, `Nano-SIM`, `QR Code`, `PCBA`, `5G`, `5G NR`, `4G LTE`, `Wi-Fi 7`, `Wi-Fi 6`, `GL.iNet`, `GL-<model>`, `App Store`, `Google Play`.

**Common-noun class** (lowercase mid-sentence; capitalize only at sentence start):
- `firmware` — even though Q4 keeps the English token, Spanish RAE rule mandates lowercase as common noun
- `software`, `hardware`, `streaming`, `malware` — same
- `internet` — explicitly lowercase per RAE 2014 update / Fundéu

**Examples**:
- ✅ `Los problemas derivados del uso de firmware de terceros...`
- ✅ `Actualice el firmware del Router.`
- ✅ `Sin acceso a internet tras configurar el Router.`
- ❌ `Los problemas derivados del uso de Firmware de terceros...` (v2.0 BE3600 line 207 — incorrect)

### Decision Block 7: Per-Language Typography (v2.1 Q24)

Mandatory typography pass before save. Apply per target language:

#### German (DIN 5008 / DACH technical-writing convention)
1. Insert space between value and unit: `USB3.0` → `USB 3.0`, `2.5GHz` → `2.5 GHz`, `100m` → `100 m`, standalone `5V` → `5 V`. **Exception**: networking spec tokens (`2.5G`, `5G NR`, `4G LTE`, `Wi-Fi 7`) are excluded — Q10 prevails.
2. Collapse soft line break mid-clause (single `\n` inside one continuous clause without markdown role) into a single space.
3. Stray U+00A0 (NBSP) → regular space, except where DIN 5008 prefers NBSP between value and unit.

#### French (AFNOR NF Z 44-001 + Imprimerie nationale)
1. Insert U+202F (narrow no-break space) before `:`, `;`, `?`, `!`, after `«`, before `»`.
2. Insert U+00A0 between number+unit and inside inseparable expressions (`M. Dupont`, `n° 4`).
3. `USB3.0` → `USB 3.0` (AFNOR + USB-IF style).
4. Merge mid-clause line breaks (heuristic: line ends without terminal punctuation AND next line starts with lowercase).
5. Apostrophes in prose: ASCII `'` → curly `’` (U+2019). Exception: keep ASCII inside ASCII-quoted UI strings, URLs, code blocks.
6. Ellipsis: `...` → `…` (U+2026).
7. Em-dash with non-breaking spaces ` — ` for parenthetical inserts.
8. Prose-quoted French text uses guillemets `« »` (with U+202F inside); UI-categorized strings use ASCII per Decision Block 2.
9. **Common-noun loanword lowercase mid-sentence**: `firmware`, `software`, `hardware`, `streaming` lowercase mid-sentence per French orthography (Académie française *Dictionnaire* + Grevisse §97). Capital only sentence-initial.

#### Spanish (RAE + Fundéu + AENOR UNE 50132)
1. Insert space between number and SI unit: `5V` → `5 V`, `220V` → `220 V`, `2.4GHz` → `2.4 GHz`. **Exception**: Q10 spec tokens.
2. `USB3.0` → `USB 3.0`. Hyphenated connector types (`USB-C`, `USB-A`) keep hyphen.
3. Inverted opening punctuation `¿`/`¡` mandatory: scan for closing `?`/`!` and add opener if missing.
4. `internet` lowercase mid-sentence and in headings (RAE 2014 / Fundéu).
5. Em-dash for parenthetical: `—texto—` (no internal spaces, RAE convention).
6. ASCII straight quotes for UI strings (Decision Block 2 lock); ASCII for prose by default (downstream stability).
7. Decimal separator: keep `.` per Q10.
8. Apply Spanish two-class loanword casing per Decision Block 6.

#### Polish (PWN Słownik ortograficzny + Microsoft/Apple Polish style)
1. `USB N.M` with space: `USB3.0` → `USB 3.0`. Do NOT split `USB-C`.
2. Em-dash flanked by single regular spaces for parenthetical: `słowo — słowo`. NOT hyphen, NOT en-dash.
3. Polish typographic quotes `„...”` for native Polish quoted text; ASCII straight quotes for UI-categorized strings (Decision Block 2 lock).
4. Quoted UI status strings start with capital letter: `„Połączono, ale sieć jest niedostępna"`.
5. Prefer em-dash over semicolon for clausal interruption (Polish IT-manual house style).

---

## 🛠 Translation Rules

### Rule 1: Action headings use verb infinitives or concise action forms

For section headings describing an action (button, menu item, step name), use verb form:

| Language | Use (verb) | Avoid (noun) |
|---|---|---|
| Spanish | Reparar / Restablecer / Instalar | Reparación / Restablecimiento / Instalación |
| French | Réparer / Réinitialiser / Installer | Réparation / Réinitialisation / Installation |
| German | Reparieren / Zurücksetzen / Einsetzen | Reparatur / Zurücksetzung / Einsatz |
| Polish | Naprawa / Reset / Instalacja | (Polish nominal forms acceptable; verb is also fine) |

### Rule 2: No word-for-word translation — render meaning idiomatically

Translate what a native technical writer would write. Examples:

| Context | English | Avoid (literal) | Prefer (idiomatic) |
|---|---|---|---|
| Support intro | "If you have further questions" | Si tiene más preguntas | Si tiene más dudas |
| Support intro | "get help from the following ways" | obtener ayuda de las siguientes maneras | contactarnos en los siguientes medios |
| Contact channels | "ways" (contact methods) | maneras | medios / canales |

### Rule 3: Contact info uses "Label: Value" format

| Avoid | Use |
|---|---|
| `Envíe un correo electrónico a support@gl-inet.com` | `Correo: support@gl-inet.com` |
| `Send an email to support@gl-inet.com` | `Email: support@gl-inet.com` |

### Rule 4: Brevity — match English source length

No padding, no extra clarifications. If English is terse, translation must be terse.

### Rule 5: Source-text fidelity exceptions

#### 5a. Source typos: silently fix; log to `_source-typos.md`.
#### 5b. Source case inconsistency (`to` vs `To`): normalize to lowercase `to`; log.
#### 5c. Source markdown structure: preserve byte-for-byte (`**bold**` stays `**bold**`, `# heading` stays `# heading`, never swap).

#### 5d. Per-language typographic auto-fixes (v2.1, mandatory final pass before save)

Apply Decision Block 7 per target language. Every applied normalization logged in `_source-typos.md` for upstream source patching.

### Rule 6: Technical terms — stable across languages

Per Decision Block 1. Universal tokens (Wi-Fi, USB, IP, etc.) verbatim.

### Rule 7: Compliance text precision

#### 7a. Directive references: localize "Directive" word + per-language EU/UE per Decision Block 4.

#### 7b. DoC bracket descriptors: byte-identical to any product-card occurrence.

#### 7c. Product adjectives mapping (v2.1: Travel row added)

| English | German | French | Spanish | Polish |
|---|---|---|---|---|
| Portable | Tragbar / Tragbarer | portable | portátil | przenośny |
| Tri-band | Dreiband | tri-bande | tribanda | trójzakresowy |
| Dual-band | Dualband / Zweiband | bi-bande | doble banda | dwuzakresowy |
| Mobile | Mobil | mobile | móvil | mobilny |
| Compact | Kompakt | compact | compacto | kompaktowy |
| **Travel** | **Reise-** (compound prefix: `Reise-Router`) | **de voyage** (post-nominal: `routeur de voyage`) | **de viaje** (`router de viaje`) | **podróżny** (`router podróżny`) |

Rationale (v2.1 specialist consensus): each language's mapping is the established term in real consumer-electronics market corpus. `Mobile`/`Portable` collide with existing entries and erase the travel-class semantic — they are NOT acceptable substitutes for `Travel`.

---

## ✅ Quality Checklist (run before save)

- [ ] **Terminology Map** (Decision Block 1): each row's term in correct form for target language
- [ ] **UI Strings** (Decision Block 2): every quoted UI string verified against right category
- [ ] **Numbers** (Decision Block 3): no `2,5G` or `2,8 Zoll` — only `2.5G` and `2.8"`
- [ ] **Headings** (Decision Block 3): per-language convention; v2.1 — Spanish uses sentence case (NOT Title Case)
- [ ] **Kept-English tokens** (Decision Block 3 v2.1): Router/Wi-Fi/Firmware/etc. retain capitalization mid-heading and mid-sentence
- [ ] **Compliance** (Decision Block 4): EU/UE per language; DoC byte-identical to product card; company name verbatim
- [ ] **Tone** (Decision Block 5): consistent formal address
- [ ] **Spanish only — Decision Block 6 v2.0**: no LatAm vocabulary
- [ ] **Spanish only — Decision Block 6 v2.1**: `firmware` lowercase mid-sentence; `internet` lowercase
- [ ] **Polish only — Decision Block 1 v2.1**: no apostrophe-declined forms (`Router'a`, `Firmware'u`); `Firmware` falls back to `oprogramowanie układowe` in oblique cases
- [ ] **Typography pass** (Rule 5d / Decision Block 7): per-language typography auto-fixes applied
- [ ] **Source typos** silently fixed; logged in `_source-typos.md`
- [ ] **Markdown format** preserved byte-for-byte (Rule 5c)
- [ ] **Document structure** preserved
- [ ] **No added content**
- [ ] **Consistent terminology**

---

## 📝 Language-Specific Notes

### Spanish (Peninsular)
- See Decision Block 6 (v2.0 vocabulary + v2.1 two-class loanword casing).
- Formal `usted` form throughout.
- **Sentence case for headings** (v2.1 reversal): only first word + proper nouns + kept-English brand tokens capitalized. Title Case is an Anglicism per RAE/Fundéu.
  - Heading example: `Soporte técnico`, `Instalar la tarjeta Nano-SIM`, `Configurar el Router mediante el panel de administración web`.
- `firmware` lowercase mid-sentence (Spanish common-noun rule); `Router`, `Wi-Fi`, `Bluetooth` always capitalized.
- `internet` lowercase per RAE 2014.
- SI units spaced from numerals: `5 V`, `USB 3.0`. Networking spec tokens (`2.5G`, `5G NR`) keep closed form per Q10.
- Travel-router class → `de viaje` (e.g., `Router de viaje doble banda`). Do NOT use `portátil` or `de bolsillo`.
- Inverted opening punctuation `¿/¡` mandatory.

### French
- Formal `vous` throughout.
- Sentence case headings — only first word + proper nouns capitalized.
- Sentence case applies to French words; kept-English brand-style tokens (Wi-Fi, USB, LAN) retain canonical form.
- **Common-noun loanwords** (firmware, software, hardware) lowercase mid-sentence; capital only sentence-initial.
- Localize `Email` → `E-mail`, `Router` → `routeur`.
- Travel adjective: `de voyage` (post-nominal): `routeur de voyage`.
- EU directive: `directive 2014/53/UE` (lowercase `directive`, `UE`).
- DoC bracket word order: type → bandes → norme Wi-Fi → modèle. Example: `[Routeur de voyage bi-bande Wi-Fi 7, GL-BE3600]`.
- Apply French typography pass (Decision Block 7): U+202F before `:?!»`, after `«`; curly `’` in prose; em-dash with NBSP; ellipsis `…`.
- Prose quotations use guillemets `« »`; UI strings use ASCII per Decision Block 2.

### German
- Formal `Sie` throughout.
- All nouns capitalized per Duden §57 — kept-English nouns (Router, Wi-Fi, Firmware, App, E-Mail) inherit this rule automatically (no special clarification needed for headings).
- Compound nouns are normal: `Tragbarer 5G NR Dreiband-Wi-Fi 7-Router`.
- Localize `Email` → `E-Mail` (capital M, hyphen).
- EU directive: `Richtlinie 2014/53/EU` (German keeps `EU`, NOT `UE`).
- `Router` stays English.
- Travel adjective: `Reise-` (hyphenated compound): `Reise-Router`.
- DoC compound formation order (v2.1): `[Tragbar/Mobil] + [BandClass] + [Wi-Fi standard] + [Use prefix: Reise- if Travel] + Router`. Example: `[Dualband-Wi-Fi 7-Reise-Router, GL-BE3600]`.
- Apply German typography pass (Decision Block 7): unit spacing `USB 3.0`, `2.5 GHz`, `5 V`; soft-break collapse mid-clause.

### Polish
- Formal `Pan/Pani` for noun-of-address; verb forms use second-person singular imperative (standard manual convention) — do NOT mix.
- Sentence case headings, with kept-English tokens (Router, Wi-Fi, Firmware, Ethernet) retaining capitalization mid-heading.
- Localize `Email` → `E-mail`.
- EU directive: `dyrektywa 2014/53/UE` (lowercase `dyrektywa`, `UE`).
- **`Router` stays English AND declines without apostrophe** (Routera, Routerowi, Routerem, Routerze).
- **`Firmware` stays English ONLY in nominative or UI-label contexts**. For oblique cases, fall back to `oprogramowanie układowe` (e.g., `oprogramowania układowego firm trzecich`, NOT `oprogramowania Firmware innych producentów`).
- Apostrophe-declension (`Firmware'u`, `Router'a`) is **wrong** in Polish technical writing — never use.
- Polish typographic quotes `„...”` for native Polish text; ASCII straight quotes for UI-categorized strings (Decision Block 2).
- Em-dash `—` flanked by single spaces for clausal interruption; NOT hyphen, NOT en-dash.
- Travel adjective: `podróżny` (post-nominal): `router podróżny`. (Reserved — distinct from `mobilny` for cellular routers and `przenośny` for portable.)
- Apply Polish typography pass (Decision Block 7).

---

## Example Usage

```
/translate-manual /path/to/E5800-English.md Spanish
/translate-manual /path/to/E5800-English.md French
/translate-manual /path/to/E5800-English.md German
/translate-manual /path/to/E5800-English.md Polish
```

When invoked via plugin namespace:

```
/data-team-skills:translate-manual /path/to/E5800-English.md Spanish
```

## Output Files

For each translation produce:
- `<source-dir>/<source-name>-<lang>.md` — translated document
- `<source-dir>/_source-typos.md` (cumulative across runs) — source corrections + typography normalizations applied per Rule 5d
- `<source-dir>/_unhandled-categories.md` (cumulative; created on demand) — entries for novel UI categories, non-approved target languages, or warranty-class flags encountered during this run; consumed by the Final Report's `UNHANDLED CATEGORIES: N` first-line metric

---

## Decision Provenance

v2.0 (product team, 2026-04-29) + v2.1 (specialist agents: De Duden/DIN, Fr Académie/AFNOR, Sp RAE/Fundéu, Pl PWN, 2026-04-29).

详细决策审计文档由 maintainer 私存，未随 marketplace 分发。如需翻阅决策细节或就单条决策提出 clinic round 升级，联系 GL.iNet 数据组 maintainer。

If a future translation surfaces a case **not covered** by the decisions above:
1. Apply the closest existing decision and proceed
2. Log to `_unhandled-categories.md`
3. Recommend a follow-up Q in the next clinic round (Tier 1 product team OR Tier 2 specialist agent)

Do NOT pause translation to ask the user.

## Final Report

After saving the translated document, the post-translation summary returned to the user MUST start with:

```
UNHANDLED CATEGORIES: N
```

where `N` is the number of entries logged to `_unhandled-categories.md` during this run (output `0` if the file is empty or absent). When `N > 0`, append on the same line: ` — STATUS: REQUIRES MAINTAINER REVIEW`. After this line, briefly report: target language, output file path, and the source-typo / typography-fix count from `_source-typos.md`. This makes the unhandled-category signal the loudest output, not a buried tail comment.
