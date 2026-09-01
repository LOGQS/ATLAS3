# Security, Credentials, and Trust Boundaries

## Status

Canonical. This file defines the data-plane security model of ATLAS3: how secret material is stored and used, how data is kept from leaking, how trust in code, sources, and devices is established, what encryption protects, and what the system defends against. It realizes the security, credential, secret-vault, encryption, trust, and egress boundaries Files 06, 09, 10, 11, 15, 17, 19, 20, and 21 declare and delegate to this layer, and it introduces the net-new primitives those files reference but do not own: the secret vault internals, the cryptography, the trust model, and the threat model. Later canonical files may refine it, but may not contradict it.

## Scope

This file defines:

- the threat model and trust posture: the local-first single-user adversary model, the trust boundaries between processes, the least-authority-by-default invariant, and the rule that security-critical state is human-governed
- the backend secret boundary (`secret.backend-boundary`) as the general, owning rule — the destinations raw `Secret` material may never reach, what may cross in its place, the `SecretValue` wrapper, and zeroization
- the `SecretVault` contract — the dedicated credential/secret store, its OS-keyring and encrypted-file backends, its namespace, the `SecretRef` and `vault:<key>` reference forms, the unlock model, and the agent-invisibility rule
- the credential lifecycle — store, resolve-at-point-of-use, rotate, expire, revoke, multi-account, credential-source removal, and the vault-reference contract Files 17 and the external-integration specs consume
- secret detection and redaction — the registered pattern set, the reverse environment-value scan, the automatic sensitivity stamping that feeds File 10, and redaction before any log, event, persistence, or egress
- encryption — encryption at rest of the vault and the optionally-encrypted substrate and blobs; the point at which encryption attaches to a sync stream or an export package; key derivation, the key hierarchy, and key rotation; committed cryptographic realizations behind a contract
- the trust model — trust classes and how trust is established, verified, escalated, downgraded, and revoked; the install-time capability-manifest review; the integrity-verification mechanism; the code-signing posture and its declared extension path; supply-chain trust
- device trust and pairing — the device-identity trust proof, the pairing-authorization mechanism, the sync credential, and the privilege-separation pairing boundary
- data egress governance — the policy semantics behind the `Public`/`Sensitive`/`Secret` egress tiers File 21 applies, the `Denied`-floor plus typed-confirmation gate for credential/secret export and irreversible publication, the egress-destination inspector, and redaction before egress
- untrusted content and injection defense — the structural untrusted-content marking, the no-authority-from-untrusted-content rule, sanitization, and the advisory injection classifier
- the local security posture — the process and IPC trust boundary, structural enforcement at service boundaries, content-security policy, input validation, and the local-authentication / vault-unlock gate
- audit cryptography — the cryptographic primitive behind File 10's hash-chained audit overlay, the tamper-detection contract, and the credential/secret operation entries this file registers into that overlay
- the security capability surface, the event vocabulary, the settings dimensions, the explicit rejections, and the consequences later specs consume

This file does not define:

- process spawning, sandbox scopes, resource isolation, filesystem-boundary enforcement, network-policy enforcement, killability, or the elevated-helper process mechanics — File 23 owns those; this file owns the trust boundary, the egress policy, and the secret/credential aspects across them, and consumes the enforcement primitives File 23 provides
- the `Public`/`Sensitive`/`Secret` sensitivity classification taxonomy itself, the per-entry sensitivity field, sensitivity-aware ledger persistence and retention, or the audit-overlay structure, membership, and verification contract — File 10 owns those; this file owns the security enforcement around them, the secret-detection that drives automatic stamping, and the cryptographic primitive the audit chain uses
- the capability policy evaluation algorithm, effective tier resolution, approval flows, leases, or contradiction-checking — File 06 owns those; this file owns the trust verification and the secret/egress inspectors that feed them
- sync and export movement mechanics, the conflict model, the package format and manifest, or the import pipeline — File 21 owns those; this file owns the encryption that attaches and the no-raw-secret-egress rule
- the storage substrate, the secret-vault file's existence and location, the blob store, or the audit-overlay storage — File 20 owns those; this file owns the vault cryptography, the keyring integration, and the encryption keying
- the settings cascade, scope resolution, the TOML overlay, or the `SecretRef` settings boundary — File 15 owns those; this file owns the vault that resolves the reference
- the perception capture-privacy contract — consent, sensitive-source redaction-before-persist, and recording transparency — File 19 owns those; this file owns the credential vault and trust state perception references by identity
- the provider adapter contract, the credential-pool rotation mechanics, or the per-provider credential namespace usage — File 17 owns those; this file owns the vault interface File 17 calls and the secret boundary it honors
- UI rendering of unlock prompts, trust-review dialogs, egress confirmations, or audit panels — File 37 and File 38 own those; this file specifies the data contracts they consume

## Source Resolution

This file resolves credentials, secrets, the secret vault, encryption, trust, code signing, data egress, exfiltration defense, prompt-injection defense, authentication, and the local threat model into one boundary: the data-plane security layer that protects secret material, governs what leaves the device, and establishes trust in code, sources, and devices, without re-owning any substrate's semantics or any execution-containment primitive.

Resolved design:

- ATLAS3 is local-first single-user software. The security model defends the user's secrets and data against untrusted code, injected instructions, compromised connectors, malicious imported data, and casual local exposure — not against a multi-tenant adversary or a remote authentication principal, which the product does not have.
- There is one secret vault, separate from the durable substrate and the settings store, accessed through one contract. Raw secret material lives only in backend-owned transient buffers and the vault, and is discarded after use. Everything else that needs a secret holds an opaque reference.
- Trust is established by source provenance plus an install-time capability-manifest review, with integrity verification by canonical source-integrity records and cryptographic signature verification as one evidence path. A source receives evidence-based `Verified` trust only when the system has verifiable authorship evidence; user trust overrides affect local policy, not the underlying evidence class.
- Egress is the moment privacy and secrecy are at stake. The safe default is automatic, every widening is explicit and policy-gated, and raw secrets never leave ordinary data-movement paths. This file owns the policy semantics and the explicit secret-egress exceptions; File 21 owns ordinary movement; File 06 owns the gate.
- Encryption attaches at declared boundaries — the vault always, the substrate and a sync stream and an export package optionally — over plaintext canonical encodings, so encryption never changes identity, hashes, or replication semantics.
- Security invariants are structural, not advisory: the vault is unreachable from the agent and the renderer by construction, not by a checklist; the secret boundary is enforced at the layers that persist or transmit, not by asking each call site to remember.

Resolved tensions:

- Author-authenticating code signing versus install-time manifest approval: resolved toward evidence-based trust. Install-time review plus source-integrity verification is sufficient for `Community`, `Unverified`, `Sideloaded`, or user-overridden effective trust; evidence-based `Verified` requires verifiable authorship evidence such as a trusted signature or organizational verification. The trust model never claims a guarantee it cannot prove.
- A single regex denylist versus an extensible detector for secret scanning: resolved toward a registered, settings-extensible detector (vendor-prefix patterns plus structural patterns plus reverse environment-value scan plus entropy), defaulting sensitivity up on uncertainty, because no fixed pattern list catches every credential shape and silent misses are unacceptable.
- LLM-classifier injection defense versus a structural rule: resolved toward the structural rule (untrusted content can never escalate authority) as load-bearing, with the classifier as an advisory inspector, because a probabilistic classifier must never be the only thing standing between injected text and a privileged action.
- Owning encryption-in-transit versus delegating it to the transport: resolved by attaching encryption at File-22-declared boundaries keyed by this file's requirements, while the transport and the substrate engine perform the byte-level work, so the cryptography is owned here and the mechanics stay where they belong.

## 1. Chosen Model

Anchor: `security.chosen-model`

### 1.1 Definition

ATLAS3 has one security layer. It is a substrate service with five cohesive responsibilities that sit beneath every other layer:

- **Secret custody**: the `SecretVault` holds every credential and secret, and the backend secret boundary keeps raw secret material out of every other layer.
- **Credential lifecycle**: storing, resolving at point of use, rotating, expiring, and revoking the credentials providers, connectors, sync, and integrations consume.
- **Trust establishment**: deciding how much a capability source, plugin, connector, imported package, or paired device is trusted, on what evidence, and verifying integrity.
- **Egress governance**: owning the policy semantics that decide what may leave the device and in what form, and the encryption that protects what does.
- **Cryptographic foundation**: the key hierarchy, the encryption primitives, and the audit-chain cryptography every integrity- and confidentiality-sensitive boundary relies on.

### 1.2 Purpose

Files 01 through 21 each declare a security boundary and delegate its internals here: File 10 the secret-payload-never-persists rule and the audit chain; File 15 the settings/secret split; File 17 the provider credential vault and the backend secret boundary; File 19 the credential and trust state perception references by identity; File 20 the vault file and the substrate-exclusion boundary; File 21 the encryption attachment point, the no-secret-egress rule, the vault-backup separation, and the egress-governance tiers; File 06 the trust input to policy. This file is the single place those internals become concrete, so no later spec invents a parallel secret store, a private credential path, an ungoverned egress channel, or an unverified trust shortcut.

### 1.3 Rule

- There is one secret vault, one backend secret boundary, one trust model, one egress-governance policy, and one cryptographic foundation. No subsystem, surface, plugin, or connector may introduce a private secret store, a private credential path, a private encryption scheme for shared data, or a private trust authority.
- Raw `Secret` material is held only in backend-owned transient buffers and the vault, and is discarded after use. Every other layer holds an opaque reference, a redacted projection, or a safe description.
- Security-critical state — the vault, the credential storage, the policy kernel, the trust state, the audit chain, and the environment variables that control paths, linkers, or interpreters — is human-governed. No agent, plugin, connector, or imported record may mutate it through ordinary capability paths (`core.extension-planes`, File 01 §6.14).
- Agents, plugins, automations, and imports may propose security changes as typed proposals. Applying changes to vault state, credential storage, trust state, egress policy, policy kernels, audit settings, or path/linker/interpreter environment variables requires the direct user-governed flows this file and File 06 define; no lease, auto-decide mode, profile, or automation silently applies those changes.
- The safe default is automatic and the unsafe widening is explicit. Egress defaults to `Public`-only; secret access is least-authority; untrusted content holds no authority.
- Security invariants are enforced structurally at the layers that persist, transmit, or expose, never by per-call-site discipline alone.

### 1.4 Boundary

This file owns the secret vault internals, the credential lifecycle, the trust model, the egress-governance policy, the encryption, and the audit cryptography. File 23 (Sandbox, Process Control, and Isolation) owns execution containment — the sandbox, the filesystem and network enforcement, the process boundaries, and the elevated-helper mechanics — and this file consumes those primitives and supplies the trust and secret rules across them. File 06 owns policy evaluation and consumes this file's trust verification. File 10 owns the sensitivity taxonomy and the audit-chain structure and consumes this file's cryptography. Files 17, 20, and 21 own the provider, storage, and movement layers and consume this file's vault, boundary, and encryption.

## 2. Boundaries with Adjacent Layers

Anchor: `security.boundaries-with-adjacent-layers`

### 2.1 With File 01

`core.extension-planes` (File 01 §6.14) already forbids extensions from overriding security-critical system state (path/linker/interpreter environment variables, credential storage, policy kernels); this file is where that prohibition is realized. `core.canonical-encoding` and `core.canonical-hash` (File 01 §6.15, §7.14) mean every integrity hash and encryption boundary computes over declared canonical encodings, never physical bytes. `core.non-destructive-by-default` (File 01 §7.13) means revoking a credential, downgrading trust, or rotating a key is recorded, never silently destructive. `core.stack-commitments` (File 01 §9) grounds the Tauri process model this file's IPC boundary relies on.

### 2.2 With File 06 (Capability Policy)

Trust is the input; policy is the evaluator. This file owns how a source's trust class is established, verified, and changed; File 06 owns how that trust class narrows an effective tier (`policy.trust-mapping-defaults`, File 06 §9.6; `policy.risk-classification-trust-interaction`, File 06 §15). The secret-detection and egress-destination inspectors this file defines register as policy inspectors (`policy.internal-composition-policy-inspectors`, File 06 §3.3); they narrow, never widen. The `Denied`-floor plus typed-confirmation gate this file requires for credential/secret export and irreversible publication is the File 06 mechanism (`policy.permission-floor-typed-confirmation`, File 06 §7), applied to the egress capabilities this file governs.

### 2.3 With File 10 (Ledger, Events, Hooks)

File 10 owns the `Public`/`Sensitive`/`Secret` taxonomy (`ledger.sensitivity-aware-persistence-retention`, File 10 §10), the rule that raw `Secret` payloads never persist to the durable ledger, the producer-seeded sensitivity stamping (`ledger.producer-seeded-sensitivity`, File 10 §10.2), the commit-time forgery guard that rejects secret-bearing entries (`ledger.forgery-guards`, File 10 §3.7), and the hash-chained audit overlay's structure, membership, and verification contract (`ledger.hash-chained-audit-log`, File 10 §16). This file owns the secret-detection patterns that drive the automatic stamping, the cryptographic primitive the audit chain hashes with, and the credential/secret operation entries File 10 §16.4 reserves for this file to register.

### 2.4 With File 15 (Settings)

`settings.secret-boundary` (File 15 §10) already requires that settings store only `SecretRef` values, that secret material never appears in settings/TOML/sync/export/log/agent-context, and that resolving a reference requires an authorized backend path owned by this file. This file provides that path: the vault. The no-secrets-in-overlay pattern scan File 15 and the configuration overlay perform is this file's secret-detection applied at the settings boundary.

### 2.5 With File 17 (Provider Layer)

File 17 §23.6 applies the backend secret boundary at the provider layer (`provider.sensitivity-redaction-secret-boundary`, File 17 §23), and `provider.credentials-accounts-pools` (File 17 §14) defined the `vault_ref` namespace (`provider.<provider_id>.<account_id>.<credential_id>`) and the `CredentialPool`. This file owns the general `secret.backend-boundary` rule (§4), implements the backend-only `resolve_for_use(...)` vault operation File 17 calls at the point of use, and emits the credential-rotation event File 17 subscribes to. The provider layer's namespace is one instance of this file's vault namespace contract.

### 2.6 With File 19 (Perception)

`perception.capture-privacy` (File 19 §10) owns consent, sensitive-source detection, redaction-before-persist, secret masking at capture, scope bounding, and recording transparency. This file owns the credential vault and the trust state that perception references by identity, treats every `Secret` capture as safe-description-only, and provides the secret-detection patterns perception's redaction applies. Perception senses; this file decides what is secret and where credentials live.

### 2.7 With File 20 (Storage) and File 21 (Portability)

`storage.secret-vault-boundary` (File 20 §14) gives this file the vault file's existence and location and the rule that raw secret material never enters the durable substrate; this file owns the vault's cryptography, key management, keyring integration, and encryption-at-rest keying. `portability.sensitivity-egress` (File 21 §12) applies the egress tiers and the no-secret-egress rule; `portability.export-bundle` (File 21 §10) produces the package this file may encrypt; `portability.device-identity` (File 21 §8) records pairing while this file owns the credential cryptography and trust proof; `portability.backup-restore` (File 21 §13) separates vault backup as an explicit action this file owns. This file owns the encryption that attaches and the trust internals; those files own the movement and the substrate.

### 2.8 With File 23 (Sandbox, Process Control, and Isolation)

The boundary is sharp. File 23 owns process spawning, sandbox scopes, the filesystem and network enforcement primitives, resource isolation, killability, and the elevated-helper process mechanics. This file owns the trust CLASS and its changes (§9) — the input the sandboxing decision consumes; the trust-to-tier mapping itself and the tier selection are File 23 §4.3's (its table discharges the mapping this sentence previously left unowned). This file also owns the egress-destination policy the network enforcement consults, the secret/credential rules across process boundaries, and the privilege-separation pairing credential. This file states the trust boundary and the policy; File 23 enforces the containment.

### 2.9 Boundary

This file is the data-plane security layer. It owns no execution-containment primitive, no sensitivity taxonomy, no policy-evaluation algorithm, no movement mechanic, and no storage schema. It owns secret custody, credential lifecycle, trust establishment, egress policy, and the cryptographic foundation, and supplies each to the layer that consumes it.

## 3. Threat Model and Trust Posture

Anchor: `security.threat-model`

### 3.1 Definition

The threat model is the explicit statement of what ATLAS3's security defends against, what it does not, and the trust boundaries it draws. The trust posture is the set of default stances — least authority, untrusted-by-default external content, human-governed security-critical state — that the rest of this file realizes.

### 3.2 Purpose

A security model that does not state its adversary either over-promises (claiming protections it cannot deliver) or over-engineers (defending against an adversary the product does not face). ATLAS3 is local-first single-user software; naming that shape precisely is what lets every later rule be honest and proportionate.

### 3.3 Rule

- **The product shape.** ATLAS3 is local-first and single-user. There is no remote authentication principal, no multi-tenant isolation requirement, and no per-user access control within an installation (`portability.device-identity`, File 21 §8.3). Security defends the single user's secrets and data; it does not partition users.
- **The defended adversaries.** The model defends against: untrusted or malicious capability sources (plugins, MCP servers, external-API definitions, imported packages); instructions injected into agent-reachable content (tool results, web and document content, connector responses, file content); compromised or hostile network destinations attempting to receive exfiltrated data; malicious or corrupt imported data attempting to overwrite or poison local state; and casual local exposure of secrets (in logs, exports, the clipboard, the renderer, model context, or memory-to-disk paths such as core dumps, swap, and hibernation images).
- **The explicitly-not-defended.** The model does not claim to defend against an attacker with full local code-execution or root on the user's device, against hardware or operating-system compromise, against a malicious operating-system keyring, or against the user deliberately exfiltrating their own data. These are stated, not silently assumed.
- **Least authority by default.** Every secret access, capability grant, and source is scoped to the narrowest authority that does the job, and authority is inspectable (`policy.lease-primitive`, File 06 §11). Broad standing authority is an explicit user choice, never a default.
- **Untrusted by default.** External content and unverified sources hold no authority. Authority is granted, never assumed from provenance the system cannot verify.
- **Human-governed security-critical state.** The vault, credential storage, the policy kernel, the trust state, the audit chain, and the path/linker/interpreter environment variables are human-governed (`core.extension-planes`, File 01 §6.14). No agent, plugin, connector, automation, or imported record mutates them through ordinary capability paths; changing them is an explicit, audited user action.
- **Trust boundaries between processes.** The backend process is the only trust domain that holds raw secret material. The renderer, the agent's model context, sandboxed child processes, and external connectors are lower-trust domains across which raw secrets never pass (§4, §13).

### 3.4 Boundary

This section fixes the posture and the adversary model. The mechanisms that realize each stance are owned by the sections that follow and by File 23's containment primitives. The threat model is descriptive of intent and proportionate to the product; it is not a compliance checklist.

## 4. The Backend Secret Boundary

Anchor: `secret.backend-boundary`

### 4.1 Definition

The backend secret boundary is the rule that raw `Secret` material never crosses out of the backend's transient buffers and the vault. This section is the general, owning statement of the rule; File 17 §23.6 applies it at the provider layer (`provider.sensitivity-redaction-secret-boundary`). `Secret` material is the closed set File 10 §10 classifies: resolved credentials, raw API keys, vault-decoded OAuth and bearer tokens, refresh tokens, request signatures, passphrases, private keys, and unredacted user content the user or the runtime has marked `Secret`. The boundary governs egress — material leaving backend custody. The one controlled ingress exception is user credential entry: a secret the user types transits the renderer heap and the IPC bridge once on its way into the vault, in the inbound direction only. That path is write-only toward the vault, is never echoed back, logged, or retained in the renderer (§13.2), and is not a license to move a resolved secret outward.

### 4.2 Purpose

A secret is only as safe as the narrowest place it lives. Every path a secret can take out of the backend — to disk, to the wire, to the screen, to the model — is a place it can leak. Confining raw secret material to one process and one store, and letting only references travel, makes the leak surface a single auditable boundary instead of every call site.

### 4.3 Rule

- **Forbidden destinations.** Raw `Secret` material must never reach the frontend or renderer process, the JavaScript heap, an IPC payload, model-request context, a log, an event payload, a ledger entry, telemetry, a settings value, the TOML overlay, block content, a retrieval index, a projection, an ordinary sync stream, an ordinary export package, the clipboard, a core dump, a swap file, a hibernation image, or an ordinary substrate backup. The only paths that carry raw secret material off the device are the explicit secret-egress carve-outs this file governs — credential export and the separate vault backup (§6.4, §6.5, §11.5) — never an ordinary movement, backup, log, event, or memory-to-disk path.
- **What may cross instead.** In place of raw material, the boundary passes an opaque secret reference (`SecretRef` or a vault namespace key, §5.4), a redacted projection, a safe description (`safe_description`), or a capability-scoped handle that resolves the secret only inside the backend at the point of use.
- **Capability-scoped handles.** A capability-scoped secret handle is backend-local, non-serializable, purpose-bound, and scoped to one invocation, run, or execution unit. It is invalidated by vault lock, revocation, cancellation, or the end of its scope; it is never persisted, logged, exported, sent over IPC, shown to the model, accepted from external input, or treated as a `SecretRef`.
- **The `SecretValue` wrapper.** Raw secret material held in backend memory is carried in a `SecretValue` type whose debug and display forms render a fixed redaction marker, never the contents, and which exposes its contents only through an explicit `expose` accessor called at the point of use. Accidental logging or formatting of a `SecretValue` reveals nothing.
- **Zeroization.** A backend buffer that holds raw secret material is zeroized when the capability invocation or backend operation that needed it no longer needs it. Zeroization applies only to buffers that actually hold raw material; references, redacted projections, safe descriptions, and handles carry nothing to zeroize.
- **Memory-to-disk suppression.** Because the operating system can spill process memory to disk, the backend suppresses the paths that would write raw secret material out of RAM. Disabling core dumps for the secret-holding process (`PR_SET_DUMPABLE=0` and `RLIMIT_CORE=0` on Linux, Windows Error Reporting exclusion on Windows) is a near-free, high-value mitigation and is applied. Memory locking (`mlock`/`VirtualLock`) may pin secret buffers out of the ordinary swap file, but it is best-effort with an explicit residual risk: it does not close hibernation, which images all of RAM to disk, so it is never presented as closure of the memory-to-disk exposure. Zeroization is the primary in-memory defense; these paths reduce the residual disk-spill surface, they do not replace it.
- **Resolution at point of use.** A service that needs a secret resolves the reference against the vault inside the backend at the moment of use and discards the resolved material at the end of that point-of-use scope; it never holds a secret in a long-lived structure (`provider.credentials-accounts-pools`, File 17 §14.2).
- **Structural enforcement.** The boundary is enforced at the layers that persist or transmit — the ledger commit validator (`ledger.forgery-guards`, File 10 §3.7), the settings write path (`settings.secret-boundary`, File 15 §10), the export and sync paths (`portability.sensitivity-egress`, File 21 §12), and the IPC bridge (§13) — not by asking each capability author to remember.

### 4.4 Boundary

This section owns the general boundary and its enforcement points. File 10 enforces it at the ledger, event, sync, and telemetry paths; File 15 at the settings, TOML, and sync paths; File 17 at the provider call path; File 21 at the export and share paths; File 23 at the sandbox process boundary. Each enforcement is the same rule applied at one layer; none redefines it.

## 5. The Secret Vault

Anchor: `security.secret-vault`

### 5.1 Definition

The `SecretVault` is the dedicated store for every credential and secret, separate from the durable substrate and the settings store. It is the only place raw secret material persists, and it is reachable only from backend services. File 20 §14 places the vault file; this section owns its contract, backends, namespace, reference forms, and unlock model.

### 5.2 The Vault Contract

The vault exposes a typed contract with at least: store a secret under a key, backend-only `resolve_for_use(SecretRef, purpose, invocation_context)`, delete a secret by key, list redacted vault metadata (never values), rotate a secret under a key, and report typed resolution states. `resolve_for_use` is not a capability, IPC method, model-visible tool, or renderer-accessible operation; it is a backend service operation used only at point of use. The contract is the semantic boundary; the backend behind it is replaceable (`core.extension-integrity`, File 01 §7.10). A canonical rule may name the committed backends for grounding but must not depend on a backend-specific capability the contract does not expose.

### 5.3 Backends

The vault has two committed backend realizations behind the contract:

- **OS keyring (default).** Where an operating-system keyring is available, the vault stores secrets in it: the platform keychain, credential manager, or secret-service facility, reached through one keyring abstraction so no canonical rule encodes a per-platform detail. The operating system governs unlock through its own access control.
- **Encrypted-file fallback.** Where no OS keyring is available — minimal servers, containers, continuous-integration environments — the vault stores secrets in an encrypted file under the data root (File 20 §14.3), encrypted with an authenticated-encryption cipher under a key derived from a user-set passphrase by a memory-hard key-derivation function (§8). The committed realizations are an AES-256-GCM-class authenticated cipher and an Argon2id-class derivation; they sit behind the encryption contract (§8) and are replaceable.

The backend in use is a storage-resolved fact (File 20 §14.3); the vault contract is identical across both.

### 5.4 Namespace and Reference Forms

- The vault namespace is a flat, structured key space. Keys are dotted, owner-scoped identifiers — for example `provider.<provider_id>.<account_id>.<credential_id>` (File 17 §14.2), `sync.<destination_id>.auth_token`, `connector.<connector_id>.<credential_id>`. Each owning subsystem declares its key shape; this file owns the namespace contract, not the per-owner shape.
- A `SecretRef` is the opaque reference that crosses the backend secret boundary in place of a secret: it carries the vault namespace key and a redaction-aware, source-attributed descriptor, never the value (`settings.secret-boundary`, File 15 §10).
- A `vault:<key>` substitution is the inert textual reference form permitted in declarative configuration (connector definitions, external-API files, MCP server entries): the literal value is fetched from the vault at the point of use, never at configuration-load time. A literal secret found where a `vault:<key>` reference belongs is detected (§7) and refused with a typed diagnostic; the owning declaration is marked unauthenticated until a reference replaces it.

### 5.5 Unlock Model

- When the OS keyring backs the vault, unlock is the operating system's responsibility; the vault performs no additional passphrase prompt unless the user enables one through settings.
- When the encrypted-file fallback backs the vault, a user passphrase derives the file's key. The passphrase is prompted at first run and on each subsequent start, unless the user opts into remembering it for the current desktop session, in which case the derived key is held in backend memory only and never persisted.
- No master passphrase is ever stored. An optional operating-system authentication gate (platform biometric or local-account authentication) may guard unlock as a settings-driven convenience over the keyring; it is never the sole protection and never replaces the keyring's own access control.
- A locked vault degrades cleanly: secret-dependent operations surface a typed `VaultLocked` state and request unlock; they neither fail silently nor proceed without the secret.
- Locking the vault is a categorical security boundary for secret-dependent work. It zeroizes session keys, invalidates active capability-scoped secret handles, cancels or blocks secret-dependent backend operations at safe boundaries per File 04 killability, and causes future secret resolutions to return `VaultLocked`. Non-secret work continues.

### 5.6 Metadata and Resolution States

Vault metadata is redacted management state, not secret material. Each vault entry carries at least: vault key, owner subsystem or source, secret kind, redacted descriptor, sensitivity, locality/scope, lifecycle state, source/provenance, generation, optional expiry or validity facts, and audit references. This metadata may be visible through gated management surfaces according to policy; raw values never are.

Resolution returns typed states rather than nulls or ad-hoc errors: `Resolved`, `VaultLocked`, `Missing`, `Revoked`, `Expired`, `Invalid`, `PolicyDenied`, and `BackendUnavailable`. Live validation facts are operational status recorded for inspection; replay and historical reconstruction use recorded safe descriptions and resolution outcomes, never live provider revalidation.

### 5.7 Agent and Renderer Invisibility

The vault is unreachable from the agent and the renderer by construction. The vault contract is not exposed as a capability in the tool registry; no tool resolves, lists values from, or exports the vault. When a service needs a secret to perform an operation, it resolves the reference inside backend code and never passes the value through a tool call, a block, an event, or an IPC payload (`infrastructure/configuration.md` agent-visibility rule, realized). Listing redacted vault metadata for management is a gated capability (§15); reading a value is not a capability at all.

### 5.8 Boundary

This section owns the vault contract, backends, namespace, reference forms, unlock model, and invisibility rule. File 20 owns the vault file's existence and location and the storage fact of which backend is in use. File 15 owns the `SecretRef` settings boundary. File 17 and the connector specs own their per-owner namespace shapes. The cryptography the encrypted-file backend uses is §8's.

## 6. Credential Lifecycle

Anchor: `security.credentials`

### 6.1 Definition

A credential is a secret used to authenticate to an external service — an API key, an OAuth or bearer token, a refresh token, a signed-request key, a basic-auth password, a sync authorization token. The credential lifecycle is how such secrets are stored, resolved, rotated, expired, revoked, and removed, all through the vault.

### 6.2 Storage and Resolution

- A credential is stored under a vault key and referenced everywhere else by `SecretRef` or `vault:<key>` (§5.4). It never appears inline in a provider struct, a connector definition, a settings value, a ledger entry, an event, an export, a log, or agent context (`provider.explicit-rejections`, File 17 §25).
- Multi-account is canonical: a provider or connector may hold several named accounts, each with its own credential under its own key (`provider.credentials-accounts-pools`, File 17 §14.1). The credential pool's rotation mechanics are File 17's; the vault holds the referenced material.
- Resolution happens at the point of use inside the backend through `resolve_for_use(...)`, and the resolved material is discarded when the operation no longer needs it (§4.3, §5.2).

### 6.3 Rotation, Expiry, and Refresh

- Rotating a credential writes the new material under the same key and emits `SecretRotated` (§16). Subscribers — provider adapters, connector clients — refresh their cached resolution; rotation never triggers an active health probe, and the next call validates the new material implicitly (`provider.credentials-accounts-pools`, File 17 §14.4).
- OAuth and delegated credentials carry their refresh discipline: the refresh token lives in the vault, the short-lived access token is refreshed on demand inside the backend, and a user-delegated flow stores the refresh token once after the user completes the authorization (`infrastructure/external-apis.md`, realized).
- Expiry is a typed state, not a timed deletion: an expired or invalid credential surfaces a typed authentication-failure class (aligned with File 17 §10's `ProviderError` taxonomy) and a credential-needed handoff; the runtime does not silently retry an authentication failure.

### 6.4 Revocation and Removal

- Revoking a credential deletes its vault material, emits `SecretRevoked`, and records the revocation in the audit overlay (§14); the destructive delete precedes the durable audit record, and success is reported only after that record is durable (`ledger.explicit-rejections`, File 10 §18), so a crash between the two leaves the safe residue — the secret already gone and the revocation reclaimable — never a recorded revocation standing over a still-live secret. Dependent services resolve to a credential-needed state; revocation is non-destructive to the records that referenced the credential — only the secret is gone.
- Credential removal is suppression-aware: removing a credential that has multiple discovery sources records the removal so the same credential is not silently re-seeded from another source without the user's intent.
- Credential export is governed: exporting raw credential material is a `permission_floor: Denied` operation gated by typed-confirmation (§11.4, `policy.denied-carve-out`, File 06 §7.4); the exported value, where the user explicitly authorizes it, is the only path raw secret material leaves the vault, and it leaves through the separate vault-backup or explicit-export path, never through an ordinary package or sync stream (§11).

### 6.5 Vault Backup and Restore

Vault backup and restore are separate explicit security capabilities, not ordinary export/import. `vault.backup` produces an encrypted, integrity-protected backup artifact outside `PortablePackage`; `vault.restore` stages a preview of entries, conflicts, missing keys, and add/overwrite/skip decisions before applying anything. Restore never silently overwrites an existing credential and never imports executable-source trust as local authority without source approval.

Vault backup and restore carry `permission_floor: Denied`, typed-confirmation, and audit-overlay participation, and each records its outcome durably in the audit overlay before reporting success (`ledger.explicit-rejections`, File 10 §18); where restore overwrites an existing credential, the prior material is deleted before the overwrite is recorded, yielding the same safe crash residue as revocation (§6.4). If a backup passphrase or wrapping key is lost, the backup is unrecoverable unless another key path was deliberately configured; the system must surface that fact before backup creation.

### 6.6 Boundary

This section owns the credential lifecycle over the vault. File 17 owns the provider-side credential pool, account model, and rotation triggers; the connector and MCP specs own their credential acquisition flows; this file owns the vault storage, the reference contract, and the rotation/revocation events those layers consume.

## 7. Secret Detection and Redaction

Anchor: `security.secret-detection-redaction`

### 7.1 Definition

Secret detection is the mechanism that recognizes secret-shaped material in text and structured data; redaction is the act of replacing it with a safe marker before the material is persisted, logged, exposed, or egressed. Detection is what drives the automatic sensitivity stamping File 10 §10.2 requires and the no-secrets-in-settings refusal File 15 §10 requires.

### 7.2 The Detector

- The detector is a registered, extensible set of typed patterns, not a fixed closed list. It includes: vendor-prefix and known-shape patterns (provider key prefixes, token formats, signed-JWT shapes, private-key blocks, connection strings, authorization headers); structural patterns (assignments and JSON fields whose key matches `*_api_key`, `*_token`, `*_secret`, `*_password`, and equivalents); and a reverse environment-value scan that flags content containing the live value of a known environment secret, catching hardcoded secrets that pattern matching alone misses.
- Environment-derived detector values are ephemeral `SecretValue`s. They are compared in backend memory only, never stored as detector patterns, logs, events, or debug output; only detector ids, source names, or non-reversible fingerprints may be recorded.
- The pattern set is settings-extensible (§17): the user and registered sources may add patterns. External detector extensions register through the capability/source-approval system, default to narrowing-only, and cannot lower sensitivity. Built-in patterns may be tuned, but disabling a built-in detector for a known secret shape is a security-widening settings change.
- Detection defaults up: on uncertainty, content is classified at the higher sensitivity, never the lower (`ledger.producer-seeded-sensitivity`, File 10 §10.2). Lowering a detected classification requires a typed-confirmation policy override (File 06 §7).

### 7.3 Redaction and Masking

- Redaction replaces detected secret material with a fixed marker before the content reaches any log, event, ledger entry, persisted observation, export, or model context. A redacting log formatter applies the detector to every message so a secret that reaches a log statement is masked rather than written.
- Masking preserves only what is safe to show: a detected credential may be rendered as a kind label or a short non-reversible fingerprint for display, never as its value (`open-cowork`-class fingerprint, realized as a non-reversible derivation).
- Error and tool-result scrubbing is part of the contract: provider error bodies, connector responses, and tool results are scrubbed of detected secret material before they re-enter model context or persist, so an upstream error never leaks a credential and injected error text cannot smuggle one in (`provider.sensitivity-redaction-secret-boundary`, File 17 §23.4).
- What masking shows is not customizable copy: the masked-value indication, the kind label or non-reversible fingerprint standing in for a credential, and the rendered trust-state and provenance indications whose classes §9 owns carry semantics the presentation layer localizes but never relabels away — a user copy override (`ui.i18n`, File 37 §15) may change a field's friendly label and never its secret, redaction, or trust indication.

### 7.4 Boundary

This section owns the detection patterns and the redaction mechanism. File 10 owns the sensitivity classes the detection stamps and the persistence rules; File 15 owns the settings-boundary refusal that consumes the detector; File 19 owns the capture-time masking that applies it; File 21 owns the egress filtering that applies it. The detector is one mechanism those layers consume; none reimplements it.

## 8. Encryption

Anchor: `security.encryption`

### 8.1 Definition

Encryption is the protection of confidential data at rest and in transit by authenticated ciphers under managed keys. This section owns the key hierarchy, the derivation, the attachment points, and the rotation. It defines the contract and names committed realizations; it does not freeze a wire format.

### 8.2 The Key Hierarchy and Derivation

- Keys are managed in a hierarchy: a root key, protected by the OS keyring or derived from a user passphrase by a memory-hard key-derivation function, wraps the data-encryption keys that protect individual stores. A data-encryption key is never persisted in the clear; it is wrapped by the root key or held only in backend memory while in use.
- The committed derivation realization is an Argon2id-class memory-hard function with a per-vault random salt; the committed cipher realization is an AES-256-GCM-class authenticated cipher with a unique nonce per encryption. Both sit behind the encryption contract and are replaceable; no canonical rule depends on a specific algorithm beyond "authenticated encryption under a memory-hard-derived key."
- Key material is `Secret` and obeys the backend secret boundary (§4): a derived key lives only in backend memory and is zeroized after use; it never crosses to the renderer, a log, an event, a sync stream, or a memory-to-disk path such as a core dump or swap image (§4.3).

### 8.3 Encryption at Rest

- **The vault** is always encrypted at rest: by the OS keyring's own protection where it backs the vault, or by the encrypted-file cipher and derivation (§5.3) where it does not. The vault is the one store whose encryption is non-optional.
- **The durable substrate** may optionally be opened against an encrypted engine; this file owns the keying of that encryption, and File 20 §14.3 owns the storage configuration that selects it. Substrate encryption protects device-local data at rest against casual local exposure. Whether it is enabled by default is resolved by tested settings profiles, platform capability, and user choice; the canonical rule is the attachment and keying contract, not a hardcoded unlock posture.
- **Content-addressed blobs** that carry `Sensitive` content may be encrypted at rest under the same hierarchy; the blob's content hash (`core.canonical-hash`, File 01 §7.14) is computed over the plaintext canonical encoding, so encryption never changes content identity or dedup.
- **Encryption envelope metadata** travels with every encrypted payload. The envelope records the algorithm suite id, key id or key slot, key generation, nonce or IV, associated-data descriptor, plaintext canonical-encoding id, ciphertext integrity tag, and wrapping metadata where applicable. The envelope is metadata about protection; it does not change the plaintext identity hash or the owning storage schema.

### 8.4 Encryption in Transit and the Attachment Point

This section discharges File 21's delegation of "the boundary at which encryption attaches."

- **The sync stream.** The sync transport's network protection is required and configured by this file: a `SyncDestinationProfile` carries the trust and encryption requirements (`portability.sync-transport`, File 21 §3.1, delegated here), and this file requires that a sync stream to a remote primary uses authenticated transport encryption and that the sync authorization credential is vault-held and never inline. Local in-process or local-file movement may satisfy the requirement by being non-network local movement under File 21's profile; plaintext remote sync is invalid. The transport performs the byte-level encryption; this file owns the requirement and the keying.
- **The export package.** Encryption attaches over `portability.export-bundle` (File 21 §10) as an optional outer envelope: File 21 produces the lossless package under declared canonical encoding, and this file optionally encrypts the package container under a user passphrase-derived key (§8.2) for at-rest or in-transit protection. The package integrity hash (File 21 §10.4) is computed over the plaintext canonical encoding, so encryption is an envelope over an unchanged identity. Encryption never substitutes for the no-secret-egress rule: raw secrets are excluded from the package before any encryption; encryption protects the already-permitted `Sensitive` content, it does not license secret export.

### 8.5 Key Rotation

- Rotating the root key re-wraps the data-encryption keys without re-encrypting the protected data; rotating a data-encryption key re-encrypts the store it protects. Both preserve enough envelope metadata to decrypt older records until rotation completes, both are recorded, and both emit a rotation event (§16). Neither is time-driven, and both are explicit operations or settings-driven maintenance, never a hidden cadence (`core.non-destructive-by-default`, File 01 §7.13).
- A passphrase change re-derives the root key and re-wraps; it never requires re-encrypting the data and never exposes a key in the clear.

### 8.6 Boundary

This section owns the key hierarchy, derivation, attachment points, and rotation. File 20 owns the storage configuration that selects substrate encryption and the vault file's location; File 21 owns the package bytes and the sync transport; the transport and the storage engine perform the byte-level cryptography under this file's keys and requirements. Algorithm specifics are committed realizations behind the contract, not frozen canonical wire formats (`spec_creation_criteria.md` rule 6).

## 9. The Trust Model

Anchor: `security.trust-model`

### 9.1 Definition

The trust model is how ATLAS3 decides how much a capability source — a plugin, an MCP server, an external-API definition, a user-defined capability, an imported package — is trusted, on what evidence, and how that trust is established, verified, escalated, downgraded, and revoked. The trust class is the input File 06 narrows tiers against; this file owns how the class is determined.

### 9.2 Trust Classes

The trust classes are the closed set File 06 already consumes as registered-entry `effective_trust` (`capability.trust-source-approval-flow`, File 05 §9.2; `policy.trust-mapping-defaults`, File 06 §9.6): `System` (the runtime itself), `Verified` (the source's authorship is cryptographically or organizationally verified), `User` (authored by the user on this installation), `Community` (published to a registry but unverified), `Unverified`, and `Sideloaded` (added by the user from an arbitrary source). This file owns the evidence that places a source in a class and the verification that may move it.

### 9.3 Evidence, Overrides, and Effective Trust

Trust has two distinct facts:

- `source_trust_evidence`: the evidence-backed classification derived from provenance, manifest review, integrity verification, signature verification, and organizational verification.
- `user_trust_override`: the user's local policy override, recorded separately from evidence.

Policy consumes `effective_trust`, a projection over evidence, override, settings, integrity state, and revocation state. A user can treat a source as trusted for local policy purposes, but cannot turn an unverified source into evidence-based `Verified`; `Verified` means verifiable authorship or organizational evidence exists.

### 9.4 How Trust Is Established

- **Provenance plus install-time review.** A source's initial class is determined by its provenance — bundled with the application, published to a registry, user-authored, or sideloaded — and confirmed by the install-time capability-manifest review (§9.5). Trust is not assumed from a self-declared hint; the source-authored trust hint is one input the user weighs, never the determinant (`policy.source-approval-flow`, File 06 §9).
- **Evidence-based verification.** Bundled sources inherit the application's installation trust. Registry, plugin, MCP, external-API, imported, and sideloaded sources receive the evidence class their provenance and verification justify; absence of verifiable authorship evidence prevents evidence-based `Verified` classification. Such sources remain `Community`, `Unverified`, `Sideloaded`, or user-overridden effective trust according to File 06 policy.
- **Signature verification.** Cryptographic signature verification of source authorship is one evidence path: when a trusted signature or authority exists, `Verified` may be established by verifying a signature over the source-integrity manifest or source artifact against a trusted key. The trust-class set and policy narrowing do not change; the evidence that reaches `Verified` changes.

### 9.5 The Capability-Manifest Review

- A source declares, at registration, a permission manifest: the permission tiers, floors, touched-resource classes, network and credential access, and capability families it requires (`capability.declaration`, File 05 §3; the `SourceRegistrationProposal`, File 06 §9.3). The review surfaces the manifest and the computed trust class to the user before the source's capabilities become invocable (`policy.source-approval-flow`, File 06 §9).
- This file owns the trust-class computation and the integrity verification feeding the review; File 06 owns the review flow, the user's options, and the resulting leases. The review is the trust establishment point; the runtime never registers an invocable source whose review the user did not complete (File 06 §9.7).

### 9.6 Integrity Verification

- Integrity verification binds approval to a `SourceIntegrityRecord`: the canonical source-integrity manifest hash, declaration ids and versions, executable artifact hashes or immutable source references, source version, source provenance, and approval decision. The hash is over declared canonical encodings, never incidental physical storage bytes (`core.canonical-hash`, File 01 §7.14). A later mismatch is a tamper signal that surfaces and re-gates the source, even though integrity verification authenticates the approved content, not the author.
- Source updates create a new source version and a new integrity record. They never silently rewrite the approved record. Compatibility, trust, and re-review requirements are resolved from the new record, the prior approval, and File 06 policy.
- Integrity verification composes with trust: a `Verified` or bundled source whose content fails integrity verification is treated as tampered and downgraded until re-reviewed.

### 9.7 Imported Trust Assertions

Trust is installation-local. Imported, synced, or packaged trust records are provenance and evidence only; they do not activate a source, raise effective trust, grant leases, or enable capabilities without local source approval and integrity verification. Imported records that reference unapproved executable sources resolve to inert or untrusted state until the local installation approves them.

### 9.8 Escalation, Downgrade, and Revocation

- The user may raise a source's effective trust through an explicit override (`policy.trust-mapping-defaults`, File 06 §9.6, settings-overridable); this file records the override separately from evidence. An override grants at most `User`-equivalent local effective trust: it never reaches `System`, which is the runtime itself and is not source-assignable, and it never reaches evidence-based `Verified`, which requires verifiable authorship evidence and cannot be conferred by user policy (§9.2, §9.3). Trust escalation is the user's deliberate policy act, never an automatic consequence of usage.
- Trust downgrades automatically on a tamper signal, an integrity failure, or a revoked signature; a downgrade staleness-revalidates the source's leases (`policy.mid-execution-policy-re-evaluation`, File 06 §10.2 `trust_downgrade`) and may invalidate overrides where policy requires.
- Revoking a source's trust disables its capabilities and records the revocation in the audit overlay; the records the source produced are preserved (`core.non-destructive-by-default`, File 01 §7.13). Evidence changes and override changes are recorded as distinct facts.

### 9.9 Boundary

This section owns trust establishment, verification, and change. File 06 owns how a trust class narrows an effective tier and runs the source-approval flow; File 05 owns the registered-entry trust state and the declaration; File 21, File 35, and File 36 own the install, update, and enablement mechanics this file gates. Executable code installation and execution are not this file's; the trust decision over them is.

## 10. Device Trust and Pairing

Anchor: `security.device-trust`

### 10.1 Definition

Device trust is how an installation proves its identity to the user's sync primary and how the user authorizes and revokes a device in the sync relationship. This section owns the credential cryptography and trust proof File 21 §8 delegates; File 21 owns the pairing records and the device list.

### 10.2 Rule

- **Device-identity material is device-local and private.** Each installation holds a stable device identity that keys its per-device state (`portability.device-identity`, File 21 §8.3); the private identity material is vault-held, device-local, and never synced, exported, or shared raw.
- **Pairing authorization.** Pairing a device to the user-controlled primary is authorized by a credential the user holds, stored in the vault and referenced, never inline (File 21 §8.2). The pairing authorization is account-based against a user-controlled primary; there is no Atlas-hosted server and no Atlas-held device key.
- **Sync-credential enforcement.** The credential that authorizes a device's sync to the primary is secret-vault material, referenced and never inline (`portability.device-identity`, File 21 §8.3). It is enforced either per device — each paired device authorizes with its own vault-held sync credential keyed to its device identity — or, where the sync model uses one account-based authorization, as a single shared credential the paired set holds; in both forms the credential is vault-resolved at the sync handshake and never travels in a sync payload, package, log, or event. A device whose pairing is revoked can no longer present an accepted sync credential.
- **Pairing-secret discipline.** Where a pairing exchange uses a shared secret — between devices, or between the main process and a privilege-separated helper (§10.3) — the secret is generated with cryptographic randomness, scoped, time-bounded, rate-limited against brute force, stored with least-privilege file permissions, and written atomically. A pairing secret is `Secret` and obeys the backend boundary (§4).
- **Revocation propagates.** Removing a device writes a revocation the other devices honor (File 21 §8.3); this file owns that a revoked device's trust proof is no longer accepted, while its local substrate is untouched.
- **No multi-user principal.** Device pairing authorizes a device, not a user; it introduces no authentication principal, no per-user access control, and no identity beyond the single user's device set (File 21 §8.3).

### 10.3 Privilege-Separation Pairing

Where the system performs a privileged operation through a separate elevated helper (the process mechanics of which are File 23's), the helper is paired to the main process by a shared secret this file owns: the secret is vault-or-restricted-file held with least-privilege permissions, established at first elevated use, and required on every command so only the paired main process can drive the helper. This file owns the pairing credential and the least-privilege principle; File 23 owns the helper's process model, its narrow command allowlist, and its sandbox.

### 10.4 Boundary

This section owns device-trust cryptography, the pairing credential, and the trust proof. File 21 owns the pairing records, the device list, and revocation propagation; File 23 owns the elevated-helper process; the user-controlled primary is infrastructure outside ATLAS.

## 11. Data Egress Governance

Anchor: `security.egress-governance`

### 11.1 Definition

Egress governance is the policy that decides what data may leave the device or installation and in what form. Every boundary crossing is exactly one of the twelve closed `EgressChannelKind`s (§11.7) — there is no ungoverned "any external transfer" residual. This section owns the policy semantics behind the tiers File 21 §12 applies, and the closed kind set itself.

### 11.2 The Sensitivity Tiers

- **`Public` has no sensitivity-specific egress gate.** Public-classified data may leave through governed egress paths without sensitivity opt-in, but capability policy, source trust, destination inspection, and capability-specific audit still apply.
- **`Sensitive` egresses only on explicit opt-in.** Sensitive data leaves only when the user opts in at the relevant movement scope: per operation for export, share, publish, clipboard, and format conversion; per sync destination, profile, or workspace for sensitive sync; and per automation template for expected non-interactive egress. The opt-in is explicit, recorded, visible, revocable, and settings-governed, never a silent default (`ledger.sensitivity-aware-persistence-retention`, File 10 §10.6; `portability.sensitivity-egress`, File 21 §12.3).
- **`Secret` never egresses through ordinary movement paths as raw material.** Raw secret material never enters an ordinary sync stream, package, share, publish, clipboard copy, log, event, agent context, substrate backup, or telemetry path (§4). Only safe descriptions and opaque references travel. The only raw-secret egress paths are explicit secret-egress capabilities such as credential export and separate vault backup (§6.4, §6.5, §11.5).

### 11.3 The Gate

- Egress is a governed capability: export to an external destination, publish, external share, sensitive export, and restore/backup route through File 06 policy and typed-confirmation where required (`portability.sensitivity-egress`, File 21 §12.3).
- Credential and secret export and irreversible external publication carry a `permission_floor: Denied` and the typed-confirmation override (`policy.permission-floor-typed-confirmation`, File 06 §7; `policy.denied-carve-out`, File 06 §7.4). This is the egress-governance tier policy File 21 §12 applies and this file owns: no lease, posture preset, trust upgrade, or mode lifts the floor; the only path is the user typing the confirmation per operation.
- Redaction before egress is explicit and typed: detected secret material is removed (§7), and the redaction is recorded as a typed manifest redaction with a provenance gap where needed (`portability.export-bundle`, File 21 §10.3). A per-field override may raise effective sensitivity before egress, never silently lower it.

### 11.4 Egress-Destination Governance

- The destination is part of the egress decision, not only the data. An egress-destination inspector registers as a File 06 policy inspector (`policy.internal-composition-policy-inspectors`, File 06 §3.3): it consumes the resolved File 05 touched resources and capability preview data for the proposed invocation, including network destinations, connector targets, filesystem/export destinations, clipboard destinations, browser-navigation targets, credential destinations, remotes, and external endpoints, then matches them against the user's destination allowlist and denylist.
- A proposed egress to a destination outside the allowlist (or inside the denylist) narrows the decision — it escalates to ask-user or denies — and is recorded. The inspector narrows, never widens; it cannot grant an egress the tier system would deny.
- The destination allowlist and denylist are settings (§17), default-deny for high-risk classes (credential and secret egress) and configurable per scope. The network enforcement that blocks a connection is File 23's; the egress policy that classifies the destination is this file's.

### 11.5 Vault Backup as a Separate Path

Vault backup is an explicit secret-egress capability, and it is separate from every ordinary egress path (`portability.backup-restore`, File 21 §13.3). A substrate backup does not back up the vault; a package or sync stream never carries raw secrets. Vault backup is a `permission_floor: Denied`, typed-confirmation operation that produces an encrypted vault backup artifact (§6.5, §8) the user moves deliberately; this file owns its internals.

### 11.6 Provider-Call Content Egress

Sending content to an external model provider is a first-class egress channel, not an unclassified side effect. A provider call is governed by the pre-selection data-boundary decision (`model.model-workload-requirements`, File 16 §5.3), which analyzes content sensitivity before a model is chosen and treats the resulting `data_boundary_requirements` as hard filters, and by the boundary proof the provider layer carries into every request (`provider.provider-request`, File 17 §7.1): sensitive material the active provider must not see fails at the adapter boundary with a typed data-boundary conflict rather than being transmitted (`provider.provider-request`, File 17 §7.3). This channel uses the data-boundary-filter model, not the §11.2 `Sensitive` per-operation opt-in — the boundary decision, not a user opt-in at a movement scope, determines whether content may reach a given provider — and raw `Secret` material never reaches a provider call in any form (§4). File 21 §12 mirrors this channel at the movement boundary.

### 11.7 The Closed Egress-Channel Kind Set

`EgressChannelKind` is a closed, twelve-variant policy-routing discriminant, keyed one kind per distinct governing gate. It identifies the governing boundary channel; it is neither a sensitivity classification nor an authorization result. Every attempted egress selects exactly one kind before the boundary crossing and carries it through preview, policy evaluation, destination inspection (§11.4), ledger recording, and audit. Selecting a kind never grants egress — the applicable sensitivity rule (§11.2), permission floor (§11.3), destination decision, redaction requirement, capability policy, and audit requirement remain independently binding. A missing, unknown, or unmappable kind fails closed before data crosses the boundary.

- `SyncPush` — the sensitive-sync gate: a durable per-destination, per-profile, or per-workspace grant (§11.2), never per-operation consent. Replica, remote, and sync-profile distinctions are metadata, not kinds.
- `OperationScopedMovement` — the per-operation `Sensitive` opt-in gate (§11.2) over the ordinary movement mechanisms: package export, surface format export, external filesystem write, clipboard copy, and share (File 21 §§10, 12.3). The mechanism distinctions are capability and preview metadata; the gate is one.
- `Publish` — the per-operation gate PLUS the irreversibility floor: irreversible external publication carries `permission_floor: Denied` with the typed-confirmation override (§11.3); an explicit irreversibility fact determines whether the floor activates.
- `ProviderCall` — the data-boundary-filter gate (§11.6): pre-selection sensitivity analysis as a hard filter (File 16 §5.3), pre-dispatch revalidation (File 13 §6), and adapter-boundary rejection (File 17 §7.3) — never the §11.2 per-operation opt-in model.
- `ExternalCapabilityCall` — File 06 capability policy plus destination inspection for an Atlas-initiated external invocation: outbound MCP-client calls, connectors, external APIs, remote tools, and data sent to external local processes over stdio/IPC/native messaging. A capability-declared higher floor remains effective.
- `ExternalClientResponse` — sensitivity and secret enforcement plus destination inspection at the outbound RESULT boundary: data returned by Atlas in its MCP-server or another external-protocol server role. It never merges into `ExternalCapabilityCall` — the crossing is a response to an inbound invoker, not an Atlas-initiated call.
- `WebOrBrowserRequest` — destination inspection specialized to browser-navigation and web-request targets, re-validated on every redirect hop (§11.4, §12.5); File 23 performs the network enforcement.
- `TelemetryExport` — the active, durable, revocable telemetry-consent gate, keyed per category, destination, permitted data classes, and installation (File 41 §7) — including an opt-in crash-report destination, which is a telemetry sink under that consent. Log, trace, metric, usage, and crash categories are fields, not kinds.
- `DiagnosticBundleExport` — the user-initiated one-shot diagnostic-bundle gate (File 41 §§7.4, 13): redaction first, `Public`-only by default, `Sensitive` only on typed confirmation, then explicit user sharing. It acquires no authority from durable sink consent.
- `SubstrateBackupExport` — the explicit-selection backup gate (File 21 §13.3); raw `Secret` material categorically excluded. A device-local internal snapshot is not egress; this kind applies when the recoverable copy crosses the installation boundary.
- `CredentialExport` — the raw-secret release gate: `permission_floor: Denied`, per-operation typed confirmation, default-deny destination inspection (§6.4, §11.3-§11.4). Never merged with `VaultBackup`: this path releases explicitly selected raw credential material.
- `VaultBackup` — the separate explicit secret-egress capability (§6.5, §11.5): `permission_floor: Denied`, typed confirmation, producing the encrypted, integrity-protected vault backup artifact. "Separate path" separates it from ordinary egress, never from egress governance.

`Public` removes only the sensitivity-specific gate on a kind. `Sensitive` uses the scope attached to the selected kind. Raw `Secret` material is denied on every ordinary kind; only `CredentialExport` and `VaultBackup` are the declared raw-secret paths (§11.2). The per-automation-template opt-in (§11.2) is an additional scope over whichever kind a non-interactive operation uses, not a thirteenth kind. Classification names the actual gate-bearing outbound crossing — never the producing subsystem, UI affordance, payload purpose, or protocol name — and one operation performing two independently gated crossings classifies and evaluates each separately. There is no `Custom` kind and none may be added by registration: an extension-defined kind would be an undeclared egress path outside the closed governance table (`core.invariants`, File 01), so an extension maps its outbound operation to one of the twelve, and an unmappable path fails closed pending canonical maintenance.

### 11.8 Boundary

This section owns the egress policy semantics, the closed `EgressChannelKind` set, the destination inspector, and the vault-backup path. File 21 owns the movement and the package format; File 10 owns the sensitivity taxonomy; File 06 owns the gate and the floor; File 23 owns the network enforcement. The egress decision is this file's policy applied through File 06's mechanism over File 21's movement.

## 12. Untrusted Content and Injection Defense

Anchor: `security.untrusted-content`

### 12.1 Definition

Untrusted content is any agent-reachable data the system did not author and cannot vouch for: tool results, web and document content, connector and MCP responses, imported package metadata, file content, and external messages. Injection defense is the set of rules that keeps instructions embedded in untrusted content from escalating authority.

### 12.2 The Structural Rule

The load-bearing defense is structural, not probabilistic: untrusted content holds no authority. Specifically, content marked untrusted can never, by its own text, widen a lease, lift a permission floor, lift a typed-confirmation requirement, change a sensitivity classification downward, raise a source's trust, or authorize an egress. Authority comes only from the user and from verified policy (`policy.effective-tier-resolution`, File 06 §4); an instruction found inside untrusted content is data, not a command. This rule composes with File 06: an injected "approve this" in a tool result reaches the policy layer as ordinary input the user or policy still gates, never as an approval.

### 12.3 Marking and Sanitization

- Agent-reachable external content is represented using File 13's assembly-part authority model: tool results, web content, connector and MCP responses, imported records, and external files enter model-request assembly as `authority_class: untrusted_source_data` unless stricter evidence and policy justify another class. Instruction-boundary markers render at authority transitions per File 13; the boundary between instruction and data cannot be erased by the content itself.
- Sanitization removes known injection carriers before untrusted content reaches model context: invisible or tag-channel characters (the Unicode Tags block and equivalents) are stripped and the stripping recorded, and content-addressed or structural smuggling vectors are normalized. Sanitization reduces the carrier surface; it is not the primary defense and never makes untrusted content trusted.

### 12.4 The Advisory Classifier

- An optional injection classifier may inspect untrusted content and flag suspected injection, escalating a proposed action to ask-user. It is advisory and composes as a narrowing-only policy inspector (`policy.internal-composition-policy-inspectors`, File 06 §3.3): it may escalate or deny, never silently allow, and it never substitutes for the structural rule (§12.2). A probabilistic classifier is never the only thing between injected text and a privileged action.

### 12.5 Destination Re-Validation

Where untrusted content can redirect an outbound request (a redirect chain, a connector-supplied URL), the destination is re-validated against the egress-destination policy (§11.4) on every hop, so an initially-allowed destination cannot redirect to a forbidden one. This defends the exfiltration-via-redirect vector.

### 12.6 Boundary

This section owns the untrusted-content marking, the no-authority rule, sanitization, and the advisory classifier. File 06 owns the policy evaluation the rule composes with; File 19 owns the capture-side handling of sensitive sources; File 23 owns the network enforcement the destination re-validation consults. The structural rule is canonical; the classifier is opt-in.

## 13. Local Security Posture

Anchor: `security.local-posture`

### 13.1 Definition

The local security posture is the set of structural protections at the process, IPC, and input boundaries of the local application: the backend-only secret domain, the renderer trust boundary, content-security policy, input validation, and the local-authentication gate.

### 13.2 The Process and IPC Trust Boundary

- The backend process is the only trust domain that holds raw secret material and reaches the vault (§3.3, §5.7). The renderer process is a lower-trust domain: it never receives raw secrets, never reaches the vault, and communicates with the backend only through typed, named IPC methods, not an open channel (`core.stack-commitments`, File 01 §9 Tauri model).
- The IPC surface is an allowlist of typed commands; the renderer cannot invoke arbitrary backend functions. Business logic lives in the backend service layer, never in the IPC command wrappers (Service-Layer Ownership, File 01 §7.7), so the trust boundary is structural.
- Secret-bearing values are never returned to the renderer after being saved: a stored credential is write-only from the renderer's perspective; the renderer holds a reference and a redacted descriptor, never the value.
- Credential entry is the one controlled ingress exception to §4.3's no-raw-secret-in-renderer-or-IPC letter: a secret the user types transits the renderer heap and a typed IPC method once, in the inbound direction toward the vault (§4.1). The boundary treats that entry path as write-only — the value is consumed into the vault and never read back, so ingress for entry does not weaken the egress rule that raw secrets never return to the renderer.

### 13.3 Structural Enforcement at Service Boundaries

Security invariants are enforced at the service trait boundary, not scattered across call sites: the file-access boundary, the secret boundary, and the egress boundary are each a single structural chokepoint a subsystem cannot bypass by forgetting a check. The filesystem path-validation and workspace-boundary enforcement mechanics are File 23's; this file owns the principle that the invariant is structural and the trust boundary it protects.

### 13.4 Content-Security and Input Validation

- The renderer runs under a content-security policy that restricts script and resource origins to the application's own and forbids embedding by foreign frames, reducing the injection and exfiltration surface of any rendered content.
- User and external input is validated and sanitized against injection at the boundary it enters; control characters and oversized payloads are rejected with typed errors, and a security-boundary rejection is non-retryable (a path-traversal or boundary error is a boundary, not a transient fault).

### 13.5 The Local-Authentication Gate

- An optional local-authentication gate (a platform biometric or local-account check, or the vault passphrase) may guard application unlock or sensitive operations as a settings-driven convenience (§5.5). It protects against casual local exposure; it is not claimed as a defense against a local code-execution adversary (§3.3) and never replaces the vault's own protection.

### 13.6 Boundary

This section owns the trust-boundary principle, the IPC posture, and the local-authentication gate's security role. File 23 owns the filesystem and process enforcement mechanics; File 37 and File 38 own the unlock and consent presentation; File 01 §9 grounds the process model. The posture is structural; the rendering is not this file's.

## 14. Audit Cryptography

Anchor: `security.audit-crypto`

### 14.1 Definition

Audit cryptography is the cryptographic primitive behind File 10's device-local hash-chained audit overlay and the credential/secret operation entries this file registers into it. File 10 owns the overlay's structure, membership, and verification contract (`ledger.hash-chained-audit-log`, File 10 §16); this file owns the cryptography and the security-operation membership.

### 14.2 The Cryptographic Primitive

- The audit chain is a hash chain: each entry's hash is computed by a collision-resistant hash function (the committed realization is SHA-256) over the prior entry's hash, the canonical redacted entry hash, and the entry's identifying fields, so any alteration of a past entry breaks the chain from that point forward (`ledger.hash-chained-audit-log`, File 10 §16). This file owns that the hash function is collision-resistant and the chaining is over canonical encodings (`core.canonical-hash`, File 01 §7.14); File 10 owns the field set hashed.
- Verification recomputes the chain and reports a tamper signal on mismatch; the tamper signal halts sync of the affected device and surfaces to the user (File 10 §16.5). This file owns the cryptographic verification; File 10 owns the response contract.
- The audit overlay is device-local, append-only, never synced, and never disabled — even when telemetry and logging are disabled, security-sensitive operations write to it (File 10 §10.5; File 20 §14.3). This file owns that the never-disabled property holds for the security operations it registers.

### 14.3 Registered Security Operations

This file registers, into File 10's audit tier (File 10 §16.4, which reserves "every credential or secret operation" for this spec), the security-operation entries: secret stored, resolved-for-use, rotated, revoked, and deleted; key rotation; trust evidence changed; trust override changed; trust revoked; integrity-verification failure; vault unlock and lock; vault backup and restore; credential and secret export; and egress block. These join the policy, lease, floor-violation, source-approval, hard-delete, and `DeniedFloorOverridden` entries File 10 §16.4 already enumerates.

### 14.4 Boundary

This section owns the cryptographic primitive and the security-operation membership. File 10 owns the chain structure, the verification response, and the membership contract; File 20 owns the overlay's storage. The cryptography is this file's; the chain and its storage are File 10's and File 20's.

## 15. Security Capability Surface

Anchor: `security.capability-surface`

### 15.1 Definition

The security layer exposes canonical capabilities for vault management, trust management, egress-policy management, and security inspection, declared and gated like every other capability.

### 15.2 Rule

- Canonical capabilities include: writing and rotating a vault-backed credential reference, deleting and revoking a credential, listing redacted vault metadata (never values), unlocking and locking the vault, reviewing trust evidence and user trust overrides, verifying integrity, managing the egress allowlist and denylist, rotating a key, exporting a credential, backing up or restoring the vault, and verifying the audit chain. The provider-credential capabilities File 17 §22.6 declares (`provider.set_credential`, `provider.rotate_credential`) resolve through this file's vault.
- Reading a secret value is never a capability: no tool, palette action, automation, or external client resolves a secret value. Listing redacted metadata, managing references, and rotating are gated capabilities; resolving a value happens only inside backend service code at the point of use (§5.2).
- The high-risk security capabilities — credential export, vault backup or restore, trust override that widens effective trust for a sideloaded or unverified source, and security-widening settings changes — carry a `permission_floor: Denied` and typed-confirmation (`policy.permission-floor-typed-confirmation`, File 06 §7); no posture preset, lease, or mode lifts the floor.
- Security capabilities are declared per File 05, tier-gated per File 06, surfaced per File 07, and cancellable per File 04 where long-running; none bypasses the policy layer, the secret boundary, or the audit overlay.

### 15.3 Boundary

This section names the capability surface. File 05 owns the declarations, File 06 the policy gating, File 07 the loading and visibility, File 17 the provider-credential capabilities that resolve here. This file declares the security capabilities as canonical built-ins.

## 16. Events

Anchor: `security.events`

### 16.1 Rule

- Security events emit through File 10's canonical bus with the standard envelope and sensitivity (`ledger.event-stream`, File 10 §5; `ledger.event-envelope`, File 10 §5.2). Consequential security operations also write to the audit overlay (§14.3). Specialized security facts are registered as `Custom { namespace: "security", name, payload }` kinds unless File 10 later promotes a cross-cutting kind into its closed catalogue. Credential and secret event names include `SecretStored`, `SecretResolvedForUse`, `SecretRotated`, `SecretRevoked`, and `SecretDeleted`; trust, encryption, and egress event names include `TrustEvidenceChanged`, `TrustOverrideChanged`, `TrustRevoked`, `IntegrityVerificationFailed`, `KeyRotated`, `VaultUnlocked`/`VaultLocked`, `VaultBackedUp`/`VaultRestored`, `CredentialExported`, `EgressBlocked`, and `InjectionDetected`. `AuditChainTamperDetected` is File 10's event (File 10 §16.5); this file consumes it.
- `SecretRotated` is the vault rotation event; File 17's `CredentialRotated` (File 17 §14.4) is the provider-facing event the vault rotation triggers for a provider credential, emitted alongside, never a parallel rotation mechanism.
- Live event emission and audit recording are distinct. Audit entries are durable device-local security facts; live events are coordination and projection signals. Events that touch `Secret` content carry the corresponding sensitivity and never include raw secret material in their payload (§4.3). Security events flow only through the canonical bus; no side-channel security notification is permitted.

### 16.2 Boundary

This section names the security event behavior. File 10 owns the envelope, sequencing, delivery, persistence, and the audit overlay; File 17 owns `CredentialRotated`. This file emits its events through that shared mechanism.

## 17. Settings

Anchor: `security.settings`

### 17.1 Rule

Every security mechanism with meaningful variation is configurable through File 15 settings, with namespaced keys (`security.*`) declaring scope, agent exposure, locality, and sensitivity. Dimensions include:

- vault backend selection and the encrypted-file fallback location (bootstrap-resolved, File 20 §14.3)
- vault unlock behavior: passphrase prompt, session-remember, and the optional OS-authentication gate
- the secret-detection pattern set extensions and the redaction policy
- encryption enablement for the substrate and for `Sensitive` blobs, and the key-rotation policy (explicit and settings-driven, never timed)
- export-package encryption default and the sync-stream encryption requirement
- trust thresholds per source class and the source-approval review trigger (composed with File 06 §16's policy settings, not a parallel store)
- the install-time integrity-verification strictness and the signature-verification enablement when available
- the egress-destination allowlist and denylist per scope, default-deny for credential and secret destinations
- the injection-defense mode: structural-only, sanitization, or sanitization-plus-advisory-classifier
- the local-authentication gate enablement and scope

Specific defaults belong to tested settings profiles, not hardcoded constants (`settings.settings-over-constants`, File 15 §13). Agent exposure of security settings is conservative: the vault, trust state, secret-detection internals, and audit cryptography are `Hidden` from the agent; posture-level settings may be `OnRequest`; secret values are never a setting at all. No security behavior is a hidden hardcoded branch where a meaningful variation exists.

Security setting changes are classified by safety direction:

- `narrowing`: increases protection and may apply directly if otherwise valid
- `equivalent`: preserves posture and applies normally
- `widening`: weakens a guardrail and requires typed-confirmation, audit recording, and clear UI
- `forbidden`: attempts to violate a structural invariant and is rejected

Structural invariants are not settings. They include no raw secrets to renderer, model context, logs, ordinary egress, sync, packages, or events; no authority from untrusted content; no policy-floor bypass; no private secret store; and no disabled audit overlay for security operations. Explicit secret-export and vault-backup/restore capabilities are controlled exceptions, not settings that disable the invariant.

### 17.2 Boundary

This section names the dimensions. File 15 owns the cascade, storage, agent-exposure enforcement, and the secret-reference boundary; File 06 owns the policy settings these compose with. This file declares the security settings through that shared mechanism.

## 18. Explicit Rejections

Anchor: `security.explicit-rejections`

The following shapes are wrong for this layer:

- a private secret store, a per-subsystem credential cache, or any secret persistence outside the one vault
- raw `Secret` material reaching the renderer, the JavaScript heap, an IPC payload, model context, a log, an event, a ledger entry, telemetry, a settings value, the TOML overlay, block content, a retrieval index, an ordinary sync stream, an ordinary export package, the clipboard, or a substrate backup
- a secret value exposed as a capability, a tool result, or a block — listing keys and managing references is gated; reading a value is never a capability
- inline secrets in a configuration file, a connector definition, an MCP entry, a provider struct, or a settings value — only `SecretRef` and `vault:<key>` references
- a resolved credential retained in a long-lived structure beyond the request that needed it, or a key held in the clear outside backend memory
- a fixed closed secret-detection list treated as complete, or detection that defaults sensitivity down on uncertainty
- a trust model that claims to authenticate authorship without verifiable evidence, or that treats a self-declared trust hint as the determinant of trust
- code execution or capability invocation from a source whose install-time manifest review the user did not complete, or trust escalation as an automatic consequence of usage
- authority granted by untrusted content — an injected instruction in a tool result, web page, connector response, or imported record that widens a lease, lifts a floor, lifts typed-confirmation, lowers sensitivity, raises trust, or authorizes egress
- a probabilistic injection classifier as the only defense, with no structural no-authority-from-untrusted rule beneath it
- egress that includes `Sensitive` data without explicit opt-in at the relevant movement scope, ordinary egress that moves raw `Secret` material in any form, or any egress that bypasses the destination policy
- credential or secret export, or irreversible external publication, without the `permission_floor: Denied` plus typed-confirmation gate
- the secret vault backed up as part of an ordinary substrate backup, package, or sync stream rather than as a separate explicit encrypted security action
- encryption that changes a content hash, a package identity, or a replication semantic — encryption attaches over plaintext canonical encodings
- a hash chain over physical bytes rather than the declared canonical encoding, or an audit overlay that syncs across devices or can be disabled for security-sensitive operations
- time-based or polling-driven security behavior treated as a correctness condition — key rotation, trust revalidation, and audit verification are event-driven or explicit, never a hidden cadence
- agent, plugin, connector, automation, or imported-record mutation of the vault, credential storage, the policy kernel, the trust state, the audit chain, or the path/linker/interpreter environment variables — security-critical state is human-governed
- a setting, profile, lease, automation, or trust override that disables a structural security invariant; configurable guardrails may widen only through typed-confirmation, but structural invariants remain enforced
- a per-surface or per-plugin parallel trust authority, egress policy, or encryption scheme for shared data — there is one of each behind one contract
- a multi-user authentication principal or per-user access control — ATLAS3 is single-user; device pairing authorizes a device, not a user

## 19. Consequences for Later Specs

Anchor: `security.consequences-for-later-specs`

Every later spec that touches credentials, secrets, trust, encryption, egress, or local security consumes this layer as defined here.

- File 23 owns process spawning, sandbox scopes, filesystem and network enforcement, resource isolation, killability, and the elevated-helper process mechanics; it consumes this file's trust decision (how strictly to sandbox an untrusted source), egress-destination policy (which destinations the network enforcement blocks), secret/credential rules across process boundaries, and the privilege-separation pairing credential. It enforces containment; this file decides trust and policy.
- File 24 persists workspace data through the substrate and consumes this file's secret boundary (no secret in a materialized file unredacted) and egress governance (workspace export through the governed paths).
- The **per-surface specs** (Coder, Web, Data Processor, Teacher, GUI Control, System Agent) consume the vault for any service credential, the backend secret boundary for any secret-bearing capture or log, the secret detector for redaction, the trust model for any source they load, and the egress governance for any export; none introduces a private secret store, a private egress path, or a private trust authority.
- The **Automation and Triggers** spec (File 33) runs non-interactive work under least authority, resolves credentials through the vault at point of use, and obeys the egress governance for any automated outbound transfer; an automation never holds a resolved secret or escalates trust without the user.
- The **Extension and Plugin System** (File 35) and **MCP and External Integrations** (File 36) specs own the install, update, enablement, and execution of code; they consume this file's trust establishment, the install-time manifest review, source-integrity records, evidence-based verification, and user trust overrides; a synced or imported record referencing an unapproved source resolves to an untrusted, inert state, and imported trust assertions are evidence rather than local authority.
- The **UI Shell** spec (File 37) and the **UI Customization** spec (File 38) render the unlock prompt, the trust-review dialog, the egress confirmation, the credential management surface, and the audit panel from the data contracts this file defines; raw secrets never reach the renderer to be rendered.
- The **Telemetry, Logging, and Observability** spec (File 41) consumes security events as data, redacts through this file's detector, and never makes a telemetry view a source of truth or egresses content this file excludes.
- The **Evaluation and Benchmarking** spec (File 40) verifies the secret boundary (no secret in any persisted, transmitted, or exposed path), the redaction detector (golden fixtures for known secret shapes), the audit-chain tamper detection, the egress gate (no `Sensitive` without opt-in, no raw `Secret` ever), the encryption attachment (identity unchanged under encryption), and the no-authority-from-untrusted-content rule; it replays over recorded snapshots and immutable references, not live secret state.
- Every later spec that introduces a credential, a secret, a trusted source, an encrypted store, or an egress path declares it against this file's vault, boundary, trust model, encryption contract, and egress governance, and obeys the no-inline-secret, no-secret-egress, least-authority, human-governed-security-state, and no-authority-from-untrusted-content rules this file fixes.

## 20. Canonical Rule Anchors

Anchor: `security.canonical-rule-anchors`

Load-bearing rules defined by this file carry stable anchors: `security.chosen-model`, `security.boundaries-with-adjacent-layers`, `security.threat-model`, `secret.backend-boundary`, `security.secret-vault`, `security.credentials`, `security.secret-detection-redaction`, `security.encryption`, `security.trust-model`, `security.device-trust`, `security.egress-governance`, `security.untrusted-content`, `security.local-posture`, `security.audit-crypto`, `security.capability-surface`, `security.events`, and `security.settings`. Cross-references should prefer the anchor and may cite the section number secondarily. An anchor names exactly one canonical rule and is stable across spec revisions.
