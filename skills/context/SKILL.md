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
2. **Fallback Path:** Otherwise, run:
   ```bash
   python3 ~/.local/bin/agy-context-hook --panel
   ```
   and display the output inside a `text` code block.
