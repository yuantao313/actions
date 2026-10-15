import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from _lib import operations as op


class API:
    def __init__(self, post_identifier=42):
        self.post_identifier = post_identifier
        self.calls = []
        self.comment = {'id': 42, 'body': 'old body'}

    def request(self, method, path, body=None, encoding='form'):
        self.calls.append((method, path, body, encoding))
        if method == 'GET' and path.endswith('/labels'): return [{'name': 'success'}]
        if method == 'POST' and path.endswith('/comments') or method == 'PATCH':
            self.comment['body'] = body['body']
            return dict(self.comment, id=self.post_identifier)
        return {}


def status(api, body=None, comment_id=''):
    return op.pr_status(api, 'example/project', '2', 'start', '',
                        'https://github.com/example/project/actions/runs/1', comment_id,
                        ['running', 'success', 'failure'], body)


class PRStatusTests(unittest.TestCase):
    def test_creation_preserves_returned_id_and_does_not_read_comment(self):
        for identifier in (42, '97219c08d421e55cfa841deca16a30f5d7269e10'):
            with self.subTest(identifier=identifier):
                api = API(post_identifier=identifier)
                result = status(api, 'Exact final body')
                self.assertEqual(result, {'comment-id': str(identifier)})
                self.assertEqual([c for c in api.calls if '/comments' in c[1]], [
                    ('POST', '/repos/example/project/pulls/2/comments', {'body': 'Exact final body'}, 'json')])

    def test_comment_write_failure_still_fails(self):
        api = API()
        original = api.request
        def request(method, path, body=None, encoding='form'):
            if method == 'POST' and path.endswith('/comments'):
                raise RuntimeError('AtomGit POST request failed (HTTP 403)')
            return original(method, path, body, encoding)
        api.request = request
        with self.assertRaisesRegex(RuntimeError, 'HTTP 403'):
            status(api)

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

    def test_action_entrypoint_reads_the_exact_body_file_and_emits_returned_id(self):
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
