#!/usr/bin/env python3
"""Create a curated repository and archive suitable for community distribution."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import tarfile
import tempfile

from build import build

ROOT = Path(__file__).resolve().parent
PLUGIN_ID = 'kazu.usage-credits'
VERSION = '0.1.0'
RUNTIME = ('manifest.json', 'Panel.qml', 'Main.qml', 'Agent.qml',
           'I18n.js', 'credits.py', 'update.py', 'claude-collector.py')
SOURCES = ('build.py', 'change_alert.py', 'credits.py', 'update.py',
           'i18n.py', 'I18n.js', 'release.py', 'test_credits.py', 'test_release.py')


def package(destination):
    if destination.exists():
        raise FileExistsError(f'{destination} already exists; choose a new output directory')
    upstream = Path(os.environ.get('OMARCHY_PATH', '/usr/share/omarchy'))
    with tempfile.TemporaryDirectory(prefix='usage-credits-release-') as temp:
        staged = build(Path(temp) / 'generated')
        public = Path(temp) / 'public'
        public.mkdir()
        (public / '.gitignore').write_text('__pycache__/\n*.py[cod]\n/source/dist/\n/next-release/\n')
        for name in RUNTIME:
            shutil.copy2(staged / name, public / name)
        shutil.copytree(staged / 'assets', public / 'assets')
        manifest = json.loads((public / 'manifest.json').read_text())
        manifest.update(id=PLUGIN_ID, name='Agents — Usage credits', version=VERSION,
                        author='Kazuhide Takahashi; based on Omarchy',
                        description='Claude extra-usage spending percentage with English and Japanese Agents panels.')
        manifest['barWidget']['displayName'] = manifest['name']
        manifest['barWidget']['aliases'] = ['usage-credits']
        (public / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        for source, target in [('README.md', 'README.md'),
                               ('README_ja.md', 'README_ja.md'),
                               ('LICENSE', 'LICENSE'), ('NOTICE.md', 'NOTICE.md')]:
            shutil.copy2(ROOT / source, public / target)
        dev = public / 'source'
        dev.mkdir()
        for name in SOURCES:
            shutil.copy2(ROOT / name, dev / name)
        # Keep release.py usable from source/ without shipping private work notes.
        for name in ('README.md', 'README_ja.md', 'LICENSE', 'NOTICE.md'):
            shutil.copy2(ROOT / name, dev / name)
        paths = sorted((upstream / 'shell/plugins/agents').rglob('*'))
        paths.append(upstream / 'bin/omarchy-agent-usage-claude')
        hashes = {str(p.relative_to(upstream)): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in paths if p.is_file() and '__pycache__' not in p.parts
                  and p.suffix != '.pyc'}
        metadata = {'omarchyVersion': (upstream / 'version').read_text().strip(),
                    'upstream': 'https://github.com/omacom/omarchy',
                    'filesSha256': hashes}
        (public / 'UPSTREAM.json').write_text(json.dumps(metadata, indent=2) + '\n')
        shutil.copytree(public, destination)
    return destination


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'publish')
    args = parser.parse_args()
    destination = package(args.output.resolve())
    dist = ROOT / 'dist'
    dist.mkdir(exist_ok=True)
    archive = dist / f'omarchy-usage-credits-{VERSION}.tar.gz'
    with tarfile.open(archive, 'w:gz') as bundle:
        bundle.add(destination, arcname=f'omarchy-usage-credits-{VERSION}')
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix(archive.suffix + '.sha256').write_text(f'{checksum}  {archive.name}\n')
    print(f'Public repository: {destination}\nArchive: {archive}')


if __name__ == '__main__':
    main()
