import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
ENTRY = '战斗任务开始-极限峰值缺员作战'

class PeakIncompleteSlotsTest(unittest.TestCase):
    def setUp(self):
        self.interface = json.loads((ASSETS / 'interface.json').read_text())
        self.nodes = json.loads((ASSETS / 'resource/base/pipeline/public/SimulatedCombat/极限峰值缺员作战.json').read_text())

    def test_option_is_off_by_default_and_only_rewires_three_peak_groups(self):
        option = self.interface['option']['极限峰值：槽位未满仍开始作战']
        self.assertEqual(option['default_case'], 'NO')
        for case in option['cases']:
            override = case['pipeline_override']
            self.assertEqual(set(override), {f'开始作战-子群{i}-极限峰值' for i in range(1, 4)})
            entry = ENTRY if case['name'] == 'YES' else '通用战斗任务开始'
            for i in range(1, 4):
                self.assertEqual(override[f'开始作战-子群{i}-极限峰值']['next'],
                    ['[JumpBack]' + entry, f'子群{i}后返回极限峰值标签页-极限峰值'])

    def test_empty_party_is_still_deployed_and_popup_never_cancels(self):
        click = self.nodes['点击作战开始按钮-极限峰值缺员作战']
        self.assertEqual(click['next'][0], '发现可部署人形提示-极限峰值缺员作战')
        popup = self.nodes[click['next'][0]]
        self.assertNotIn('action', popup)
        self.assertEqual(popup['next'], ['确认缺员作战-极限峰值'])
        self.assertEqual(self.nodes['未部署任何人形-极限峰值缺员作战']['next'], ['选中部署位-极限峰值缺员作战'])
        self.assertEqual(self.nodes['部署人形-极限峰值缺员作战']['next'], ['点击作战开始按钮-极限峰值缺员作战'])
        self.assertNotIn('取消可部署人形提示-通用战斗', json.dumps(self.nodes, ensure_ascii=False))

    def test_option_labels_and_english_popup_overlay(self):
        for lang in ['zh', 'en']:
            labels = json.loads((ASSETS / f'interface_{lang}.json').read_text())
            for key in ['极限峰值：槽位未满仍开始作战', '极限峰值缺员作战说明']:
                self.assertIn(key, labels)
        en = json.loads((ASSETS / 'resource/resource_en/pipeline/极限峰值缺员作战.json').read_text())
        self.assertEqual(en['确认缺员作战-极限峰值']['expected'], '^Confirm$')
        self.assertIn('发现可部署人形提示-极限峰值缺员作战', en)

if __name__ == '__main__':
    unittest.main()
