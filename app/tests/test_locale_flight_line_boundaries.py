import importlib.util
from pathlib import Path
import sys, unittest, json
APP = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('subject', APP / 'scripts/extract-auth-copy.py')
subject = importlib.util.module_from_spec(spec)
sys.modules['subject'] = subject
spec.loader.exec_module(subject)
spec2 = importlib.util.spec_from_file_location('competition', APP / 'scripts/extract-competition-rules-copy.py')
competition = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(competition)

def auth_locale():
    result = {'locale': 'en', 'resources': {}}
    for key in subject.KEYS:
        target = result['resources']
        parts = key.split('.')
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        target[parts[-1]] = 'Label'
    return result

def auth_html(value, kind=1):
    return '<script>self.__next_f.push(' + json.dumps([kind, 'c6:' + json.dumps(value, ensure_ascii=False) + '\n'], ensure_ascii=False) + ')</script>'

def competition_html(kind=1, label='Label'):
    cup = {key: label for key in competition.CUP_KEYS}
    cup['rules'] = {key: label for key in competition.RULE_KEYS}
    rows = {'c1': {'locale': 'en', 'resources': {'common': {'close': label}}}, '103': {'locale': 'en', 'resources': {'web': {'leaderboard': {'cup': cup}}}}}
    payload = ''.join((key + ':' + json.dumps(value, ensure_ascii=False) + '\n' for key, value in rows.items()))
    return '<script>self.__next_f.push(' + json.dumps([kind, payload], ensure_ascii=False) + ')</script>'

class Tests(unittest.TestCase):

    def test_unicode_line_separators_inside_json_strings(self):
        value = auth_locale()
        value['resources']['common']['sign_in'] = 'Before\u2028After\u2029End'
        result = subject.extract(auth_html(value))
        self.assertEqual(result['common.sign_in'], 'Before\u2028After\u2029End')

    def test_competition_separator(self):
        self.assertEqual(competition.extract(competition_html(label='A\u2028B'))['title'], 'A\u2028B')
