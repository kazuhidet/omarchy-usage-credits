"""Route the stock panel's visible text through I18n.js.

Unlike the functional patches in build.py, a translation anchor that no
longer matches only leaves that text in English, so it warns instead of
stopping the build.
"""
import sys

PANEL = [
    ('import qs.Ui\n', 'import qs.Ui\nimport "I18n.js" as I18n\n'),
    ('  readonly property string fontFamily: bar ? bar.fontFamily : Style.font.family\n',
     '''  readonly property string fontFamily: bar ? bar.fontFamily : Style.font.family
  // shell.json: "language": "ja" | "en" | "auto" (session locale).
  readonly property string lang: I18n.resolve(root.settings ? root.settings.language : "", Qt.locale().name)
  function tr(text) { return I18n.tr(lang, text, Array.prototype.slice.call(arguments, 1)) }
  function msg(text) { return I18n.message(lang, text) }
'''),
    ('if (!(ms > 0)) return "now"', 'if (!(ms > 0)) return root.tr("now")'),
    ('''    if (days > 0) return days + "d " + (hours % 24) + "h"
    if (hours > 0) return hours + "h " + (minutes % 60) + "m"
    return Math.max(1, minutes) + "m"''',
     '''    if (days > 0) return root.tr("%1d %2h", days, hours % 24)
    if (hours > 0) return root.tr("%1h %2m", hours, minutes % 60)
    return root.tr("%1m", Math.max(1, minutes))'''),
    ('''    var text = formatMoney(b.spent, b.currency) + " spent of " + formatMoney(b.funded, b.currency) + " funded"
    if (b.estimated) text += " · estimated"''',
     '''    var text = root.tr("%1 spent of %2 funded", formatMoney(b.spent, b.currency), formatMoney(b.funded, b.currency))
    if (b.estimated) text += root.tr(" · estimated")'''),
    ('if (String(p.usageStatusText || "") !== "") return p.usageStatusText',
     'if (String(p.usageStatusText || "") !== "") return root.msg(p.usageStatusText)'),
    ('if (tier === "") return "Subscription"\n    return tier.charAt(0).toUpperCase() + tier.slice(1)',
     'if (tier === "") return root.tr("Subscription")\n    return root.msg(tier.charAt(0).toUpperCase() + tier.slice(1))'),
    ('return ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][parsed.getDay()]',
     'return root.tr(["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][parsed.getDay()])'),
    ('if (today) return "Today"', 'if (today) return root.tr("Today")'),
    ('var text = label + " · " + usage.formatTokenCount(Number(day.messageCount || 0)) + " tokens"',
     'var text = label + " · " + root.tr("%1 tokens", usage.formatTokenCount(Number(day.messageCount || 0)))'),
    ('''      text += " · " + Number(provider.todayPrompts || 0) + " prompts · "
        + Number(provider.todaySessions || 0) + " sessions"''',
     '''      text += " · " + root.tr("%1 prompts · %2 sessions",
        Number(provider.todayPrompts || 0), Number(provider.todaySessions || 0))'''),
    ('''    return "In " + usage.formatTokenCount(row.input)
      + " · out " + usage.formatTokenCount(row.output)
      + " · cache read " + usage.formatTokenCount(row.cacheRead)
      + " · cache write " + usage.formatTokenCount(row.cacheWrite)''',
     '''    return root.tr("In %1 · out %2 · cache read %3 · cache write %4",
      usage.formatTokenCount(row.input), usage.formatTokenCount(row.output),
      usage.formatTokenCount(row.cacheRead), usage.formatTokenCount(row.cacheWrite))'''),
    ('if (usage.syncStatusText !== "") return usage.syncStatusText',
     'if (usage.syncStatusText !== "") return root.msg(usage.syncStatusText)'),
    ('return "Merged from " + provider.syncDeviceCount + " device" + (provider.syncDeviceCount === 1 ? "" : "s")',
     'return root.tr(provider.syncDeviceCount === 1 ? "Merged from %1 device" : "Merged from %1 devices", provider.syncDeviceCount)'),
    ('''text: "No AI coding subscriptions found.\\nAgents show up here once you've used them."''',
     '''text: root.tr("No AI coding subscriptions found.\\nAgents show up here once you've used them.")'''),
    ('text: root.provider ? String(root.provider.authHelpText || "") : ""',
     'text: root.provider ? root.msg(root.provider.authHelpText) : ""'),
    ('text: "BALANCE"', 'text: root.tr("BALANCE")'),
    ('text: "Prepaid credits"', 'text: root.tr("Prepaid credits")'),
    ('text: "LIMITS"', 'text: root.tr("LIMITS")'),
    ('text: "TOKENS BY DAY"', 'text: root.tr("TOKENS BY DAY")'),
    ('text: "TOKENS BY MODEL"', 'text: root.tr("TOKENS BY MODEL")'),
    ('text: limitRow.window ? limitRow.window.title : ""', 'text: limitRow.window ? root.msg(limitRow.window.title) : ""'),
    ('"Resets in " + root.formatDuration(remainingMs)', 'root.tr("Resets in %1", root.formatDuration(remainingMs))'),
]


def apply(path, patches=PANEL):
    text = path.read_text()
    missing = []
    for index, (old, new) in enumerate(patches):
        # The import and the helpers are what every other patch calls.
        if index < 2 and text.count(old) != 1:
            raise RuntimeError(f'Unsupported Omarchy version: {path.name}: expected one i18n anchor')
        if text.count(old) == 1:
            text = text.replace(old, new)
        else:
            missing.append(old.strip().splitlines()[0])
    path.write_text(text)
    for anchor in missing:
        print(f'warning: {path.name}: translation anchor not found, left in English: {anchor}', file=sys.stderr)
    return missing
