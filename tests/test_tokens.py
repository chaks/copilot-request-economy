import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

from tokens import find_latest_process_log, parse_tokens_from_log

class TestTokenParser(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def _write_log(self, content: str) -> str:
        path = os.path.join(self.tmpdir, 'process-1234567890-1234.log')
        with open(path, 'w') as f:
            f.write(content)
        return path

    def test_parse_tokens_from_valid_log(self):
        log_content = '''
        {"object": "chat.completion", "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}}
        {"object": "chat.completion", "usage": {"prompt_tokens": 200, "completion_tokens": 75, "total_tokens": 275}}
        '''
        path = self._write_log(log_content)
        result = parse_tokens_from_log(path)
        self.assertEqual(result['input_tokens'], 300)
        self.assertEqual(result['output_tokens'], 125)

    def test_parse_tokens_empty_log(self):
        path = self._write_log('')
        result = parse_tokens_from_log(path)
        self.assertEqual(result['input_tokens'], 0)
        self.assertEqual(result['output_tokens'], 0)

    def test_parse_tokens_no_completions(self):
        path = self._write_log('some random log content')
        result = parse_tokens_from_log(path)
        self.assertEqual(result['input_tokens'], 0)
        self.assertEqual(result['output_tokens'], 0)

    def test_parse_tokens_malformed_json(self):
        log_content = '''
        {"object": "chat.completion", "usage": {"prompt_tokens": 100, "completion_tokens": 50}}
        {malformed json here}
        {"object": "chat.completion", "usage": {"prompt_tokens": 200, "completion_tokens": 75}}
        '''
        path = self._write_log(log_content)
        result = parse_tokens_from_log(path)
        self.assertEqual(result['input_tokens'], 300)
        self.assertEqual(result['output_tokens'], 125)

    def test_parse_tokens_missing_fields(self):
        log_content = '''
        {"object": "chat.completion", "usage": {"prompt_tokens": 100}}
        '''
        path = self._write_log(log_content)
        result = parse_tokens_from_log(path)
        self.assertEqual(result['input_tokens'], 100)
        self.assertEqual(result['output_tokens'], 0)

    def test_find_latest_process_log_no_files(self):
        result = find_latest_process_log(self.tmpdir)
        self.assertIsNone(result)

    def test_find_latest_process_log_returns_newest(self):
        import time
        old_path = os.path.join(self.tmpdir, 'process-1111111111-1111.log')
        with open(old_path, 'w') as f:
            f.write('old')
        time.sleep(0.01)
        new_path = os.path.join(self.tmpdir, 'process-2222222222-2222.log')
        with open(new_path, 'w') as f:
            f.write('new')
        result = find_latest_process_log(self.tmpdir)
        self.assertEqual(result, new_path)
