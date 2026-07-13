# Hermes backlog — Luke Jarvis reel (DZ5H6F1Rz1S)

Ordered **Hermes runtime** tasks inspired by [Luke's reel critique](https://www.instagram.com/reel/DZ5H6F1Rz1S/) and Ranne's reply transcript (`data/inbox/DZ5H6F1Rz1S.md`). Current runtime is the Windows PC; Mac/VPS are optional hosts. This is **runtime Nami on Hermes**, not a full Jarvis build in Cursor.

See [SURFACE_MAP.md](./SURFACE_MAP.md) for what belongs on the PC runtime vs Cursor/build work.

**Loop engineering lens:** [LOOP_ENGINEERING.md](./LOOP_ENGINEERING.md) — same backlog items reframed as automations, connectors, sub-agents, memory, and checker-first design (Sabrina article + [YouTube](https://www.youtube.com/watch?v=Ry3YyG22EUc)).

## Priority (actionable on Hermes runtime)

| # | Task | Surface | Effort | Notes |
|---|------|---------|--------|-------|
| 1 | **Hermes voice** — enable built-in talk-to-agent mode | Hermes | ~1–2h | Luke uses Hermes voice instead of typing; aligns with STATUS "Bella voice skill later" but native voice is first |
| 2 | **Browser connect** — Chrome control from Hermes (`/browser` or equivalent) | Hermes | ~1–2h | Only enable on the active runtime host; document allowlist + security posture |
| 3 | **Sub-agents + skills** — main Nami + scoped workers (e.g. research, build notes) | Hermes | ~2h | Luke's "forklift to sub-agent" pattern; use Hermes skills/connectors, not Claude-only agents |
| 4 | **Daily brief routine** — cron/heartbeat that prepends Telegram context | Hermes | ~1–2h | Skill spec: [brief/SKILL.md](../../hermes-nami/skills/brief/SKILL.md) + [loop-checker/SKILL.md](../../hermes-nami/skills/loop-checker/SKILL.md); **first closed loop** per [LOOP_ENGINEERING.md](./LOOP_ENGINEERING.md) |
| 5 | **Gateway reliability** — gateway autostart + cron | Hermes | ~1h | Already on [STATUS.md](./STATUS.md) todo; PC sleep/off still blocks delivery until VPS migration |

## Design / build lane (PC — Cursor)

| Item | Surface | Status |
|------|---------|--------|
| **Claude design → export → Claude Code** for UI mockups | Cursor + external | Optional; Luke uses Claude design then Code — Ranne may prefer Cursor agent + stitch-app for product UI |
| **Scroll-frame landings** | Cursor | Shipped placeholder: `demos/scroll-frames/` |
| **linkup MCP** (search, RAG, whisper) | Hermes + Cursor | Done — re-run `.\scripts\install-nami-stack-pc.ps1` after pull on PC |

## Deferred / product-dependent (not Nami infra)

These appear in the reel but are **not** immediate Hermes backlog — wire only when a shipped app needs them:

| Mention | Luke / transcript | Why defer |
|---------|-------------------|-----------|
| **RevenueCat MCP** | App revenue tracking | Tied to mobile app SKU + store accounts |
| **Metricool** | Cross-platform posting | Marketing ops for a specific product |
| **Meta Ads MCP** | Paid ads automation | Campaign spend + Bobby-style agent is product-specific |
| **FAQ markdown → Claude CS** | 90% customer service | Needs 24/7 server + trained support skills — SupplyMe lane, not Nami v1 |
| **Full Jarvis clone** | Multiple sub-agents on Claude | Runtime is **Hermes**; Cursor builds tools, doesn't host the agent |

## Honest gaps (Luke is right)

- **Customer support via raw Claude** — insufficient without always-on harness, memory, and skills. Defer until SupplyMe or explicit CS scope.
- **"Claude for everything"** — Nami stack already diverges: Hermes + Ollama + linkup MCP + Cursor for code. Don't duplicate Claude Agent SDK on Mac unless there's a clear win.
- **Voice on PC** — ElevenLabs `nami-speak` is build-time/demo; runtime voice should be wired through Hermes when Ranne enables it.

## Verify after shipping priorities 1–3

```powershell
cd C:\Users\ranne\Cursor\cursor_linkup_mcp
.\scripts\install-nami-stack-pc.ps1
# Manual: trigger /brief in Telegram and confirm one read-only reply
```

## Source

- Transcript: `data/inbox/DZ5H6F1Rz1S.md`
- Workflow card: `data/inbox/DZ5H6F1Rz1S.workflow.md`
- Loop engineering: [LOOP_ENGINEERING.md](./LOOP_ENGINEERING.md) — `data/inbox/loop-engineering-sabrina.md`, `data/inbox/Ry3YyG22EUc.md`
- Surface map: [SURFACE_MAP.md](./SURFACE_MAP.md)
- Scorecard: [STATUS.md](./STATUS.md)
