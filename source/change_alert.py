#!/usr/bin/env python3
"""Apply only the icon warning fix to an installed user plugin."""
from pathlib import Path
import datetime
import getpass
import os
import shutil

OLD = '''  readonly property bool alarming: (!!headline && headline.percent >= 0.9) || balanceAlarming
    || (!!extraUsage && extraUsage.enabled && extraUsage.percent !== null && extraUsage.percent >= 0.9)'''
NEW = '''  readonly property bool normalLimitAlarming: !!headline && headline.percent >= 0.9
  readonly property bool extraLimitAlarming: !!extraUsage && extraUsage.enabled
    && extraUsage.percent !== null && extraUsage.percent >= 0.9
  // Extra spending alone must not alarm after the normal allowance resets.
  readonly property bool alarming: balanceAlarming || (normalLimitAlarming
    && (provider && provider.providerId === "claude" && extraUsage && extraUsage.enabled
      && extraUsage.percent !== null
      ? extraLimitAlarming : true))'''


def patch(text):
    if NEW in text:
        return text
    previous = NEW.replace('      && extraUsage.percent !== null\n', '')
    if previous in text:
        return text.replace(previous, NEW)
    if text.count(OLD) != 1:
        raise RuntimeError('Unexpected Panel.qml version; no files changed')
    return text.replace(OLD, NEW).replace(
        '購入残高は未確認です。通常枠の警告は追加利用分を含みません。',
        '購入残高は未確認です。アイコンは通常枠と追加利用の両方が90%以上のときに警告します。')


if __name__ == '__main__':
    user = os.environ.get('USER') or getpass.getuser()
    target = Path.home() / '.config/omarchy/plugins' / (user + '.agents') / 'Panel.qml'
    original = target.read_text()
    updated = patch(original)
    if updated == original:
        print('Already updated')
    else:
        backup = target.with_name('Panel.qml.bak.' + datetime.datetime.now().strftime('%Y%m%d%H%M%S%f'))
        shutil.copy2(target, backup)
        target.write_text(updated)
        print('Updated:', target)
        print('Backup:', backup)
        print('Run omarchy-restart-shell to apply (hot reload keeps the cached QML)')
