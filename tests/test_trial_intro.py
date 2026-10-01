import json
import unittest
from pathlib import Path
import json5

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
INTRO = '[JumpBack]发现人形介绍界面-通用战斗'

class TrialIntroTest(unittest.TestCase):
    def test_modal_is_reachable_without_combat_start_text(self):
        battle = json5.loads((ASSETS / 'resource/base/pipeline/public/通用战斗.json').read_text())
        trial = json5.loads((ASSETS / 'resource/base/pipeline/public/活动/预演.json').read_text())
        self.assertLess(trial['autoBattleForTrial']['next'].index(INTRO),
                        trial['autoBattleForTrial']['next'].index('[JumpBack]通用战斗任务开始'))
        entry = battle['通用战斗任务开始']
        self.assertIn('试用人形介绍', entry['expected'])
        self.assertEqual(entry['next'][0], INTRO)
        self.assertEqual(entry['next'].count(INTRO), 1)
        self.assertEqual(battle['发现人形介绍界面-通用战斗']['next'], ['点击关闭人形介绍-通用战斗'])
        self.assertNotIn('action', battle['发现人形介绍界面-通用战斗'])

    def test_pc_close_remains_guarded_and_preserves_old_templates(self):
        pc = json.loads((ASSETS / 'resource/resource_pc/pipeline/public/试用人形介绍.json').read_text())
        self.assertEqual(set(pc), {'点击关闭人形介绍-通用战斗'})
        close = pc['点击关闭人形介绍-通用战斗']
        self.assertEqual(close['order_by'], 'Score')
        self.assertNotIn('target', close)
        for template in close['template']:
            self.assertTrue((ASSETS / 'resource/resource_pc/image' / template).is_file())
        self.assertIn('公用按钮组件/关闭按钮_gray.png', close['template'])
        self.assertIn('公用按钮组件/关闭按钮_black.png', close['template'])

if __name__ == '__main__':
    unittest.main()
