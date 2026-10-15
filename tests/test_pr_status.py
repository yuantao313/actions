import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from _lib import operations as op


class API:
    def __init__(self, reads=()):
        self.reads = list(reads)
        self.calls = []
        self.comment = {'id': 42, 'body': 'old body'}

    def request(self, method, path, body=None, encoding='form'):
        self.calls.append((method, path, body))
        if method == 'GET' and path.endswith('/labels'): return [{'name': 'success'}]
        if method == 'POST' and path.endswith('/comments') or method == 'PATCH':
            self.comment['body'] = body['body']
            return dict(self.comment)
        if method == 'GET' and '/pulls/comments/' in path:
            value = self.reads.pop(0) if self.reads else dict(self.comment)
            if isinstance(value, Exception): raise value
            return value
        return {}


def status(api, body=None, comment_id=''):
    return op.pr_status(api, 'example/project', '2', 'start', '',
                        'https://github.com/example/project/actions/runs/1', comment_id,
                        ['running', 'success', 'failure'], body)


class PRStatusTests(unittest.TestCase):
    @patch.object(op.time, 'sleep')
    def test_recently_created_comment_can_be_temporarily_unavailable(self, sleep):
        api = API([RuntimeError('AtomGit GET request failed (HTTP 400)'),
                   RuntimeError('AtomGit GET request failed (HTTP 404)'),
                   {'id': 42, 'body': 'stale body'}])
        self.assertEqual(status(api, 'Build running: https://github.com/run/1'), {'comment-id': '42'})
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [1, 2, 4])
        self.assertEqual(len([c for c in api.calls if c[0] == 'POST' and c[1].endswith('/comments')]), 1)
        self.assertFalse(any(c[0] == 'PATCH' for c in api.calls))

    @patch.object(op.time, 'sleep')
    def test_permanent_readback_failure_fails_without_reposting(self, sleep):
        for reads in [[RuntimeError('AtomGit GET request failed (HTTP 400)')]*5,
                      [{'id': 999, 'body': 'body'}]*5,
                      [{'id': 42, 'body': 'wrong body'}]*5]:
            api = API(reads)
            with self.assertRaisesRegex(RuntimeError, 'after 5 reads'):
                status(api, 'body')
            self.assertEqual(len([c for c in api.calls if c[0] == 'POST' and c[1].endswith('/comments')]), 1)
            self.assertEqual(len([c for c in api.calls if c[0] == 'GET' and '/pulls/comments/' in c[1]]), 5)

    @patch.object(op.time, 'sleep')
    def test_auth_and_server_errors_are_not_retried_or_hidden(self, sleep):
        for code in (401, 403, 500):
            api = API([RuntimeError(f'AtomGit GET request failed (HTTP {code})')])
            with self.assertRaisesRegex(RuntimeError, f'HTTP {code}'):
                status(api)
        sleep.assert_not_called()

    def test_default_body_and_updating_an_existing_comment(self):
        api = API()
        status(api)
        self.assertEqual(api.comment['body'], 'CI started: https://github.com/example/project/actions/runs/1')
        status(api, 'Finished result', '42')
        self.assertEqual(api.comment['body'], 'Finished result')
        self.assertEqual(len([c for c in api.calls if c[0] == 'PATCH']), 1)

    def test_empty_custom_body_does_not_write_labels_or_comments(self):
        api = API()
        with self.assertRaisesRegex(ValueError, 'nonempty'):
            status(api, '  ')
        self.assertEqual(api.calls, [])

    def test_action_entrypoint_reads_the_exact_body_file_and_emits_verified_id(self):
        api = API()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'body.md').write_text('Task running: literal `$(command)`', encoding='utf-8')
            env = {'ACTION_OPERATION':'pr-status', 'ATOMGIT_TOKEN':'fixture-only', 'REPOSITORY':'example/project',
                   'PR_NUMBER':'2', 'PHASE':'start', 'RUN_URL':'https://github.com/run/1',
                   'BODY_FILE':str(root/'body.md'), 'GITHUB_OUTPUT':str(root/'outputs')}
            with patch.dict(os.environ, env, clear=True), patch.object(op, 'AtomGitAPI', return_value=api):
                op.main()
            self.assertEqual(api.comment['body'], 'Task running: literal `$(command)`')
            self.assertEqual((root/'outputs').read_text().strip(), 'comment-id=42')
