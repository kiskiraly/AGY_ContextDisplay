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

## 🔒 Privacy

- **100% Local & Offline:** Pure Python 3 standard library. Zero network calls, zero external packages.
- **No Content Leakage:** Only reads token integers and byte lengths from `transcript.jsonl` — never echoes prompt text, file paths, or command outputs.

## 📄 License

[MIT](LICENSE)
