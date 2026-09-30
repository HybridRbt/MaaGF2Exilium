"""Install a version-specific resource patch using the bundled Python (stdlib only)."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

OPTION = '极限峰值：槽位未满仍开始作战'
LABELS = [OPTION, '极限峰值缺员作战说明']
BACKUP = '.dialog-patch-backup'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def encode_json(data):
    return (json.dumps(data, ensure_ascii=False, indent=4) + '\n').encode('utf-8')


def safe_path(root, rel):
    path = (root / rel).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Invalid package path: ' + rel)
    return path


def write_atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.dialog-patch-tmp')
    try:
        temporary.write_bytes(data)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def apply(root, package):
    root, package = Path(root).resolve(), Path(package).resolve()
    manifest = read_json(package / 'manifest.json')
    interface = read_json(root / 'interface.json')
    if interface.get('version') != manifest['resource_version']:
        raise ValueError('Expected resource ' + manifest['resource_version'] + '; installed: ' + str(interface.get('version')))
    backup = root / BACKUP
    if backup.exists():
        raise ValueError('Backup already exists. Roll back the previous patch before applying again.')
    staged = {}
    for item in manifest['files']:
        rel = item['path']
        target = safe_path(root, rel)
        expected = item['before_sha256']
        if expected is None:
            if target.exists():
                raise ValueError('New patch file already exists: ' + rel)
        elif not target.is_file() or digest(target.read_bytes()) != expected:
            raise ValueError('Installed file differs from v2.7.2: ' + rel)
        content = safe_path(package / 'payload', rel).read_bytes()
        if digest(content) != item['after_sha256']:
            raise ValueError('Package file is damaged: ' + rel)
        staged[rel] = content
    additions = read_json(package / 'interface-additions.json')
    if OPTION in interface['option']:
        raise ValueError('Patch option already exists.')
    task = next(t for t in interface['task'] if t['name'] == '模拟作战日常')
    if OPTION not in task['option']:
        task['option'].append(OPTION)
    interface['option'][OPTION] = additions['option']
    staged['interface.json'] = encode_json(interface)
    for lang, labels in additions['labels'].items():
        rel = interface['languages'][lang]
        target = safe_path(root, rel)
        current = read_json(target)
        current.update(labels)
        staged[rel] = encode_json(current)
    # Validate everything before creating a backup or changing installed resources.
    originals = {rel: safe_path(root, rel).read_bytes() if safe_path(root, rel).exists() else None for rel in staged}
    backup.mkdir()
    state = {'files': []}
    for rel, content in originals.items():
        if content is not None:
            dst = safe_path(backup / 'original', rel)
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(content)
        state['files'].append({'path': rel, 'existed': content is not None, 'patched_sha256': digest(staged[rel])})
    (backup / 'state.json').write_bytes(encode_json(state))
    written = []
    try:
        for rel, content in staged.items():
            write_atomic(safe_path(root, rel), content)
            written.append(rel)
    except Exception:
        for rel in reversed(written):
            target = safe_path(root, rel)
            if originals[rel] is None:
                target.unlink(missing_ok=True)
            else:
                write_atomic(target, originals[rel])
        shutil.rmtree(backup)
        raise
    return len(staged)


def rollback(root):
    root = Path(root).resolve()
    backup = root / BACKUP
    state = read_json(backup / 'state.json')
    # Refuse to overwrite resource updates or edits made after patch installation.
    for item in state['files']:
        target = safe_path(root, item['path'])
        if not target.is_file() or digest(target.read_bytes()) != item['patched_sha256']:
            raise ValueError('File changed after patch installation; manual review needed: ' + item['path'])
    for item in state['files']:
        target = safe_path(root, item['path'])
        if item['existed']:
            write_atomic(target, safe_path(backup / 'original', item['path']).read_bytes())
        else:
            target.unlink()
    shutil.rmtree(backup)


def main():
    package = Path(__file__).resolve().parent
    root = package.parent
    try:
        if len(sys.argv) == 2 and sys.argv[1] == 'rollback':
            rollback(root)
            print('Original resources restored.')
        elif len(sys.argv) == 2 and sys.argv[1] == 'apply':
            print('Patch installed; files updated:', apply(root, package))
            print('Restart the assistant. Enable the new Extreme Peak option to test it.')
        else:
            raise ValueError('Usage: patch.py apply|rollback')
    except Exception as exc:
        print('PATCH FAILED:', exc)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
