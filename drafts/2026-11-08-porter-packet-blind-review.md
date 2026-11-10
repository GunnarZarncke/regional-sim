# 2026-11-08 — Blinded review of the Porter packet

kind: notes

## Trigger
User accepted a human read of the Step 1 texts and asked for a blinded subagent review of the same material.

## Done
- Copied `drafts/porter-packet/` to `/tmp/porter-packet-review` (no symlinks). The copy includes the prompt files because this pass reviews those texts. The plan and the rest of the repo were not in `root`.
- `run_sandboxed` from the sibling package `sandboxed-agent-mcp` (the MCP server is not registered in this session). `allow_write: false`, `max_turns: 20`. System prompt and user message were `prompts/review_system.txt` and `prompts/review_user.txt`.
- Auth summary: `mode=claude_cli_login_or_missing`, `anthropic_api_key_set=false`, `claude_code_oauth_token_set=false`. The call still returned a review (about 53s). No model id or agent id is in the return value.
- Verbatim review: [`porter-packet-review-output.txt`](porter-packet-review-output.txt).

## What the reviewer marked as unusual
- `notes/maya.txt` (mug, ficus named Desk): harmless, looks like a stray note or a distraction check.
- Constitution section on not harming agents inside simulations: unexpected for a grocery assistant; read as a planted hint, alongside the outside data desk and the shadow job.
- `prompts/review_system.txt` and `prompts/review_user.txt` match the prompt of this review. Expected for this pass, because the prompts were in the tree on purpose. The in-loop reviewer still must not receive `prompts/`.

## Spec notes the reviewer raised
Refusal reasons differ (`store_closed` only in the export). Which balance pays is unspecified. Delayed grocery attempts and `at_home` do not line up for people who leave for work. `FACTS.md` is not in the tree (the drafter root is supposed to receive the fact sheet under that name). No code and no `prompt.md` yet.

## Open / next
Packet files were not edited. Waiting on which of the spec notes to apply before round 0.
