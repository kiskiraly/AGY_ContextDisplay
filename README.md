# AGY_CoontextDisplay (`agy-context-hook`)

> **100% vibecoded with Gemini inside Google Antigravity.**

Brings the [Antigravity CLI `/context`](https://antigravity.google/docs/cli/commands/context/) visual gauge and token breakdown directly into the **Antigravity 2.0 Desktop Chat UI** — plus an on-demand `/context` 10×10 grid panel — using a single zero-dependency Python hook.

```text
🟢 ◉□□□□□□□□□ 100.5k / 1M (10.1%) · ⛁ Sys 11.9k · ◉ Msg 22.1k · ◉ Tools 66.5k · Δ +7.9k · ⚡ 97% cached · ⊠ 1 checkpoint
```

---

## 🎯 Goal & How It Works

Antigravity 2.0's desktop chat doesn't natively display live context window fullness or the CLI's `/context` panel, making it easy to hit surprise compactions during heavy coding sessions.

**`agy-context-hook`** solves this with a lightweight `PreInvocation` hook:
1. **Reads Server Telemetry Locally:** Parses the active session's `transcript.jsonl` (`input_tokens`, `cache_read_tokens`, `output_tokens`) in pure Python — the model never counts or estimates tokens itself.
2. **CLI-Style Category Breakdown:** Splits active context across the official CLI `/context` categories:
   - `⛁ Sys` — System prompt, built-in tools, rules, skills & MCP schemas
   - `◉ Msg` — User messages + Agent responses & reasoning
   - `◉ Tools` — Tool calls & command outputs
   - `□ Free` — Remaining capacity in the `1M` window
   - `Δ` / `⚡` / `⊠` — Net turn growth, prompt cache hit rate, and compaction checkpoints
3. **Ephemeral Injection:** Injects the pre-computed single-line badge via `ephemeralMessage` so it renders at the bottom of every reply without accumulating in conversation history across turns.
4. **Traffic-Light Compaction Alerts:**
   - `🟢` `< 25%` · `🟡` `25–50%` · `🟠` `50–75%` (`💡 Consider /compact`) · `🔴` `>= 75%` (`⚠️ High context — run /compact`)

---

## 📊 Full `/context` 10×10 Panel (In-Chat or Terminal)

Send `/context` in chat (zero tool calls) or run `agy-context-hook --panel` in your terminal to render the full CLI-style 10×10 grid:

```text
  Antigravity Context Usage (/context)

  ⛁ ◉ ◉ ◉ ◉ ◉ ◉ ◉ ◉ ◉    🟢 Context Usage: 100.5k / 1M (10.1%)
  □ □ □ □ □ □ □ □ □ □    ────────────────────────────────────────────────
  □ □ □ □ □ □ □ □ □ □    ⛁ System & customizations :   11.9k (  1.2%)
  □ □ □ □ □ □ □ □ □ □    ◉ User messages           :    1.0k (  0.1%)
  □ □ □ □ □ □ □ □ □ □    ◉ Agent responses         :   21.0k (  2.1%)
  □ □ □ □ □ □ □ □ □ □    ◉ Tool calls              :   66.5k (  6.6%)
  □ □ □ □ □ □ □ □ □ □    □ Free space              :  899.5k ( 89.9%)
  □ □ □ □ □ □ □ □ □ □    ────────────────────────────────────────────────
  □ □ □ □ □ □ □ □ □ □    Δ Last turn growth        :   +7.9k
  □ □ □ □ □ □ □ □ □ □    ⚡ Prompt cache hit rate   :     97%
                         ⊠ Compaction checkpoints  :       1
```

---

## 🚀 Quick Install

1. **Install the hook & optional `/context` skill:**
   ```bash
   mkdir -p ~/.local/bin ~/.gemini/config/skills/context
   cp agy-context-hook ~/.local/bin/agy-context-hook
   chmod +x ~/.local/bin/agy-context-hook
   cp skills/context/SKILL.md ~/.gemini/config/skills/context/SKILL.md
   ```

2. **Add to `~/.gemini/config/hooks.json` (see [`hooks.example.json`](hooks.example.json)):**
   ```json
   {
     "context-status-hook": {
       "PreInvocation": [
         {
           "type": "command",
           "command": "python3 ~/.local/bin/agy-context-hook pre || echo {}",
           "timeout": 4
         }
       ]
     }
   }
   ```
   *(Set `AGY_CONTEXT_WINDOW=200000` if using a model with a non-`1M` context window.)*

---

## 🖥️ Supported Surfaces & Cloud / Remote Limitations

| Surface | `<app_data_dir>` | Status | Notes |
| :--- | :--- | :---: | :--- |
| **Antigravity App (Desktop)** | `~/.gemini/antigravity` | ✅ Supported | Full live badge + `/context` panel |
| **Antigravity IDE** | `~/.gemini/antigravity-ide` | ✅ Supported | Full live badge + `/context` panel |
| **Antigravity CLI (`agy`) & [Remote Control](https://antigravity.google/docs/remote-control/)** | `~/.gemini/antigravity-cli` | ✅ Supported | Works locally and on self-hosted Linux servers/VMs via Remote Control |
| **Google-Managed [Remote Agents](https://antigravity.google/docs/remote-agents/) (`jetski` Cloud VMs)** | `/shared/user/.gemini/jetski` | ❌ Unsupported | Blocked by cloud container isolation (see below) |

### Why Google-Managed Remote Agents (`jetski` Cloud VMs) Aren't Supported
Empirically tested inside Google's managed Debian 12 Remote Agent VMs (`jetski_remote_agents_3p`):
1. **External Control Plane (`hooks.json` Not Evaluated):** In Google-managed Remote Agents, the `PreInvocation` / `PostToolUse` loop executes inside Google's cloud orchestrator outside the tool-execution VM. Lifecycle hooks in `~/.gemini/config/hooks.json` and `.agents/hooks.json` are never invoked on turn boundaries (`Lifecycle hooks` are currently scoped to App, CLI, and IDE only).
2. **No Container-Side `transcript.jsonl`:** While Google mounts `.system_generated/tasks/` and artifacts into `/shared/user/.gemini/jetski/brain/...`, `.system_generated/logs/transcript.jsonl` (`input_tokens`, `cache_read_tokens`, `output_tokens`) is retained server-side and is not accessible from inside the VM.
3. **Workaround:** To inspect exact context telemetry on a Google-managed Remote Agent thread, attach from a terminal with `agy --remote-agent -c` (or `--conversation=<id>`) and run the built-in CLI `/context` command — or run remote sessions on your own workstation/server using **[Remote Control](https://antigravity.google/docs/remote-control/)**, where `hooks.json` and `transcript.jsonl` execute locally.

---

## 🔒 Privacy

- **100% Local & Offline:** Pure Python 3 standard library. Zero network calls, zero external packages.
- **No Content Leakage:** Only reads token integers and byte lengths from `transcript.jsonl` — never echoes prompt text, file paths, or command outputs.

## 📄 License

[MIT](LICENSE)
