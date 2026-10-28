import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from release import package, PLUGIN_ID


class Distribution(unittest.TestCase):
    def test_warning_patch_upgrades_previous_installation(self):
        from change_alert import NEW, patch
        previous = NEW.replace('      && extraUsage.percent !== null\n', '')
        self.assertEqual(patch(previous), NEW)
        self.assertEqual(patch(NEW), NEW)

    def test_native_bundle_contains_runtime_and_no_workstation_notes(self):
        with tempfile.TemporaryDirectory() as temp:
            public = package(Path(temp) / 'public')
            manifest = json.loads((public / 'manifest.json').read_text())
            self.assertEqual(manifest['id'], PLUGIN_ID)
            self.assertEqual(manifest['omarchy']['clonedFrom'], 'omarchy.agents')
            self.assertTrue((public / manifest['entryPoints']['barWidget']).is_file())
            self.assertTrue((public / 'claude-collector.py').is_file())
            self.assertIn('David Heinemeier Hansson', (public / 'LICENSE').read_text())
            for path in public.rglob('*'):
                self.assertNotIn(path.name, ('HANDOFF.md', 'AGENTS.md', '.aws', '.codex',
                                              '__pycache__', 'SUGGESTION_URL.txt'))
                if path.is_file() and path.suffix in ('.py', '.md', '.json', '.qml', '.js'):
                    self.assertNotIn(str(Path.home()) + '/', path.read_text())
            metadata = json.loads((public / 'UPSTREAM.json').read_text())
            self.assertIn('bin/omarchy-agent-usage-claude', metadata['filesSha256'])
            with self.assertRaises(FileExistsError):
                package(public)

    def test_unknown_extra_percentage_keeps_regular_warning(self):
        from change_alert import NEW
        node = shutil.which('node')
        if not node:
            self.skipTest('node is not installed')
        # Evaluate the QML property's actual expression across the warning states.
        expression = NEW.split('readonly property bool alarming: ', 1)[1].strip()
        script = '''
function alarm(normalLimitAlarming, extraUsage) {
  var provider = {providerId: "claude"};
  var balanceAlarming = false;
  var extraLimitAlarming = !!extraUsage && extraUsage.enabled
    && extraUsage.percent !== null && extraUsage.percent >= 0.9;
  return EXPRESSION;
}
console.log(JSON.stringify([
  alarm(true, null), alarm(true, {enabled: false, percent: null}),
  alarm(true, {enabled: true, percent: null}),
  alarm(true, {enabled: true, percent: 0.5}),
  alarm(true, {enabled: true, percent: 0.95}),
  alarm(false, {enabled: true, percent: 0.95})
]));
'''.replace('EXPRESSION', expression)
        result = subprocess.run([node, '-e', script], text=True, capture_output=True, check=True)
        self.assertEqual(json.loads(result.stdout), [True, True, True, False, True, False])


if __name__ == '__main__':
    unittest.main()
