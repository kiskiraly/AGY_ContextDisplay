---
name: context
description: >-
  Display the Antigravity CLI-style `/context` 10x10 visual grid and category-by-category
  token breakdown (`⛁` System & customizations, `◉` User messages, `◉` Agent responses,
  `◉` Tool calls, `□` Free space, `⊠` Compaction checkpoints) in chat. Triggered by /context.
---

# Context Usage Panel (`/context`)

When the user runs `/context` (or asks to view the full context window breakdown):

1. **Zero-Tool Path (Preferred):** If `<context_status_badge>` in the current turn already includes the pre-rendered `Antigravity Context Usage (/context)` 10x10 grid block, output that exact `text` code block directly without calling any tools.
2. **Fallback Path:** Otherwise, run the installed hook script with `--panel` using the appropriate Python command and path for the current OS and display the output inside a `text` code block:
   - **macOS / Linux:**
     ```bash
     python3 ~/.gemini/hooks/agy-context-hook.py --panel
     ```
     *(or `agy-context-hook --panel` / `python3 ~/.local/bin/agy-context-hook --panel` if installed there)*
   - **Windows (`cmd` / PowerShell):**
     ```powershell
     python "%USERPROFILE%\.gemini\hooks\agy-context-hook.py" --panel
     ```
     *(or `py -3 "$env:USERPROFILE\.gemini\hooks\agy-context-hook.py" --panel` in PowerShell)*
