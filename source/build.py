#!/usr/bin/env python3
"""Build a user plugin against the installed Omarchy version."""
import json
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def replace(path, old, new):
    text = path.read_text()
    if text.count(old) != 1:
        raise RuntimeError(f'Unsupported Omarchy version: {path.name}: expected one patch anchor')
    path.write_text(text.replace(old, new))

def build(out):
    source = Path(os.environ.get('OMARCHY_PATH', '/usr/share/omarchy'))
    shutil.copytree(source / 'shell/plugins/agents', out,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.git'))
    manifest = json.loads((out / 'manifest.json').read_text())
    manifest['id'] = 'kazu.agents-credits'
    manifest['name'] = 'Agents with usage credits'
    manifest['barWidget']['displayName'] = manifest['name']
    manifest.setdefault('omarchy', {})['clonedFrom'] = 'omarchy.agents'
    widget = manifest['barWidget']
    widget.setdefault('defaults', {})['language'] = 'auto'
    widget.setdefault('schema', []).append({
        'key': 'language',
        'type': 'enum',
        'label': 'Language',
        'options': ['auto', 'en', 'ja'],
        'defaultValue': 'auto',
        'description': 'Panel language. auto follows the session locale.',
    })
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    shutil.copy2(ROOT / 'credits.py', out / 'credits.py')
    shutil.copy2(ROOT / 'update.py', out / 'update.py')
    shutil.copy2(ROOT / 'I18n.js', out / 'I18n.js')
    collector = out / 'claude-collector.py'
    shutil.copy2(source / 'bin/omarchy-agent-usage-claude', collector)
    replace(collector, 'from __future__ import annotations', 'from __future__ import annotations\nfrom credits import normalize_extra_usage')
    replace(collector, 'return {"ok": True, "limits": limits}', 'return {"ok": True, "limits": limits, "extraUsage": normalize_extra_usage(payload.get("extra_usage"))}')
    replace(collector, 'result["limits"] = fallback\n    return result\n\n  probe =', 'result["limits"] = fallback\n    result["extraUsage"] = cached.get("extraUsage")\n    return result\n\n  probe =')
    replace(collector, 'result["limits"] = probe["limits"]\n    write_json(probe_cache, {"fetchedAtMs": round(time.time() * 1000), "limits": probe["limits"]})', 'result["limits"] = probe["limits"]\n    result["extraUsage"] = probe.get("extraUsage")\n    write_json(probe_cache, {"fetchedAtMs": round(time.time() * 1000), "limits": probe["limits"], "extraUsage": probe.get("extraUsage")})')
    replace(collector, '"limits": limits["limits"],\n  }', '"limits": limits["limits"],\n    "extraUsage": limits.get("extraUsage"),\n  }')
    # Keep the private collector cache separate from the stock collector.
    replace(collector, '"claude-limits.json"', '"claude-credits-limits.json"')
    replace(out / 'Main.qml', 'var command = ["omarchy-agent-usage-update"]', 'var command = ["python3", Qt.resolvedUrl("update.py").toString().replace(/^file:\\/\\//, "")]')
    replace(out / 'Main.qml', 'balance: balanceValue(record.balance),', 'balance: balanceValue(record.balance),\n      extraUsage: record.extraUsage || null,')
    panel = out / 'Panel.qml'
    replace(panel, 'readonly property var balance: provider ? (provider.balance || null) : null', 'readonly property var balance: provider ? (provider.balance || null) : null\n  readonly property var extraUsage: provider ? (provider.extraUsage || null) : null')
    from change_alert import NEW
    replace(panel, '  readonly property bool alarming: (!!headline && headline.percent >= 0.9) || balanceAlarming', NEW)
    replace(panel, '// ---------- Balance / limits ----------', '''// ---------- Usage credits ----------
          PanelSeparator {
            visible: !!root.provider && root.provider.providerId === "claude"
            foreground: root.foreground
          }
          Column {
            visible: !!root.provider && root.provider.providerId === "claude"
            width: parent.width
            spacing: Style.space(8)
            PanelSectionHeader {
              text: root.tr("USAGE CREDITS")
              foreground: root.foreground
              fontFamily: root.fontFamily
            }
            Text {
              width: parent.width
              textFormat: Text.PlainText
              text: !root.extraUsage ? root.tr("Usage credit info unavailable (press r to refresh)")
                : !root.extraUsage.enabled ? root.tr("Usage credits are off")
                : root.extraUsage.percent === null ? root.tr("Usage credits on · usage rate unavailable")
                : root.tr("%1% of monthly spending limit used", (root.extraUsage.percent * 100).toFixed(1))
              color: root.foreground
              font.family: root.fontFamily
              font.pixelSize: Style.font.body
              wrapMode: Text.WordWrap
            }
            Meter {
              visible: !!root.extraUsage && root.extraUsage.enabled && root.extraUsage.percent !== null
              width: parent.width
              value: root.extraUsage && root.extraUsage.percent !== null ? root.clamp(root.extraUsage.percent, 0, 1) : 0
              alarming: !!root.extraUsage && root.extraUsage.percent !== null && root.extraUsage.percent >= 0.9
            }
            Text {
              width: parent.width
              textFormat: Text.PlainText
              text: root.tr("Purchased balance is not checked. The icon warns only when both the regular allowance and usage credits are at 90% or more.")
              color: root.dim
              font.family: root.fontFamily
              font.pixelSize: Style.font.caption
              wrapMode: Text.WordWrap
            }
          }

          // ---------- Balance / limits ----------''')
    import i18n
    i18n.apply(panel)
    return out

if __name__ == '__main__':
    import sys
    build(Path(sys.argv[1]))
