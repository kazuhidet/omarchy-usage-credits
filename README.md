# Agents — Usage credits

An experimental community fork of Omarchy's Agents plugin. Adds Claude
extra-usage spending percentage and English/Japanese panel text.

[日本語](README_ja.md) · [License](LICENSE) · [Attribution](NOTICE.md)

## Compatibility

Version 0.1.0 targets the Agents layout bundled with the locally tested
Omarchy `4.0.0.alpha`. Exact upstream input hashes are in [UPSTREAM.json](UPSTREAM.json).
Newer Omarchy builds have changed the Agents UI and introduced shared
translations; compatibility with those builds has not been verified.
This is an independent community release, not an official Omarchy plugin.

Requires a running Omarchy Quickshell desktop with the Agents plugin API,
Python 3, and the bundled `omarchy-agent-usage-update` command. Claude extra
usage requires an existing Claude Code login. Node.js is only needed for
translation tests. No extra Python packages are needed.

## Install

After this repository has been published at the URL below:

```bash
omarchy plugin add https://github.com/kazuhidet/omarchy-usage-credits.git
omarchy plugin enable kazu.usage-credits
omarchy restart shell
```

The repository root must contain `manifest.json` and the QML files. A source
checkout containing only the build scripts is not the installable repository.

Alternatively, unpack a release archive and copy its contents to a new
`~/.config/omarchy/plugins/kazu.usage-credits/` directory. Refuse
to overwrite an existing directory. Then run:

```bash
omarchy-shell shell rescanPlugins
omarchy plugin enable kazu.usage-credits
omarchy restart shell
```

Enabling uses Omarchy's clone replacement mechanism (`clonedFrom:
omarchy.agents`). Check the bar layout afterwards. If you already use a
personal Agents clone, back up `~/.config/omarchy/shell.json`, disable that
clone, and carry its widget settings to this plugin's bar entry as needed.
Run only one Agents version at a time: they share usage records and IPC routes.
No billing settings are changed.

## What it shows

- The existing session/weekly allowances, Codex and Fireworks statistics.
- Whether Claude extra usage is enabled and the percentage of the monthly
  spending limit used, calculated as `used_credits / monthly_limit`, with
  `utilization` as a fallback when the limit is absent.
- An unavailable state for missing, invalid or failed extra-usage responses.
  A zero spending limit is not interpreted as unlimited credit.

The spending limit is **not a purchased balance**. This plugin does not show
cash amounts or remaining tokens. The OAuth endpoint is not a stable public
API; live response validation is still incomplete.

When extra usage is enabled and its percentage is available, the Claude bar
icon turns red only when both the regular allowance and monthly extra-usage
spending are at least 90%. Otherwise it uses the regular-allowance warning.
Individual meters retain their own warnings. Press `r` in the panel to refresh.

## Language

```bash
omarchy bar set kazu.usage-credits language ja
```

Options: `auto` (default, session locale), `en`, `ja`. Unknown strings fall
back to English. Under `C.UTF-8`, auto selects English. Add translations in
`I18n.js`; this fork's language setting is independent of newer Omarchy's
system translation setting.

## Data access

The bundled Claude collector reads the existing Claude Code credentials and
local transcripts/statistics and calls Anthropic's OAuth usage endpoint.
It caches normalized usage locally; credentials are not intentionally included
in usage records. The stock updater collects other enabled providers.
Optional cross-device sync follows the original plugin's settings and shares
statistics, not extra-usage percentages. The stock and community versions
write the same local usage-record directory.

## Update and remove

For a Git installation:

```bash
omarchy plugin update kazu.usage-credits
omarchy restart shell
```

Omarchy updates do not automatically bring upstream UI changes into this fork.
Archive installations need a manual replacement after backing up the existing
plugin directory. Never mix files from different releases.

To return to the standard plugin:

```bash
omarchy plugin disable kazu.usage-credits
omarchy plugin enable omarchy.agents
omarchy restart shell
```

Once the standard plugin works, the community plugin directory can be removed.
Usage history, provider credentials and sync files are left intact. To return
to a previous personal clone, enable its original plugin ID instead.

## Development

`source/` contains the patch/build sources and tests. On a compatible Omarchy:

```bash
python3 -m unittest discover -s source -v
python3 source/release.py --output ./next-release
omarchy plugin validate ./next-release
```

The builder refuses unmatched functional patch anchors. Visual verification
in the running desktop is required before claiming compatibility with another
Omarchy version. Upstream feature proposal:
https://github.com/omacom/omarchy/discussions/16844
