"""Build the v2.7.2 overlay; use installed interface settings rather than replacing them."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OPTION = '极限峰值：槽位未满仍开始作战'
BASE = 'v2.7.2'
SOURCE_BASE = '23cbf0d78c6f04490c2ff8bc3f8417a7b344f141'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def build(destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    package = destination / 'dialog-patch'
    if package.exists():
        shutil.rmtree(package)
    package.mkdir()
    changed = git('diff', '--name-only', '-z', SOURCE_BASE, 'HEAD', '--', 'assets').decode().split('\0')
    manifest = {'resource_version': BASE, 'software_version': 'v2.16.1', 'framework_version': 'v5.12.3',
                'source_commit': git('rev-parse', 'HEAD').decode().strip(), 'files': []}
    for path in filter(None, changed):
        if path.startswith('assets/interface'):
            continue
        rel = path.removeprefix('assets/')
        content = (ROOT / path).read_bytes()
        exists = subprocess.run(['git', 'cat-file', '-e', BASE + ':' + path], cwd=ROOT, capture_output=True).returncode == 0
        before = git('show', BASE + ':' + path) if exists else None
        # Do not silently include changes from upstream after the user's release.
        if exists and before != git('show', SOURCE_BASE + ':' + path):
            raise ValueError('Patch baseline differs from installed release: ' + path)
        target = package / 'payload' / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        manifest['files'].append({'path': rel, 'before_sha256': hashlib.sha256(before).hexdigest() if before is not None else None,
                                  'before_text_sha256': hashlib.sha256(before.decode('utf-8-sig').replace('\r\n', '\n').replace('\r', '\n').encode('utf-8')).hexdigest() if before is not None and path.endswith(('.json', '.jsonc')) else None,
                                  'after_sha256': hashlib.sha256(content).hexdigest()})
    interface = json.loads((ROOT / 'assets/interface.json').read_text())
    additions = {'option': interface['option'][OPTION], 'labels': {}}
    for lang, filename in interface['languages'].items():
        labels = json.loads((ROOT / 'assets' / filename).read_text())
        additions['labels'][lang] = {k: labels[k] for k in [OPTION, '极限峰值缺员作战说明']}
    for name, data in [('manifest.json', manifest), ('interface-additions.json', additions)]:
        (package / name).write_text(json.dumps(data, ensure_ascii=False, indent=4) + '\n', encoding='utf-8')
    shutil.copy2(ROOT / 'scripts/dialog_patch/patch.py', package)
    shutil.copy2(ROOT / 'docs/测试补丁安装.md', package / 'README.md')
    for name, mode in [('install.bat', 'apply'), ('rollback.bat', 'rollback')]:
        (package / name).write_bytes(('@echo off\r\ncd /d "%~dp0"\r\nif not exist "..\\python\\python.exe" (\r\n  echo Place dialog-patch inside the assistant installation folder.\r\n  pause\r\n  exit /b 1\r\n)\r\n"..\\python\\python.exe" patch.py ' + mode + '\r\nset "patch_result=%ERRORLEVEL%"\r\npause\r\nexit /b %patch_result%\r\n').encode('ascii'))
    archive = destination / 'MaaGF2Exilium-dialog-patch-v2.7.2.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for path in sorted(package.rglob('*')):
            if path.is_file():
                z.write(path, path.relative_to(destination))
    copy_archive = destination / 'MaaGF2Exilium-copy-and-shortcut-v2.7.2-r3.zip'
    with zipfile.ZipFile(copy_archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for path in sorted(package.rglob('*')):
            if path.is_file():
                z.write(path, path.relative_to(destination))
        z.write(ROOT / 'scripts/dialog_patch/deploy-copy.ps1', 'deploy-copy.ps1')
        z.writestr('install-copy.bat', '@echo off\r\npowershell.exe -NoProfile -STA -ExecutionPolicy Bypass -File "%~dp0deploy-copy.ps1"\r\nif errorlevel 1 pause\r\n')
        z.writestr('README.txt', 'Extract the entire ZIP, then double-click install-copy.bat.\r\nSelect the original MaaGF2Exilium.exe (or MFAAvalonia.exe).\r\nOnly a new sibling copy is patched; a desktop shortcut points to that copy.\r\nClose the original assistant first. Do not select a failed test-copy folder.\r\nIf installation fails, the dialog shows the underlying error and log path.\r\n')
    return archive


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='/tmp/maagf2-dialog-package')
    print(build(parser.parse_args().output))
