# DECK-ECOSYSTEM — what creators actually use (research report, 2026-07-20)

*Three parallel web briefs, findings verified against live official sources
(Elgato Marketplace listing JSON, developer sites, plugin docs) fetched
2026-07. Verification legend: **[V]** = fetched from the official page;
**[S]** = search-snippet only (help.elgato.com is Cloudflare-walled);
**[U]** = unconfirmed, do not build on it. Reddit and Blackmagic forum
bodies were crawler-blocked throughout — community claims come from
independent editor blogs, not forums.*

**Why this report exists:** Ryan rejected the bespoke Companion text-tile
deck design (2026-07-20). Directive: Elgato-native first — official
plugins, Marketplace profiles, real key artwork on the mini-screens;
bespoke only where the ecosystem can't reach. REPORT BEFORE BUILD: nothing
below is wired until Ryan reads this and picks.

---

## Part 1 — OBS: the ecosystem is strong here

**The official Elgato "OBS Studio" plugin** (free, v3.0.3.31, Jun 2026,
~1.2M downloads, macOS 13+, Stream Deck app 6.9+) **[V]**:

- Actions: Record start/stop + pause · Stream · Scene switch · Scene
  Collection · Source show/hide · Mute · Media control · Studio Mode ·
  Preview Scene · Filter toggle · Screenshot · Transition · Replay Buffer
  + Save Replay · Virtual Camera · Profile switch · Audio-mixer volume ·
  **Chapter Marker (insert during recording; needs OBS 30.2+)**. **[V]**
- **Live state on keys is official and real**: "Your keys update live — so
  you always know what's muted, what's recording, and what's on screen."
  Scene/source keys have on/off states; actions auto-title from the scene
  name. **[V]** (Exact colors, e.g. "REC turns red," are not documented —
  appearance changes, form unspecified. **[S]**)
- **When OBS is not running**: keys enter a "Waiting for OBS" condition;
  pressing one shows a yellow warning triangle; keys resync automatically
  a few seconds after OBS launches. **[S]** This natively solves the 7/13
  press-REC-into-dead-OBS incident.
- **No launch-OBS action in the plugin** — but the Stream Deck app's
  built-in "Open Application" system action launches apps, and a Multi
  Action can chain launch → wait → scene. **[S/V]**
- Stability note: the 3.x line had a rewrite then a revert-release for a
  scenes-not-loading regression; OBS major updates have broken the plugin
  for windows of time historically. Pin versions; don't auto-update mid
  production. **[V]**

**THE CHAPTER MARKER FINDING (biggest architectural win):** the official
plugin can drop a chapter marker into the recording *while OBS records* —
exactly what the blessed bespoke MARK key was for. OBS writes chapters
into Hybrid MP4; ffprobe reads chapters. If verified on our rig, the MARK
key becomes a **native plugin key** and the daemon `mark` verb is never
built — ingest just reads chapter markers from the file and emits Story IR
markers. **[V that the action exists; U that chapters survive our exact
Hybrid-MP4 → ffprobe → ingest path — verify with ONE test recording before
building ingest support.]**

**Smart Profiles** (native): the deck auto-switches to a chosen profile
when an app gains focus — OBS profile appears when OBS is focused, Resolve
profile when Resolve is. Caveat: auto-switching pauses while the Stream
Deck config window is open. macOS support demonstrated by third-party
walkthroughs; Elgato's own article is platform-silent. **[V/S]**

**OBS profiles/icon packs on the Marketplace**: Aetheon OBS Profile Pack
$8.50 (MK/Mobile/Neo — **XL not listed**), Aetheon OBS Icon Pack $5 (83
icons with on/off variants, device-agnostic), StreamSpell Marathon $30
(XL listed; Windows tag), falbart Live Production icons free. Profiles are
device-layout-specific; icon packs are not. For an XL, expect to build the
OBS page ourselves from official plugin actions + a good icon pack — which
is fine: that's key assignment, not bespoke engineering. **[V]**

**Official plugin vs Bitfocus Companion (honest gap list)** **[V]**:
Companion's OBS module has ~50 more actions (source transforms, text
set, raw websocket requests), live variables on keys (record timecode,
bitrate, dropped frames, CPU), and preview-vs-program tally styling.
The official plugin has none of that — fixed actions + state icons. If a
key ever needs record-timecode-on-key or bitrate warnings, that's
Companion territory (or a custom plugin). For scene cuts + honest REC +
chapter markers — the actual blessed scope — the official plugin covers it.

## Part 2 — DaVinci Resolve: there is no plugin, only keystroke profiles

**Headline: no official or deep-integration Stream Deck plugin for Resolve
exists anywhere.** The entire Marketplace ecosystem is **profiles** —
pre-mapped keyboard-shortcut layouts with icon sets. **[V]**

- **How they work: keystroke emulation, full stop.** SideshowFX requires
  US-English QWERTY and installs its own Resolve shortcut preset; keys
  only reach what has a keyboard shortcut; Resolve must have focus; no
  state ever flows back to the deck. **[V]**
- **SideshowFX** (the dominant developer) **[V, prices from their site]**:
  - XL Pro Profiles v5.0 (May 2026, Resolve 21): $34.99 — 53 pages,
    5,000+ icons, ~1,400 commands, all Resolve pages.
  - XL Edit: $19.99 — Edit page only, 6 pages / 168 keys.
  - DaVinci FX: $14.99 — applies 415 effects/transitions to selected clip.
  - Color Panel XL (Mac) v3.0: $44.99 — the one "deeper" product, and
    it's a **mouse-coordinate robot**: records screen XY of Resolve UI
    controls and drives them (resolution/layout-dependent, one parameter
    at a time). Their own founder: built this way because Resolve is "a
    closed API." **[V]**
  - FlowKits "Fastlane" XL v1.2.4 (updated Jul 15 2026) is the newer
    rival; prices unfetchable (site 403). **[V listing / U price]**
- **Community read** (editor blogs; forums unreachable): editors run a
  Stream Deck *alongside* a Speed Editor or grading panel, not instead —
  deck for command access across pages, panel/jog for motion. Stream Deck
  + SideshowFX ≈ 3× cheaper than entry grading panels but "can't totally
  replace" one. **[V]**
- Hardware note: Elgato shipped the **Stream Deck + XL** in 2026 (36 keys,
  6 dials, touch strip, $350) — dials matter for grading profiles. Also:
  Ryan's Elgato app already registers a **Stream Deck +** (per DECK.md) —
  SideshowFX sell SD+ Resolve variants that could ride it. **[V]**
- Contrast that proves the ceiling is Resolve's, not the deck's: Ableton
  Live has a real two-way plugin (icon state feedback via Live's
  control-surface API, updated Jul 2026). Resolve exposes no equivalent
  API, so its deck ecosystem stops at profiles + mouse robots. **[V]**
- **Architectural relief:** our pipeline's Resolve control never touches
  the deck — it's the scripting API via the daemon/MCP. Deck-Resolve
  profiles serve exactly one thing: **Ryan's hands-on GUI pass** (the
  final human edit step). So a purchased profile is a craft tool for him,
  not infrastructure for the system.

## Part 3 — Key artwork: how keys get good

- Icon format **[V]**: 144×144 px; static SVG/PNG/JPEG; **animated GIF or
  WEBP** (≤5 s loop, 10–20 fps, ≤1 MB) — animated keys are normal practice.
- **Elgato Key Creator** — free browser-based icon editor (elgato.com/s/
  keycreator), the official make-your-own path. ("Icon Suite" does not
  exist as a product — misnomer.) **[V]**
- Packs creators actually run **[V]**: **Hexaza** (free, 2,000+ icons,
  the community daily-driver) · **Nerd or Die "Clarity"** ($6, the
  best-known animated set, ships PSD/AE sources) · StreamSpell packs
  (free 400-icon animated tier) · **SideshowFX Resolve icon collections**
  (4,300+, free sampler on Marketplace) · Aetheon OBS pack ($5, on/off
  variants).
- Documented power-user practice worth copying: use pack icons for static
  verbs, but **keep the official plugin's default icons wherever a key
  indicates state** — the state art is the honest part. **[V]**

## Part 4 — Triggering our daemon from the official app (macOS)

- **Negative result that kills a whole lane: BarRaider plugins (Advanced
  Launcher, API Ninja, etc.) are Windows-only, explicitly no Mac plans.**
  Most "run commands from Stream Deck" advice assumes them. **[V]**
- Built-in System → Open can run a chmod+x script file, but with a
  crippled $PATH, no output, no state. **[V blog / S official]**
- **Best current bridge: "Mac Automation" plugin (ThoughtAsylum, Jul
  2025, on the Marketplace)** — runs shell commands, AppleScript, Apple
  Shortcuts, and **HTTP requests via curl (ideal for our localhost:8873
  daemon verbs)**, with parameter passing. Alternatives: Ceylon "Shell
  Commands" (Marketplace, v0.1), stream-deck-shell (GitHub, ✅/⚠ overlay
  feedback only). **[V]**
- **The honest-state ceiling**: no off-the-shelf macOS plugin lets an
  external script update a key's image/title. Live daemon-state keys
  (SYS/JOBS-style) require a **custom plugin via the official SDK** —
  TypeScript/Node 24+, Stream Deck app 7.1+, `streamdeck create` CLI,
  WebSocket setImage/setTitle at any moment, good samples, modest
  difficulty. That's the one bespoke piece that could ever be justified,
  and only if fire-and-forget daemon keys prove insufficient. **[V]**

## Part 5 — Synthesis: the Elgato-native deck architecture (proposal)

Maps today's blessed decisions onto the ecosystem. Ryan picks; nothing is
wired yet.

1. **Creation surface = official Elgato OBS plugin**, in Ryan's own Elgato
   profile (his OBS control-room layout restored, then extended): his 7
   scene keys with native live state, REC/STOP with true state and native
   "Waiting for OBS" when it's dead, an "Open Application → OBS" key (or
   Multi Action) for launch, and **Chapter Marker as the MARK key** —
   pending the one-recording ffprobe verification. The Companion bespoke
   page for these functions is retired.
2. **Corpus stays as blessed** (ecosystem-independent): daemon auto-indexes
   new recordings in ~/Movies (free ffprobe rows in the registry);
   expensive processing lazy at edit time; ingest gains
   read-chapters→Story-IR-markers (replacing the never-built `mark` verb)
   after verification.
3. **Daemon-verb keys** (ingest-last, ingest-screensage, restart-resolve):
   few keys via the **Mac Automation plugin** (curl → daemon), dressed
   with proper icons (Key Creator / a chosen pack). Fire-and-forget with
   the daemon's own logs as truth; a custom SDK plugin for live
   daemon-state keys is the explicitly-deferred ceiling, built only if
   its absence actually hurts.
4. **Editing surface (optional purchase, Ryan's craft call, not
   infrastructure):** SideshowFX XL Edit ($19.99) or XL Pro ($34.99) as a
   Smart Profile that auto-appears when Resolve is focused; SD+ Resolve
   variants exist for the Stream Deck + he already has; Color Panel
   ($44.99 mouse robot) only if he wants dial grading knowing its
   fragility. QWERTY-US requirement applies.
5. **What this loses vs the Companion route, stated honestly:** on-key
   daemon status tiles, OBS timecode/bitrate variables on keys,
   preview/program tally granularity, and headless operation (Smart
   Profiles pause while the Stream Deck config window is open). None of
   these are in the blessed scope.

**Open [RYAN] choices:** (a) bless this architecture; (b) icon pack
taste — Hexaza free / Clarity $6 / Key Creator custom; (c) buy a Resolve
profile now, later, or never; (d) confirm retiring the Companion studio
page once native keys are proven.

**Verification queue before build:** one OBS test recording with two
Chapter Marker presses → ffprobe shows chapters → chapters map cleanly to
recording timecode. That single test gates the MARK-as-chapter design.

## Source index (load-bearing only)

- Official OBS plugin listing + version history: marketplace.elgato.com/product/obs-studio-35615969-830f-45c9-ba0a-1a295bba7fec
- Elgato OBS plugin page: elgato.com/ww/en/s/obs-studio-plugin-for-stream-deck
- Smart Profiles: elgato.com/us/en/explorer/products/stream-deck/smart-profiles-stream-deck/
- SideshowFX Resolve products: sideshowfx.net/products-davinci
- Elwyn on deck-vs-panels + Color Panel mechanism: jonnyelwyn.co.uk/film-and-video-editing/controlling-davinci-resolve-with-the-stream-deck/
- Icon-pack spec: docs.elgato.com/stream-deck/icons/getting-started/
- Key Creator: elgato.com/us/en/s/keycreator
- BarRaider macOS status: docs.barraider.com/faqs/general/compatibility/
- Mac Automation plugin: thoughtasylum.com/2025/07/14/stream-deck-plugin-mac-automation/
- Official SDK: docs.elgato.com/streamdeck/sdk/introduction/getting-started/
- Companion OBS module (gap comparison): github.com/bitfocus/companion-module-obs-studio
