import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


installer = module('dialog_installer', ROOT / 'scripts/dialog_patch/patch.py')
builder = module('dialog_builder', ROOT / 'scripts/build_dialog_patch.py')


class DialogPatchPackageTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'installed'
        self.root.mkdir()
        builder.build(Path(self.temp.name) / 'bundle')
        self.package = Path(self.temp.name) / 'bundle/dialog-patch'
        manifest = installer.read_json(self.package / 'manifest.json')
        for item in manifest['files']:
            if item['before_sha256'] is not None:
                target = self.root / item['path']
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(self.original('assets/' + item['path']))
        interface = json.loads(self.original('assets/interface.json'))
        interface.update(version='v2.7.2', url='https://github.com/DarkLingYun/MaaGF2Exilium', custom_user_field={'keep': True})
        interface['agent'] = {'child_exec': 'python/python.exe', 'child_args': ['-u', '{PROJECT_DIR}/agent/main.py']}
        (self.root / 'interface.json').write_bytes(installer.encode_json(interface))
        for filename in interface['languages'].values():
            (self.root / filename).write_bytes(self.original('assets/' + filename))
        (self.root / 'user-config.json').write_bytes(b'{"screencap":"FramePool","mouse":"Seize"}')
        self.before = self.snapshot()

    def original(self, path):
        return subprocess.check_output(['git', 'show', 'v2.7.2:' + path], cwd=ROOT)

    def snapshot(self):
        return {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}

    def test_install_preserves_settings_and_rollback_restores_bytes(self):
        installer.apply(self.root, self.package)
        current = installer.read_json(self.root / 'interface.json')
        original = json.loads(self.before['interface.json'])
        for key in ['version', 'url', 'agent', 'controller', 'resource', 'custom_user_field']:
            self.assertEqual(current[key], original[key])
        self.assertEqual(current['option'][installer.OPTION]['default_case'], 'NO')
        self.assertEqual((self.root / 'user-config.json').read_bytes(), self.before['user-config.json'])
        with self.assertRaisesRegex(ValueError, 'Backup already exists'):
            installer.apply(self.root, self.package)
        installer.rollback(self.root)
        self.assertEqual(self.snapshot(), self.before)

    def test_windows_newlines_and_bom_install_and_restore_original_bytes(self):
        for target in self.root.rglob('*.json'):
            if 'pipeline' in target.parts:
                target.write_bytes(b'\xef\xbb\xbf' + target.read_bytes().replace(b'\n', b'\r\n'))
        before = self.snapshot()
        installer.apply(self.root, self.package)
        installer.rollback(self.root)
        self.assertEqual(self.snapshot(), before)

    def test_newline_tolerance_does_not_accept_changed_pipeline_content(self):
        target = next(p for p in self.root.rglob('*.json') if 'pipeline' in p.parts)
        target.write_bytes(b'\xef\xbb\xbf' + target.read_bytes().replace(b'\n', b'\r\n') + b'// changed content\r\n')
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'differs from v2.7.2'):
            installer.apply(self.root, self.package)
        self.assertEqual(self.snapshot(), before)

    def test_wrong_version_and_modified_resources_leave_installation_untouched(self):
        interface = installer.read_json(self.root / 'interface.json')
        interface['version'] = 'v2.7.3'
        (self.root / 'interface.json').write_bytes(installer.encode_json(interface))
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'Expected resource'):
            installer.apply(self.root, self.package)
        self.assertEqual(self.snapshot(), before)
        (self.root / 'interface.json').write_bytes(self.before['interface.json'])
        existing = next(p for p in self.root.rglob('*.json') if 'pipeline' in p.parts)
        existing.write_bytes(b'{}')
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'differs from v2.7.2'):
            installer.apply(self.root, self.package)
        self.assertEqual(self.snapshot(), before)

    def test_partial_write_failure_restores_installation(self):
        original_write = installer.write_atomic
        calls = 0
        def fail_once(path, data):
            nonlocal calls
            calls += 1
            if calls == 3:
                raise OSError('simulated write failure')
            original_write(path, data)
        with patch.object(installer, 'write_atomic', side_effect=fail_once):
            with self.assertRaisesRegex(OSError, 'simulated write failure'):
                installer.apply(self.root, self.package)
        self.assertEqual(self.snapshot(), self.before)

    def test_rollback_refuses_to_overwrite_later_resource_update(self):
        installer.apply(self.root, self.package)
        (self.root / 'interface.json').write_bytes(b'{"version":"v2.7.3"}')
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'changed after patch installation'):
            installer.rollback(self.root)
        self.assertEqual(self.snapshot(), before)


if __name__ == '__main__':
    unittest.main()
