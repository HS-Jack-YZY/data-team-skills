---
name: manual-proofread
description: >
  GL.iNet 数据组英文产品手册校对器：把人工校对低效的英文源稿过一遍机器与规则可识别的错误
  （拼写 / 语法 / 全角标点 / 多余空白 / 空格丢失 / 术语规范 / UI 引号 / heading 大小写 /
  说明书惯用句式 you-please 收敛、被动转主动、verb-infinitive 起头）。一次性输出两份：
  **标注版** = markdown diff（`~~旧~~ **新**[^n]`）+ 文末脚注修改原因；**交付版** = 干净
  markdown，可直接喂给 translate-manual / translate-compare 走多语言翻译。术语锚词与 UI
  引号规则与 translate-manual.md Decision Block 1 / 2 共享单一来源。本 command 是英文手册
  → 多语言翻译流水线的**第 0 步**（与 translate-manual / translate-compare 形成同位语三件套）。

  仅在显式调用时触发：

  - /data-team-skills:manual-proofread <英文源稿路径> [--overwrite]
  - /manual-proofread <英文源稿路径>

  以下情况**不要触发**：
  - 翻译任务（→ translate-manual / translate-compare）
  - 写新章节、补缺失说明（→ html-report）
  - 中文 / 西语 / 任何非英语版本的校对（本 command 范围限定为英文产品手册）
---

# GL.iNet 英文产品手册校对器

把翻译团队收到的英文源稿（你或同事写的、待发往多语言流水线的 `*-Eng.md` / `*-English.md`）过一遍，把人工 review 抓不全也抓不快的机械错误一次性修掉，并保留每处修改的依据。

英文版本是整条多语言翻译流水线的源头。源头一个 typo（`Sey Up`、`0n your device`、全角冒号 `：`、`theReset` 粘连），下游 4–14 种语言会把它放大 4–14 倍——德语译者"忠实于源"会把 `Sey Up` 直接保留成 `Sey Up einrichten`，西语会出 `Sey Up el router`。本 command 不替代人工 review，而是把**机器规则可定的部分**先扫干净，让人工 review 集中在判断题上（语义 / 步骤完整性 / 安全提示是否充分）。

---

## Input: $ARGUMENTS

`<source-file-path> [--overwrite]`

**唯一必填参数**：英文源稿的 markdown 路径。除此之外不会问任何"要不要改大小写 / 要不要改引号 / 要不要保留全角标点"——所有规则都是 hardcoded（见下方决策块）。

**可选参数 `--overwrite`**：开启后交付版直接覆盖源文件，源文件先 `cp` 到 `<stem>.bak.md` 留底。默认**不**覆盖（作者可能仍在迭代源稿，强制覆盖会破坏工作流）。

如果无参数：
```
请提供英文源稿路径，例如：
/data-team-skills:manual-proofread /path/to/BE3600-Eng.md
```

---

## 输出

每次运行输出三个文件，统一落在源文件同目录：

| 文件 | 内容 | 用途 |
|---|---|---|
| `<stem>-annotated.md` | markdown diff：`~~旧~~ **新**[^n]`，文末脚注汇总修改原因 | 给原作者 review 用，能直接看清每处改了什么、为什么改 |
| `<stem>-final.md` | 干净版，无任何 diff 标记 | 直接喂给 translate-manual / translate-compare 或交付翻译团队 |
| `_proofread-log.md` | **累积**修改日志（同目录多次运行追加），按 5 个 pass 分类统计触发次数 | 长期识别高频错误模式 → 反向推动写作模板 |

**命名约定**：source 是 `BE3600-Eng.md`（stem = `BE3600-Eng`），输出 `BE3600-Eng-annotated.md` 和 `BE3600-Eng-final.md`。`-Eng` 后缀保留，便于下游 translate-manual 直接识别为英文源。

---

## 工作流：5 个 pass，按机械度从高到低

每个 pass 独立扫一遍全文，每处修改记一条 footnote。**不要把 5 个 pass 合并成一遍**——分 pass 的好处是修改原因清晰、回溯方便、Final Report 能按 pass 给统计。

**严格按 1 → 2 → 3 → 4 → 5 顺序**：
- Pass 1 修了 typo / 全角，后续 pass 在干净文本上工作
- Pass 2 修了术语，后续 pass 不需要再判断 `wifi` 是不是 `Wi-Fi`
- Pass 3 修了引号分类，Pass 4 不需要 worry heading 里的引号字符串
- Pass 4 修了 Title Case，Pass 5 在最终 case 上判断 verb infinitive 的祈使句开头是否合规
- Pass 5 最后做，因为它最易激进；前面 4 个 pass 帮 Pass 5 收敛了输入

不要重排——重排会让某些规则反复打架。

---

### Pass 1 — 机械错误（必改，无判断）

#### 1.1 拼写

LLM 自身的英文拼写能力已经覆盖绝大多数常规 typo。**重点是带着这些"GL.iNet 语料里历史出现过的真实笔误模式"去扫**：

| 历史观察过的 typo | 修正 | 模式 |
|---|---|---|
| `Sey Up` | `Set Up` | 字母位置颠倒（BE3600） |
| `0n your device` | `on your device` | 数字 0 误作字母 o（BE3600） |
| `Recieve` | `Receive` | i / e 顺序 |
| `seperate` | `separate` | a / e 混淆 |
| `accomodate` | `accommodate` | 双辅音遗漏 |
| `occured` | `occurred` | 同上 |
| `firmare` | `firmware` | 漏字母（typo 高发） |
| `defualt` | `default` | u / a 错位 |

扫描时**优先看动词 / 名词的实义词**；介词 / 冠词不容易拼错。

#### 1.2 数字 / 字母混淆

OCR 转录或键盘 typo 常见：

| 错 | 对 | 模式 |
|---|---|---|
| `0n` | `on` | 数字 0 → 字母 o |
| `l0` | `10` | 字母 l → 数字 1 |
| `O.K.` | `OK` | 字母 O 在 acronym 里大小写混乱 |

判断方法：句子里出现单独 `0` 或 `l` 时，看上下文是数字位还是单词位。

#### 1.3 空格

| 类别 | 规则 | 例子 |
|---|---|---|
| 粘连必加空格 | 单词与单词间必须有空格 | `theReset` → `the Reset`、`USBPort` → `USB Port` |
| 数字与单位 | 数字与 SI 单位间加空格 | `12V` → `12 V`、`100m` → `100 m`、`USB3.0` → `USB 3.0` |
| **数字与单位例外**（保留紧凑） | 网络规格 token | `2.5G`、`5G NR`、`4G LTE`、`Wi-Fi 7`、`Wi-Fi 6` —— 不动（与 translate-manual Q10 同源） |
| 连字符 | 不能拆 | `USB-C`、`Wi-Fi`、`Nano-SIM` —— 不要被空格规则误改成 `USB C` |
| 标点后空格 | 句号 / 逗号 / 冒号后必须空格 | `router,connect` → `router, connect` |
| 句末多空格 | 行末多余空格删除 | 行尾的 trailing whitespace 全部清掉 |

#### 1.4 重复词

英文里相邻重复同一个词通常是错（除少数例外如 `had had`）：`the the router` → `the router`、`to to connect` → `to connect`、`and and` → `and`。

#### 1.5 全角 → 半角对照

| 全角 | 半角 |
|---|---|
| `：` (U+FF1A) | `:` |
| `，` (U+FF0C) | `,` |
| `。` (U+3002) | `.` |
| `！` (U+FF01) | `!` |
| `？` (U+FF1F) | `?` |
| `；` (U+FF1B) | `;` |
| `（` `）` (U+FF08/U+FF09) | `(` `)` |
| `【` `】` (U+3010/U+3011) | `[` `]` |
| `"` `"` (U+201C/U+201D) | `"` |
| `'` `'` (U+2018/U+2019) | `'` |

**例外**：英文文本里的 `—` (em-dash, U+2014) 是合法标点，不要改成 hyphen `-`。出现在数字范围（如 `2024–2025`）时是 en-dash (U+2013)，也保留。

#### 1.6 NBSP / 全角空格清理

| 字符 | Unicode | 处理 |
|---|---|---|
| 不间断空格 NBSP | U+00A0 | 替换为普通空格 |
| 全角空格 | U+3000 | 替换为普通空格，或视位置删除 |
| 窄不间断空格 | U+202F | 在英文文本里替换为普通空格（这是法语 typography） |
| Em / En space | U+2003 / U+2002 | 替换为普通空格 |

#### 1.7 多余空白行

连续空白行（含全角空格行）合并为单个 markdown 段落分隔。**保留**标题前后的空行（markdown 渲染需要）和列表项之间作者刻意加的空行。

#### 1.8 markdown 转义错位

最高发：`**bold****：` 这种 markdown bold 与中文标点相邻产生的转义混乱。

```
错: **Method 2****： Set Up Your Router
对: **Method 2:** Set Up Your Router
```

判断方法：连续 4 个 `*` 或 `**` 与文本紧贴的位置，几乎都是错。

---

### Pass 2 — 术语规范

**单一来源**：`commands/translate-manual.md` Decision Block 1。运行时读这份文件，定位 "Decision Block 1: Terminology Map" 章节，把英文列里的标准写法当作权威。

#### 2.1 校对动作

读完 Decision Block 1 后，对源稿做以下扫描：

1. 全文搜索每个 brand-style token 的所有可能错写法。例如对 `Wi-Fi`：搜 `wifi` / `Wifi` / `WIFI` / `Wi-fi` / `wi-fi` / `WiFi`，全部改为 `Wi-Fi`
2. 对 `Router`：扫 heading 和品牌 / spec 位置的 `router` / `Router`，确认大小写正确
3. 对 `Nano-SIM`：扫 `nano-sim` / `nano sim` / `Nano SIM` / `NanoSIM`，统一为 `Nano-SIM`
4. 对 `5G NR`：扫 `5GNR` / `5G-NR` / `5g nr`，统一为 `5G NR`

#### 2.2 常见困惑点

| 词 | mid-sentence | heading |
|---|---|---|
| `Wi-Fi` | `Wi-Fi`（永远） | `Wi-Fi`（永远） |
| `router` | 取决于上下文（普通名词 lowercase；品牌锚词 `Router`） | Title Case 通常 `Router` |
| `Email` | `email`（普通名词） | Title Case `Email` |
| `firmware` | `firmware`（英文普通名词，lowercase） | Title Case `Firmware` |
| `internet` | `internet`（小写，与 RAE 2014 / Microsoft Style 一致） | Title Case `Internet` 或保留 `internet` 都可，注意一致性 |

#### 2.3 明确技术语义升级（Pass 2 范围而非 Pass 5 风格）

下列改动是**明确的技术名词修正**，不是风格主观偏好——所以归入 Pass 2 而非 Pass 5：

| 错（日常用语） | 对（技术准确） | 理由 |
|---|---|---|
| `Internet cable` | `Ethernet cable` | 物理电缆类型叫 Ethernet（IEEE 802.3）/ RJ45，不叫 Internet。Internet 是网络层概念。手册描述插入 LAN/WAN 端口的物理电缆时，必须用 Ethernet cable。 |
| `LAN cable` | `Ethernet cable` | 同上。LAN 是网络拓扑概念。`LAN port` 是对的（端口位置），`LAN cable` 不准确。 |
| `power line` / `power wire` | `power cable` 或 `power cord` | 设备充电线在英文手册里是 cable / cord。 |
| `the wifi signal is weak` | `the Wi-Fi signal is weak` | 已在 Decision Block 1，列在这里只为提醒 Pass 2 这一类术语规范属于"自动改"而非"问作者"。 |

**判断启发**：如果一个改动能引用 IEEE / RFC / 厂商规范作依据，归 Pass 2；如果是"读起来更顺 / 更专业感觉"，那是 Pass 5。

#### 2.4 不改

- 在引号 / 代码块里的字符串（已是字面量，不动）
- 产品型号 `GL-MT3600BE` / `GL-E5800` 等（永远 verbatim）
- URL 中的字符串（永远 verbatim）

---

### Pass 3 — UI 引号一致性

**单一来源**：`commands/translate-manual.md` Decision Block 2。

#### 3.1 5 类 UI 字符串的识别启发

| UI 类别 | 上下文识别 | 正确引号（英文源） |
|---|---|---|
| Web admin panel 路径 | 含 `>` 分层符号、含 admin panel 菜单名（Network / Firewall / System / Wireless / MAC Mode / Clone / Modem 等） | ASCII 双引号 `"..."` 或 backtick |
| App 按钮 / 屏幕名 | 上下文出现 `the GL.iNet App` / `tap` | ASCII 单引号 `'...'` |
| 触屏文字 | 上下文出现 `display` / `screen` / `touchscreen`，型号是 E5800 / X3000 / XE3000 | ASCII 双引号 `"..."`，引号内 `to` 必须 lowercase |
| 物理印刷 | `POWER` / `RESET` / `USB-C` / `PUSH` 出现在 hardware 描述段 | 不加引号 |
| 系统弹窗按钮 | `'Join'` / `'Connect'` / `'Trust'` | ASCII 单引号 |

#### 3.2 校对动作

| 错 | 对 | 类别 |
|---|---|---|
| `Tap "Add a New Device"` | `Tap 'Add a New Device'` | App 按钮（应单引号） |
| `Go to 'Network > Ethernet Ports'` | `Go to "Network > Ethernet Ports"` | admin panel（应双引号） |
| `"Release To Reset Mode"` | `"Release to Reset Mode"` | 触屏，`to` 必须小写 |
| `the "POWER" port` | `the POWER port` | 物理印刷不加引号 |
| `tap "Join"` | `tap 'Join'` | 系统弹窗按钮 |

#### 3.3 ambiguous 标记

如果实在判断不出某个引号字符串属于哪一类（典型场景：UI 字符串脱离上下文），**不要瞎改**。在 `_proofread-log.md` 增加一条：

```markdown
**Ambiguous UI quote**: line 47 `"Connect"` —— 无法确定属于 App 按钮（应单引号）还是触屏文字（应双引号）。请作者确认。
```

---

### Pass 4 — Heading 大小写

英文产品手册 heading 用 **Title Case**（与 Spanish / French / Polish 的 sentence-case 不同；这是英文惯例）。

#### 4.1 lowercase 词清单（≤4 字母 且 是介词 / 冠词 / 连词）

以下词在 Title Case heading 中**必须 lowercase**（除非是 heading 的第一个词）：

```
a, an, the
and, or, but, nor, for (并列连词)
to, of, in, on, at, by, with, from, into, onto, over, under
as, if, so
via, per
```

**注意**：
- `for` 作介词 / 并列连词都 lowercase
- `up`, `out`, `off`, `down`, `over`, `under` 等做副词时 **uppercase**（这与做介词时不同）
  - `Set Up Your Router`（`Up` 是 `Set Up` 的 phrasal verb 一部分，uppercase）✅
  - `Set Up Router via Web Panel`（`via` 是介词，lowercase）✅

#### 4.2 永远 uppercase

- 句首词
- ≥4 字母的实词（含动词、名词、形容词、副词）
- kept-English 全大写品牌 / spec 锚词（USB / LAN / WAN / SSID / VPN / DHCP / DNS / IP / MAC / APN / LED / SIM / NFC / GPS）
- 产品型号（GL-MT3600BE / E5800 等）

#### 4.3 经典对照

| 错 | 对 |
|---|---|
| `Set Up Your Router Via The Web Admin Panel` | `Set Up Your Router via the Web Admin Panel` |
| `Connect To Wi-Fi` | `Connect to Wi-Fi` |
| `Configure The Router And The Modem` | `Configure the Router and the Modem` |
| `Set Up Router With QR Code` | `Set Up Router with QR Code` |

#### 4.4 不改

- 已经全部大写的章节标题（如 `**OVERVIEW**` / `**SETTING UP**`）—— 这是作者刻意的视觉强调。但要确认全大写是否一致——如果混用，列入 ambiguous。
- 列表项的"小标题"（粗体 + 缩进）—— 步骤名按 Pass 5 处理 verb infinitive；描述性名词短语 Title Case。
- 触屏文字（已在 Pass 3 处理）

---

### Pass 5 — 说明书惯用句式（Microsoft Manual of Style + Apple Style Guide）

#### 总原则：高置信度才改

Pass 5 是 5 个 pass 里**唯一有主观判断成分**的。错改一处不通顺的句子比漏改一处更糟糕——前者破坏作者意图，后者只是少改一点而已。所以默认偏保守：

> **如果你不能用一句话说清楚为什么这样改更好，就不要改。**

每处 Pass 5 修改在 footnote 里必须能填出 reason，且 reason 要落到下面五条 idiom 里的某一条。如果你的 reason 是"读起来更顺"或"更专业"——那就是不该改的信号。

#### Idiom 1：祈使句开头（步骤说明）

操作步骤的句子用**祈使句**起头：动词原形 + 宾语。说明书的步骤是命令读者执行某个动作——祈使句最直接、最简短、最不模糊。

**必改**：

| 改前 | 改后 |
|---|---|
| `You should press the Reset button` | `Press the Reset button` |
| `Please press the Reset button` | `Press the Reset button` |
| `You can press the Reset button`（必需操作） | `Press the Reset button` |
| `It is necessary to press the Reset button` | `Press the Reset button` |
| `The user should press the Reset button` | `Press the Reset button` |

**不改**：
- 描述性陈述句（不是步骤命令）：`The router has four LAN ports.` ← 保留
- 真正的可选操作：`You can also configure the router via the GL.iNet App.` ← `you can` 此处表"还可以"
- 安全 / 警告条款：`Do not expose the device to direct sunlight.` ← 已是祈使句，但出现在 ⚠ 警告框里，**不动任何措辞**（compliance 性质）

#### Idiom 2：被动转主动

**必改**（句子有明确施事者时）：

| 改前 | 改后 |
|---|---|
| `The Reset button should be pressed and held for 3 seconds.` | `Press and hold the Reset button for 3 seconds.` |
| `The QR code can be scanned to connect.` | `Scan the QR code to connect.` |

**不改（被动是对的）**：
- `Settings are saved automatically.`（施事者是系统）
- `The device is certified to comply with FCC regulations.`（compliance 文本）
- `Power consumption is rated at 12 W.`（规格陈述，被动是惯例）
- `The default password is printed on the bottom of the router.`（描述客观状态）

#### Idiom 3：冗余收敛

| 啰嗦 | 简洁 |
|---|---|
| `in order to` | `to` |
| `due to the fact that` | `because` |
| `at this point in time` | `now` |
| `a total of N` | `N` |
| `utilize` | `use` |
| `prior to` | `before` |
| `subsequent to` | `after` |
| `in the event that` | `if` |
| `for the purpose of` | `to` 或 `for` |
| `with regard to` | `about` 或 `for` |
| `make a decision` | `decide` |
| `provide assistance to` | `help` |

**不改**：法律 / 合规文本（`in accordance with Directive 2014/53/EU` 不要改成 `under Directive...`）；引号里的 UI 字符串。

#### Idiom 4：长句拆分

> 30 词且含两个以上独立分句的句子，拆成两到三个短句。每句一个动作 / 一个事实。

| 改前（38 词） | 改后（拆成 3 句） |
|---|---|
| `Once you have connected your router to the power supply and waited for the LED indicator to turn green, you can scan the QR code printed on the bottom of the router using your phone's camera to connect to the Wi-Fi network automatically.` | `Connect your router to the power supply. Wait for the LED indicator to turn green. Scan the QR code on the bottom of the router with your phone to connect to the Wi-Fi network.` |

**不改**：法律条款（律师故意的长句）；已在编号列表里的步骤句（编号本身承担拆分）；一气呵成的描述性 inline 列举。

#### Idiom 5：Step 起头用 verb infinitive

编号步骤的开头要用动词原形，不要用动名词或名词化形式：

| 改前 | 改后 |
|---|---|
| `1. Pressing and holding the Reset button.` | `1. Press and hold the Reset button.` |
| `2. The connection of the router to power.` | `2. Connect the router to power.` |
| `3. Scanning the QR code with your phone.` | `3. Scan the QR code with your phone.` |

**不改**：章节标题（标题用 Title Case 名词短语或动词原形都行）；描述性图注。

#### Pass 5 禁忌区（整段跳过）

以下段落 Pass 5 **整段不进入**，只让 Pass 1–4 处理：

1. **Compliance / Regulatory 段**——含 `Directive 20XX/XX/EU` / `Declaration of Conformity` / `DoC` / `FCC` / `CE` / `RoHS` / `WEEE` / `GL TECHNOLOGIES (HONG KONG) LIMITED` / `warranty period` / `RF exposure` / `SAR` 等
2. **法律 / 隐私段**——含 `privacy policy` / `terms of service` / `liability` / `indemnify`
3. **第一人称品牌口吻**——含 `We recommend` / `We strongly suggest` / `At GL.iNet`
4. **引号内的所有文本**——已在 Pass 3 处理；Pass 5 永不进入引号
5. **代码块**—— ` ``` ` 围栏块和行内 backtick

#### Pass 5 自检（每次改动前 4 项）

1. 这处修改的 reason 能否落到 5 条 idiom 里的某一条？不能就**不改**
2. 这一段是否在禁忌区？是就**不改**
3. 改完之后，原作者会同意这是改进吗？（不是"我觉得更好"——是"原作者会认为这是 typo 纠正"）。只是风格偏好就**不改**
4. 改了之后，下游翻译 agent 翻成德 / 法 / 西 / 波时，会不会把这处修改当作"语义变化"误读？有风险就**不改**

通过 4 项才落到 `<stem>-annotated.md` 里。

---

## 标注版的 diff 格式

### 基础格式

每处修改用以下格式之一：

```markdown
Press and hold ~~theReset~~ **the Reset**[^3] button.
```

```markdown
Method ~~2：~~ **2:**[^7] Set Up Your Router
```

文末汇总：

```markdown
---

## Proofread Notes

[^3]: Pass 1 · 空格丢失（the + Reset 之间漏空格）
[^7]: Pass 1 · 全角冒号 `：` → 半角冒号 `:`
[^9]: Pass 4 · Heading Title Case 修正：`via` / `the` 在 Title Case 中应小写
```

**脚注编号策略**：从 1 开始，按出现顺序自增。**不要**按 pass 分段重置；连续编号便于作者跳转。

**纯删除**：`~~多余的词~~`（删除线 + 不附粗体新词）。footnote 注明 `Pass 5 · 冗余删除`。

**纯插入**：`**新增的词**[^n]`（粗体 + 不附删除线）。footnote 注明 `Pass 1 · 缺失冠词`。

### 处理 markdown 标记内的 diff（重要）

当需要 diff 的内容**已被** `**bold**` / `*italic*` 包裹时，**不要在标记内部嵌套 `~~`/`**`** —— 嵌套会破坏 markdown 解析。

**典型陷阱**：原稿是 `**Method1: Sey Up Your Router**`（整行 bold heading），错的做法：

```markdown
错: **~~Method1: Sey Up~~ **Method 1: Set Up**[^3] Your Router**
        ↑ bold 内嵌套 ** 会让渲染器把它解析成 "关闭 bold + 开启新 bold"，破坏原意
```

**正确做法**：把 diff 作用域拉到 bold 外，原行整体加删除线，新行整体保留 bold 并附脚注：

```markdown
对: ~~**Method1: Sey Up Your Router**~~
    **Method 1: Set Up Your Router**[^3]
```

**判断启发**：

| 原文 markdown 结构 | diff 处理方式 |
|---|---|
| 整行被同一对 `**` / `*` 包裹 | 整行拆成两行：原行加 `~~...~~`，新行加 `**...**[^n]` |
| 行中只有一小段 bold | bold 标记保留在新词周围，diff 在 bold 外可以正常做 |
| ` ``` ` fenced code 块 | 不修改块内内容；如确有错（罕见），在块前加注释 `<!-- 注：第 N 行 ... -->` |
| 行内 ` `` ` 反引号代码 | 整段 backtick 字符串当字面量，要么不改要么整段替换并在脚注说明 |
| `# heading` | `#` 不与 `**` 嵌套冲突，可以正常在 heading 行内做 diff |
| 表格单元格 `\| ... \|` | 单元格内可正常 diff，但行内不要超过 1 处修改（多处会让单元格视觉混乱） |

**规则的本质**：markdown 不允许同种符号（`**` / `*`）嵌套自己。`~~` 不与它们冲突，所以 `~~` 加在 `**bold**` 外面 OK。冲突只发生在"已 bold 段落里再开 bold"——这就是 line 54 这类 bug 的成因。

---

## Final Report 格式

校对完成后，给用户的终端摘要 **必须**以这一行开头：

```
MODIFICATIONS: N
```

`N` 是本次运行的总修改数。然后接以下结构：

```
MODIFICATIONS: N

📁 输出文件
- 标注版：<source-dir>/<stem>-annotated.md
- 交付版：<source-dir>/<stem>-final.md
- 累积日志：<source-dir>/_proofread-log.md

📊 按 pass 分布
- Pass 1 机械错误：    a 处
- Pass 2 术语规范：    b 处
- Pass 3 UI 引号：     c 处
- Pass 4 Heading：     d 处
- Pass 5 句式优化：    e 处

⚠️ 需作者确认
（如果有 ambiguous-ui-quote 或可能歧义的修改，列在这里；否则写"无"）

🔁 高频问题（>3 次）
（如果某类错误在本文件触发 ≥3 次，列出来，建议作者改写作模板；否则省略此段）
```

把 MODIFICATIONS 数放第一行的理由：作者一眼能看出"今天改了 5 处还是 50 处"，自动决定是 review 一下就发翻译，还是要回炉重写。

---

## `_proofread-log.md` 累积日志格式

同目录多次运行 append 到这一份文件。每次运行追加一段，结构：

```markdown
## 2026-05-08T14:30:00+08:00 · BE3600-Eng.md

| pass | from | to | reason |
|---|---|---|---|
| 1 | `Sey Up` | `Set Up` | 拼写 |
| 1 | `theReset` | `the Reset` | 空格丢失 |
| 1 | `2：` | `2:` | 全角冒号 |
| 4 | `Set Up Your Router Via The Web Admin Panel` | `Set Up Your Router via the Web Admin Panel` | Title Case 介词冠词小写 |
| 5 | `You should press the Reset button` | `Press the Reset button` | 祈使句去 you-should |

**汇总**：Pass 1 = 12 · Pass 2 = 3 · Pass 3 = 1 · Pass 4 = 5 · Pass 5 = 4 · 总计 25
```

时间戳用 ISO-8601 + 系统时区。多次运行的目的是积累"高频错误模式"的统计，便于回头改写作模板。

---

## 决策来源与同步

- **Pass 1**：本 command 自维护
- **Pass 2 术语**：单一来源 = `commands/translate-manual.md` Decision Block 1。运行时读取，不在本 command 内复制
- **Pass 3 UI 引号**：单一来源 = `commands/translate-manual.md` Decision Block 2。同上
- **Pass 4 Heading**：英文 Title Case 是本 command 自有规则（与 translate-manual 5b `to`-lowercase 规则同源，但英文用 Title Case 而非 sentence case，所以不能直接 reuse）
- **Pass 5 句式**：本 command 自维护

如果将来 translate-manual.md 的 Decision Block 1 / 2 增删了术语 / UI 类别，本 command **自动跟着新版本走**（运行时读最新版），不需要同步改本 command。这是相比 `translate-compare.md` 现有"双轨手动镜像"模式的改进。

---

## 不在本 command 范围（明确划界）

- ❌ 改写章节结构、补充缺失步骤、合并冗余章节 → 让作者自己改
- ❌ 校对中文 / 西语 / 德语 / 任何非英语版本 → 翻译版的校对走 translate-compare 内部的 Opus merger
- ❌ 给图表 / 插图 / 物理布局图加说明 → 不是文本范畴
- ❌ 更新 EU Directive 编号 / DoC 描述 / company 名 → compliance 文本只校对全角标点和拼写，措辞不动
- ❌ 写 commit message / PR 描述 → 走 commit-commands 系列

---

## 故障排除

| 问题 | 原因 | 处理 |
|---|---|---|
| 修改了 compliance 段落的措辞 | Pass 5 误触发 | 在 Pass 5 实施前先识别 compliance 段（含 "Directive 20XX/XX/EU" / "GL TECHNOLOGIES" / "warranty" / "DoC"），整段跳过 Pass 5 |
| 删了原作者真心想要的全角符号（艺术性引用） | 文化 / 风格内容误判 | 列入 ambiguous，写入 `_proofread-log.md` 让作者确认 |
| `final.md` 把 markdown 结构改坏（表格 / 代码块） | diff 处理逻辑没保护 fenced block | 处理 `~~old~~ **new**` 时跳过 ` ``` ... ``` ` 和 `\| ... \|` 行 |
| `annotated.md` 里 bold heading 的 diff 渲染乱 | 在 `**...**` 内嵌套了 `~~`/`**` | 按"标注版的 diff 格式 → 处理 markdown 标记内的 diff" 章节，整行替换为 `~~**old**~~` + `**new**[^n]` 两行 |

---

## 与 translate-manual / translate-compare 的关系

```
英文源稿 (作者写的 *-Eng.md)
    │
    ▼
[Step 0] /manual-proofread <source>        ← 本 command
    │   生成 *-Eng-final.md（干净交付版）
    ▼
[Step 1] /translate-manual <source> <lang>   ← 单 agent 翻译
    或
[Step 2] /translate-compare <source> <lang...> ← 多 agent 翻译 + 跨语言协调
    │
    ▼
多语言交付包 (*-De.md / *-Fr.md / *-Sp.md / *-Pl.md)
```

Step 0 是**可选**的——但强烈推荐在 Step 1 / 2 之前先跑，可以避免英文源的 typo / 全角标点 / spec token 错被放大到下游 4–14 种语言。
