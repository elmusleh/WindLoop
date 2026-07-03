# Security Considerations

## Unattended AI Execution

This tool allows an AI to edit files and run commands **without human oversight**.

**Risks:**
- AI may delete or overwrite files unexpectedly
- AI may run destructive commands if given access
- Cost accumulation if loop runs indefinitely due to a bug

**Mitigations:**
- Always commit/stash work before running
- Use `--dry-run` first
- Start with low `iterations` (e.g., 3)
- Review `logs/iterations.log` after each run
- Set a reasonable `timeout` so loops can't hang forever
- Run in a throwaway branch when experimenting

## xdotool Security

`xdotool` can type into any window. Ensure no sensitive windows are focused when the loop runs.

## Sentinel File

The sentinel path (`/tmp/cascade-loop.log`) is world-writable. Any process could write the done marker. In multi-user environments, use a path in your home directory instead.
