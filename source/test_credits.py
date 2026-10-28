import json
import runpy
import tempfile
import unittest
from pathlib import Path
from credits import normalize_extra_usage


class Normalization(unittest.TestCase):
    def test_spend_cap_is_not_cash_balance(self):
        result = normalize_extra_usage({'is_enabled': True, 'monthly_limit': 5000, 'used_credits': 1250})
        self.assertEqual(result, {'enabled': True, 'percent': .25})
        self.assertNotIn('remaining', result)

    def test_disabled(self):
        self.assertFalse(normalize_extra_usage({'is_enabled': False})['enabled'])

    def test_missing_and_changed_schema(self):
        for value in (None, [], {}, {'is_enabled': 'true'}):
            self.assertIsNone(normalize_extra_usage(value))

    def test_percentage_fallback(self):
        self.assertEqual(normalize_extra_usage({'is_enabled': True, 'utilization': 0.5})['percent'], .005)

    def test_invalid_amounts_and_zero_cap(self):
        for cap in (0, -1, 'NaN', True):
            self.assertIsNone(normalize_extra_usage({'is_enabled': True, 'monthly_limit': cap, 'used_credits': 0})['percent'])

    def test_exhausted_cap(self):
        self.assertGreaterEqual(normalize_extra_usage({'is_enabled': True, 'monthly_limit': 10, 'used_credits': 11})['percent'], 1)


class Collector(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        # Test a fresh build, rather than an older checked-in preview.
        from build import build
        plugin = build(Path(self.tmp.name) / 'plugin')
        self.module = runpy.run_path(str(plugin / 'claude-collector.py'))
        self.collect = self.module['collect_limits']
        self.env = self.collect.__globals__
        self.env['cache_root'] = lambda: Path(self.tmp.name)
        self.limit = {'label': 'Weekly (7-day)', 'percent': 1.0, 'resetsAt': '2099-01-01T00:00:00+00:00'}
        self.extra = {'enabled': True, 'percent': .25}
        self.env['probe_limits'] = lambda _: {'ok': True, 'limits': [self.limit], 'extraUsage': self.extra}

    def test_refresh_and_cache_keep_extra_usage(self):
        self.assertEqual(self.collect('fake-test-token', 0, True)['extraUsage'], self.extra)
        def unexpected(_):
            self.fail('cache hit must not contact network')
        self.env['probe_limits'] = unexpected
        self.assertEqual(self.collect('fake-test-token', 0, False)['extraUsage'], self.extra)

    def test_failure_does_not_reuse_old_credit_status(self):
        self.collect('fake-test-token', 0, True)
        self.env['probe_limits'] = lambda _: {'ok': False, 'helpText': 'offline', 'transport': True}
        result = self.collect('fake-test-token', 0, True)
        self.assertIsNone(result.get('extraUsage'))
        self.assertEqual(result['limits'], [self.limit])

    def test_expired_auth_does_not_claim_extra_available(self):
        self.collect('fake-test-token', 0, True)
        self.assertIsNone(self.collect('fake-test-token', 1, False).get('extraUsage'))

    def test_real_probe_carries_extra_and_ignores_secrets(self):
        probe = self.module['probe_limits']
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self):
                return json.dumps({'five_hour': {'utilization': 100}, 'extra_usage': {'is_enabled': True, 'monthly_limit': 100, 'used_credits': 20, 'secret': 'never-copy'}}).encode()
        from unittest.mock import patch
        with patch('urllib.request.urlopen', return_value=Response()):
            result = probe('fake-test-token')
        self.assertEqual(result['extraUsage'], {'enabled': True, 'percent': .2})
        self.assertNotIn('never-copy', json.dumps(result))


class Updater(unittest.TestCase):
    def test_replaces_only_claude_and_writes_record_atomically(self):
        from unittest.mock import patch
        import update
        import subprocess
        with tempfile.TemporaryDirectory() as temp:
            record = {'id': 'claude', 'extraUsage': {'enabled': True, 'percent': .2}}
            result = subprocess.CompletedProcess([], 0, json.dumps(record), '')
            with patch.dict('os.environ', {'XDG_STATE_HOME': temp}), \
                 patch('sys.argv', ['update.py', '--force', '--except', 'codex']), \
                 patch('subprocess.call', return_value=0) as stock, \
                 patch('subprocess.run', return_value=result):
                self.assertEqual(update.main(), 0)
            command = stock.call_args.args[0]
            self.assertIn('--force', command)
            self.assertIn('claude', command)
            self.assertIn('codex', command)
            target = Path(temp) / 'omarchy/agents/usage/claude.json'
            self.assertEqual(json.loads(target.read_text()), record)
            self.assertEqual(len(list(target.parent.iterdir())), 1)

    def test_disabled_claude_is_not_probed(self):
        from unittest.mock import patch
        import update
        with patch('sys.argv', ['update.py', '--except', 'claude']), \
             patch('subprocess.call', return_value=0), \
             patch('subprocess.run') as collector:
            self.assertEqual(update.main(), 0)
            collector.assert_not_called()


class Translation(unittest.TestCase):
    def setUp(self):
        import shutil
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.node = shutil.which('node')

    def run_js(self, expression):
        import subprocess
        source = Path(__file__).with_name('I18n.js').read_text().replace('.pragma library', '')
        script = source + '\nconsole.log(JSON.stringify(' + expression + '))'
        return json.loads(subprocess.run([self.node, '-e', script], capture_output=True, text=True, check=True).stdout)

    def test_every_panel_key_is_translated(self):
        import contextlib
        import io
        import re
        from build import build
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            panel = (build(Path(self.tmp.name) / 'plugin') / 'Panel.qml').read_text()
        self.assertEqual(stderr.getvalue(), '')
        keys = set()
        for match in re.finditer(r'root\.tr\((\[[^\]]*\]|[^,)]*\?[^:]*:[^,)]*|"(?:[^"\\]|\\.)*")', panel):
            keys.update(json.loads('"' + s + '"') for s in re.findall(r'"((?:[^"\\]|\\.)*)"', match.group(1)))
        if not self.node:
            self.skipTest('node is not installed')
        missing = self.run_js('%s.filter(function(k) { return !(k in tables.ja) })' % json.dumps(sorted(keys)))
        self.assertEqual(missing, [])
        self.assertGreater(len(keys), 30)

    def test_lookup(self):
        if not self.node:
            self.skipTest('node is not installed')
        self.assertEqual(self.run_js('[resolve("", "ja_JP"), resolve("auto", "C"), resolve("ja", "en_US"), resolve("xx", "ja_JP")]'), ['ja', 'en', 'ja', 'en'])
        self.assertEqual(self.run_js('[tr("en", "Resets in %1", ["2h"]), tr("ja", "Resets in %1", ["2時間"]), tr("ja", "%1% of monthly spending limit used", ["99.3"])]'),
                         ['Resets in 2h', '2時間後にリセット', '月間支出上限の 99.3% を消費'])
        self.assertEqual(self.run_js('[message("ja", "Fable Weekly"), message("ja", "Anthropic\'s usage endpoint returned status 500. Local Claude Code stats are still shown."), message("ja", "boom"), message("en", "Waiting for auth")]'),
                         ['Fable 週間', 'Anthropicの利用状況エンドポイントがステータス 500 を返しました。ローカルのClaude Code統計は引き続き表示します。', 'boom', 'Waiting for auth'])


if __name__ == '__main__':
    unittest.main()
