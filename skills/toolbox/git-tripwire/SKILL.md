---
name: git-tripwire
description: Set up Claude Code hooks to block dangerous git commands (push, reset --hard, clean, branch -D, etc.) before they execute. Use when user wants to prevent destructive git operations, add git safety hooks, or block git push/reset in Claude Code.
---

# Git Tripwire

A `PreToolUse` hook that catches a dangerous git command and stops it before Claude ever runs it — `git push` (including `--force`), `git reset --hard`, `git clean -f`/`-fd`, `git branch -D`, `git checkout .`/`git restore .`. When one trips the wire, Claude sees a message saying it doesn't have authority to run that command — not a crash, a refusal.

**Scope first.** This project only (`.claude/settings.json`) or every project on this machine (`~/.claude/settings.json`)? Ask before doing anything else.

**Place the script.** [scripts/guard.sh](scripts/guard.sh) is the bundled hook. Copy it to `.claude/hooks/guard.sh` (project scope) or `~/.claude/hooks/guard.sh` (global), then `chmod +x` it.

**Wire it into settings.** Merge this into `hooks.PreToolUse` in the target settings file — don't clobber whatever else is already there:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/guard.sh"
          }
        ]
      }
    ]
  }
}
```

(Global scope: same shape, `command` becomes `~/.claude/hooks/guard.sh` instead.)

**Offer customization.** Ask whether anything should be added to or dropped from the blocked-pattern list, and edit the copied script if so.

**Prove it works.** Feed the script a blocked command directly and confirm it exits 2 with a BLOCKED message on stderr:

```bash
echo '{"tool_input":{"command":"git push origin main"}}' | <path-to-script>
```
