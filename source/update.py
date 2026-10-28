#!/usr/bin/env python3
"""Refresh stock providers, replacing only the Claude collector."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    flags, selected, excluded = [], [], set()
    args = iter(sys.argv[1:])
    for arg in args:
        if arg in ('--force', '--limits-only'):
            flags.append(arg)
        elif arg == '--except':
            excluded.add(next(args))
        elif arg.startswith('-'):
            raise ValueError('Unknown option: ' + arg)
        else:
            selected.append(arg)
    # The stock updater owns the other providers, including future additions.
    command = ['omarchy-agent-usage-update', *flags, '--except', 'claude']
    for agent in excluded - {'claude'}:
        command.extend(['--except', agent])
    if selected:
        command.extend(selected)
    status = subprocess.call(command)
    if 'claude' in excluded or (selected and 'claude' not in selected):
        return status
    result = subprocess.run([sys.executable, str(Path(__file__).with_name('claude-collector.py')), *flags], capture_output=True, text=True)
    if result.returncode:
        # Never expose collector output: it may contain private data.
        print('Claude credits collector failed; keeping previous usage record', file=sys.stderr)
        return 1
    record = json.loads(result.stdout)
    target = Path(os.environ.get('XDG_STATE_HOME', str(Path.home() / '.local/state'))) / 'omarchy/agents/usage'
    target.mkdir(parents=True, exist_ok=True)
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', dir=target, prefix='.claude-credits-', delete=False) as stream:
            tmp = Path(stream.name)
            json.dump(record, stream)
            stream.write('\n')
        tmp.replace(target / 'claude.json')
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)
    return status


if __name__ == '__main__':
    raise SystemExit(main())
