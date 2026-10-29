"""Package an already built Agent; never builds or reads another checkout."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import shutil
import subprocess


def package(binary, output, version, target, notices, url=None):
    if not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?', version) or not re.fullmatch(r'[a-zA-Z0-9_]+(?:-[a-zA-Z0-9_]+){2,}', target):
        raise ValueError('An exact version and target triple are required')
    actual = subprocess.check_output([str(binary.resolve()), '--version'], text=True).strip()
    if actual != f'llmn-agent {version}':
        raise ValueError(f'Agent version mismatch: {actual!r}')
    if url and not url.startswith('https://'):
        raise ValueError('Published artifact URL must use HTTPS')
    notice_bytes = notices.read_bytes()
    if not notice_bytes.decode('utf-8').strip():
        raise ValueError('Third-party notices must be nonempty UTF-8 text')
    license_root = Path(__file__).resolve().parents[1]
    own_licenses = {name: (license_root / name).read_bytes() for name in ('LICENSE', 'NOTICE')}
    output.mkdir(parents=True, exist_ok=True)
    name = f'llmn-agent-{version}-{target}' + ('.exe' if 'windows' in target else '')
    destination = output / name
    if any(output.iterdir()):
        raise ValueError('Artifact or manifest already exists; choose an empty output directory')
    shutil.copy2(binary, destination)
    notice_name = f'THIRD_PARTY_NOTICES-{version}-{target}.txt'
    (output / notice_name).write_bytes(notice_bytes)
    for license_name, data in own_licenses.items():
        (output / license_name).write_bytes(data)
    entry = {'sha256': hashlib.sha256(destination.read_bytes()).hexdigest(), 'file': name}
    entry['notices'] = {'file': notice_name, 'sha256': hashlib.sha256(notice_bytes).hexdigest()}
    if url:
        entry['url'] = url
    manifest = {'schemaVersion': 1, 'agentVersion': version, 'artifacts': {target: entry}}
    (output / 'agent-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    return destination


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--binary', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--version', required=True)
    p.add_argument('--target', required=True)
    p.add_argument('--notices', type=Path, required=True)
    p.add_argument('--url')
    a = p.parse_args()
    print(package(a.binary, a.output, a.version, a.target, a.notices, a.url))
