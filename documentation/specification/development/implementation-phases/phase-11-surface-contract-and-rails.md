# Phase 11 — Surface Contract & Control Rails

## 1. Goal & why now

The two horizontal layers that define what a work surface *is* and how anything gets *invoked*: the
File 25 `SurfaceContract` + `SurfaceRegistry` with its structural no-private-architecture conformance
gate, and the File 26 `ControlRail` input-resolution layer (conversation, command palette,
keybindings, slash commands, steering, elicitation). Neither the six surfaces nor the full shell can
be built until this foundation exists — every surface declares a complete contract against 25, and
every modality reaches the same capability through 26's one resolution path. The P4 minimal surface
and conversation entry mature into the first instances of these full contracts.

## 2. Canonical scope & deferrals

- **File 25 — complete**: the `WorkSurface` primitive + surface disambiguation; `surface_id` =
  `subsystem_id`; the open `SurfaceKind` set (§3–§4); the **`SurfaceContract`** — all five required
  sections (Identity + availability predicate; State — `PanelKind`s + selection kinds + the
  static-vs-live split; Actions — the `SubsystemSurfaceSpec` reference + the **hint-not-fence rule**
  + control affordances + produced kinds; Views — `ViewPreset`s + customization policy; Context/
  model/execution/sandbox/workspace policy by reference); incomplete contracts rejected at
  registration; the declaration-vs-registry-state split — immutable `surface_contract_version`,
  mutable registered-entry state (§4–§9); the **`SurfaceRegistry`** + lifecycle + **the registration
  validator as the structural conformance gate** (§10); activation — presentation-activation vs
  execution-binding, the shell relationship, multi-surface composition (§11); **the
  no-private-architecture invariant + its closed reuse list** (§12); **the no-autonomy-field
  deletion** (§13); management-surface boundary (§14); persistence/locality (§16); events (§18).
- **File 26 — complete core**: the `ControlRail` primitive + `RailRegistry` + closed kinds (§3,
  §14); the input-resolution contract — the closed `RailResolution` set, the fixed resolution order,
  `RailResolutionRecord` with high-volume input transient by default (§4); **the
  unified-invocation-path invariant** (§4.4); availability-filtered presentation + typed
  `RailResolutionUnavailable` (§4.5); the Conversation rail — message commit + pre-dispatch +
  duplicate handling + queue-vs-interrupt (§5); the Command palette + menus (§6); the **Keybinding
  rail + keymap** — chord grammar, context stack, deterministic top-down first-match resolver,
  conflicts, null-action unbind, platform reality (§7); the Slash-command rail + `.atlas/commands/`
  definitions + precedence-never-upgrades-authority (§8); the Steering rail → 04 §17 interventions +
  cancellation (§10); Trigger-rail *framing* (§11 — mechanics → **P14**); External-protocol framing
  (§12 — transports → **P18**); **the elicitation contract** — approval is exactly 06 §13's
  request/response as one kind (§13). The Voice rail (§9) → **P17** (needs the audio sensor +
  consent; availability-gated until then).

## 3. Prerequisites

P10 — SurfaceState/self-registration, the availability evaluator (what rails present). P5/P6 —
capabilities, policy, routing, runs, lenses. P9 — the `.atlas/commands/` store, workspace binding.

## 4. Lanes

(a) SurfaceContract types + registry + validator; (b) activation/shell-relationship/composition;
(c) the rail resolution engine + per-rail behaviors; (d) elicitation + steering. (a) first — (b) and
(c) reference it; (c)'s core resolution contract is otherwise independent. Cross-phase overlap: P13's
quality-machinery lanes may start (their prerequisites are P6/P9).

## 5. Build plan

1. **SurfaceContract + registry**: validation per §10.3 — every required section present, ids
   well-formed + non-colliding, referenced capabilities resolvable, predicates parseable, **no
   private substrate declared** (the validator rejects against the closed reuse list); contract
   versions immutable; tombstoned unregistration preserving historical references; user-defined
   surface discovery from the surface directory, event-first.
2. **A reference surface fixture**: a minimal test-only conforming surface (one PanelKind, tiny
   spec) used by the conformance harness forever — proving "conforms by construction" (§12.4)
   before any real surface exists. The P4 minimal conversation surface then registers a real
   contract — the maturation seam closes.
3. **Activation wiring**: routing `primary_surface` → registry resolution → surface defaults feed
   07/13/16/04 composition; opening/focusing never reroutes a run; activation is scope-resolved (no
   single global active surface).
4. **Rail registry + resolution engine**: structural parse → deterministic match → pre-dispatch
   transform → schema resolution → route (argument/content reference expansion runs before the schema
   check so schema resolution sees the resolved arguments, 26 §4.2); resolution recorded and linked to downstream facts; the
   deterministic-match path skips the router model but never routing/policy/ledger.
5. **Conversation rail**: the P4 entry matured — pre-dispatch (02 §3.4) + 13's duplicate handling +
   queue-vs-interrupt.
6. **Command palette**: presentation over the availability-filtered list (07 Palette lens);
   argument elicitation from `input_schema`; effective-tier + availability indicators read from
   policy/registry; search is presentation, never authority.
7. **Keymap**: chord grammar; context stack; the one resolver (supersedes scattered per-component
   listeners); `ShortcutConflict`; null-action unbind.
8. **Slash commands**: namespaced grammar; capability-binding vs prompt-template kinds; precedence
   workspace > user > plugin > built-in choosing a definition, never upgrading trust/authority/floor.
9. **Steering + elicitation**: stop/cancel/pause/interject/takeover → 04 §17 (`control` flip);
   elicitation kinds closed; the P5 headless approval harness now answers through the rail — same
   contract, new channel.

## 6. Test obligations & acceptance evidence

- 25 — the named suites: **no-private-architecture-is-structural** (the headline) — the validator
  rejects omitted sections and private substrates (private pool/registry/policy/state-store/history/
  context-path/config-file/sandbox/secret-store/execution-model); grep + validator prove conformance
  by construction; **contract-completeness + declaration immutability**; **no-autonomy-field** — no
  participation/autonomy/interaction-shape/persona/phase field on any contract/preset/state, no
  `ParticipationLevelChanged` event; **ViewPreset-changes-presentation-only** — never silently
  changes model selection/context policy/execution entry/budget/sandbox/posture/instruction
  authority; **static-vs-live split** — the contract declares shape, the world model holds values
  via self-registration; no self-scraping, no private available-action store;
  **activation-vs-execution-binding** — focusing a surface never changes an active run without a
  03/04 reroute; lifecycle reconstruction — disable preserves history, unregister leaves references
  resolvable via tombstone (§10.4); structural semantics on panels/affordances (§5.3/§6.4);
  persistence — live state computed, loss is a rebuild.
- 26 — the named suites: **unified-invocation-path** (the headline) — the same capability through
  every rail hits the same declaration/policy/touched-resources/ledger/pipeline; no per-rail
  handler, no "palette version vs voice version"; a user vs agent invocation differs only in the
  recorded `Invoker` + tier path (the N-rails × 1-capability → 1-pipeline matrix test);
  **rail-resolution determinism** + closed outcome set + fixed order; **availability-filtered** —
  unavailable gesture → typed `RailResolutionUnavailable`, recomputed event-first, no polling;
  **keymap determinism** — pure function of input + context stack + bindings + pending chord;
  conflicts by stack priority not registration order; unbind; unavailable-modifier typed
  diagnostic; **elicitation** — approval is exactly 06 §13's shape (no re-owned approval),
  rail-agnostic, one response channel, never auto-resolves, typed-confirmation always asks;
  **steering safety** — floors + typed-confirmation honored; cancellation honors
  cooperative-then-forceful; mid-execution input never silently abandons a run;
  **non-interactive-can't-auto-approve** (trigger/external framing); slash precedence never
  upgrades authority + no silent shadowing; no-autonomy-field on rails (auto-approve is 06's
  posture preset, not a rail field).
- **Closed-set pinning**: SurfaceKind baseline, PanelKind baseline, SelectionKinds,
  ControlRailKind, RailResolution, elicitation kinds.
- Conformance matrix gains: `worksurface.*` + `controlrail.*` anchors; the P4 minimal-surface and
  conversation-entry stub rows close.

## 7. Artifacts, docs & CI surface

- **Generated artifacts**: shared types for `SurfaceContract` (required sections) + `SurfaceKind`/
  `ViewPreset`/`PanelKind`, `ControlRailKind`/`RailResolution`/`RailResolutionRecord`,
  `KeyBinding`/`Keystroke` + the context stack, elicitation kinds; the registration validator; the
  rail-resolution conformance suite (gesture → expected `RailResolution`); migrations for the
  surface-registry + rail/keybinding/custom-command families.
- **Docs**: the SurfaceContract reference + static-vs-live + hint-not-fence + activation docs; the
  no-private-architecture invariant doc; the input-resolution + per-rail references; the elicitation
  doc; **banned-vocabulary update** (domain/mode/sub-app/DomainSpec; command bar/hotkey system/
  intent dispatch).
- **CI/local commands**: the no-private-architecture (structural), contract-completeness,
  no-autonomy-field, unified-invocation-path, rail-determinism, and keymap suites as named CI jobs —
  these guards protect every later surface.

## 8. Exit criteria

- [ ] The reference surface registers, activates, and presents capabilities through palette +
      keybinding + slash — every gesture resolving to the identical invocation path.
- [ ] The conformance + autonomy-field guards wired into CI as structural checks.
- [ ] Steering a live run from the rail: pause, interject, cancel, takeover — all ledgered.
- [ ] The P4 surface/entry maturation seams closed; M0–M2 still green.

## 9. Locked in this phase

- **The `SurfaceContract` required-section set + `surface_id` = `subsystem_id` unification**
  (threading through routing, settings namespaces, instruction qualifiers, capability sources).
- **The closed reuse list** (what "a surface" means); registration-validation rules (the conformance
  gate QC and eval hook into).
- **The `RailResolution` closed set + resolution order + `RailResolutionRecord` shape**; the
  unified-invocation-path invariant.
- **The KeyBinding chord grammar + context-stack model**; the slash grammar + `.atlas/commands/`
  definition shape; the elicitation kind set.
- The permanent deletion of autonomy/participation/interaction-shape fields — structurally guarded
  from here forward (25 §13, 26 §17).
