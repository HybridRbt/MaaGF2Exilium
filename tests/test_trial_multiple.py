"""Exercise the real MaaFramework JumpBack and max_hit behavior with simulated screens."""
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
from maa.controller import CustomController
from maa.custom_action import CustomAction
from maa.custom_recognition import CustomRecognition
from maa.resource import Resource
from maa.tasker import Tasker, LoggingLevelEnum

ROOT = Path(__file__).resolve().parents[1]


class OfflineController(CustomController):
    def connect(self):
        return True

    def request_uuid(self):
        return 'offline-trial-test'

    def screencap(self):
        return np.zeros((720, 1280, 3), dtype=np.uint8)

    def unexpected_input(self, *args):
        raise AssertionError('Offline routing tests must never send input')

    start_app = stop_app = click = swipe = unexpected_input
    touch_down = touch_move = touch_up = unexpected_input
    click_key = input_text = key_down = key_up = unexpected_input


class TrialScreens(CustomRecognition):
    def __init__(self, state):
        super().__init__()
        self.state = state

    def analyze(self, context, argv):
        name, s = argv.node_name, self.state
        visible = {
            'clickTrialTab': s['screen'] in ['list', 'detail'],
            'trialTabClicked': s['screen'] == 'detail',
            'trialRewardClaimed': s['screen'] == 'detail' and s['selected'] in s['done'],
            'autoBattleForTrial': s['screen'] == 'detail' and s['selected'] not in s['done'],
            '发现人形介绍界面-通用战斗': s['screen'] == 'intro',
            '通用战斗任务开始': s['screen'] == 'battle',
            '打开活动页-预演': False,
            '滑动活动列表-预演': False,
            'returnToHomePage': True,
        }.get(name, True)
        return (10, 10, 30, 30) if visible else None


class TrialActions(CustomAction):
    def __init__(self, state):
        super().__init__()
        self.state = state

    def run(self, context, argv):
        name, s = argv.node_name, self.state
        s['visited'].append(name)
        if name == 'clickTrialTab':
            s['selected'] = s['queue'][0]
            s['screen'] = 'detail'
        elif name == 'autoBattleForTrial':
            s['attempts'] += 1
            s['battled'].append(s['selected'])
            s['screen'] = 'intro' if s['intro'] else 'battle'
        elif name == '发现人形介绍界面-通用战斗':
            s['screen'] = 'battle'
        elif name == '通用战斗任务开始':
            if not s['fail']:
                s['done'].add(s['selected'])
                s['completed'] = len(s['done'])
                # The observed game behavior moves a completed trial to the tail.
                s['queue'].remove(s['selected'])
                s['queue'].append(s['selected'])
            s['screen'] = 'list'
        elif name == 'returnToHomePage':
            s['screen'] = 'home'
        return True


class TrialMultipleTest(unittest.TestCase):
    def run_scenario(self, total, completed=0, fail=False, intro=False):
        state = dict(total=total, completed=completed, fail=fail, intro=intro,
                     screen='list', attempts=0, visited=[], selected=None,
                     queue=list(range(completed, total)) + list(range(completed)),
                     done=set(range(completed)), battled=[])
        nodes = json.loads((ROOT / 'assets/resource/base/pipeline/public/活动/预演.json').read_text())
        # Keep actual trial transitions and hit limits; substitute only perception,
        # clicks, and external shared nodes. No game/OCR success is implied.
        for external in ['returnToHomePage', '发现人形介绍界面-通用战斗', '通用战斗任务开始',
                         '打开活动页-活动通用', '滑动活动列表-活动通用']:
            nodes[external] = {}
        for name, node in nodes.items():
            node.update(recognition='Custom', custom_recognition='TrialScreens',
                        action='Custom', custom_action='TrialActions',
                        pre_delay=0, post_delay=0, post_wait_freezes=0, timeout=1000)
        Tasker.set_stdout_level(LoggingLevelEnum.Error)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'pipeline').mkdir()
            (root / 'pipeline/trials.json').write_text(json.dumps(nodes, ensure_ascii=False))
            resource = Resource()
            resource.register_custom_recognition('TrialScreens', TrialScreens(state))
            resource.register_custom_action('TrialActions', TrialActions(state))
            self.assertTrue(resource.post_bundle(root).wait().status.succeeded)
            controller = OfflineController()
            self.assertTrue(controller.post_connection().wait().status.succeeded)
            tasker = Tasker()
            self.assertTrue(tasker.bind(resource, controller))
            self.assertTrue(tasker.post_task('开始预演任务').wait().status.succeeded)
        return state

    def test_three_new_trials_are_completed_in_one_task_with_intro_interrupts(self):
        state = self.run_scenario(total=3, intro=True)
        self.assertEqual(state['completed'], 3)
        self.assertEqual(state['attempts'], 3)
        self.assertEqual(state['battled'], [0, 1, 2])
        self.assertEqual(state['visited'].count('发现人形介绍界面-通用战斗'), 3)
        self.assertIn('trialRewardClaimed', state['visited'])
        self.assertNotIn('预演战斗尝试次数达到上限', state['visited'])
        self.assertEqual(state['screen'], 'home')

    def test_all_claimed_does_not_start_a_battle(self):
        state = self.run_scenario(total=3, completed=3)
        self.assertEqual(state['attempts'], 0)
        self.assertEqual(state['screen'], 'home')

    def test_failed_trial_exits_with_limit_notice_instead_of_looping_forever(self):
        state = self.run_scenario(total=3, fail=True)
        self.assertEqual(state['completed'], 0)
        self.assertEqual(state['attempts'], 8)
        self.assertIn('预演战斗尝试次数达到上限', state['visited'])
        self.assertNotIn('trialRewardClaimed', state['visited'])
        self.assertEqual(state['screen'], 'home')


if __name__ == '__main__':
    unittest.main()
