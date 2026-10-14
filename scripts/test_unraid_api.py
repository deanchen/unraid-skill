"""Offline transport/authorization tests; never load real credentials."""

import io
import json
import unittest
import urllib.error
from unittest.mock import Mock, patch

import unraid_api as api


def opener_for(result):
    response = io.BytesIO(json.dumps(result).encode())
    opener = Mock()
    opener.open.return_value = response
    return opener


class GraphQLTests(unittest.TestCase):
    def test_mutations_require_write_and_exact_target(self):
        for name, (_, needs_id) in api.WRITES.items():
            with self.subTest(name=name):
                with self.assertRaises(api.APIError):
                    api.payload_for(name, 'synthetic-id')
                if needs_id:
                    with self.assertRaises(api.APIError):
                        api.payload_for(name, write=True)
                    payload = api.payload_for(name, 'synthetic-id', write=True)
                    self.assertEqual(payload['variables'], {'id': 'synthetic-id'})
                    self.assertNotIn('synthetic-id', payload['query'])
                else:
                    with self.assertRaises(api.APIError):
                        api.payload_for(name, 'synthetic-id', write=True)

    def test_graphql_id_is_not_interpolated(self):
        value = 'id"); malicious { field }'
        payload = api.payload_for('container-stop', value, write=True)
        self.assertEqual(payload['variables']['id'], value)
        self.assertNotIn(value, payload['query'])

    def test_reads_reject_irrelevant_ids(self):
        with self.assertRaises(api.APIError):
            api.payload_for('system', 'synthetic-id')

    def test_origin_validation(self):
        for url in ('http://host.invalid', 'https://user:password@host.invalid',
                    'https://host.invalid/graphql', 'https://host.invalid?x=1',
                    'https://host.invalid#x', 'https://host.invalid:8443',
                    'https://host.invalid:bad', 'https:// host.invalid'):
            with self.subTest(url=url), self.assertRaises(api.APIError):
                api.endpoint(url)
        self.assertEqual(api.endpoint('https://host.invalid/'), 'https://host.invalid/graphql')

    def test_header_transport_and_no_secret_in_output(self):
        opener = opener_for({'data': {'value': 'synthetic-key'}, 'extensions': {'debug': 'hidden'}})
        result = api.request('https://host.invalid', api.payload_for('system'), 'synthetic-key', opener=opener)
        request = opener.open.call_args.args[0]
        self.assertEqual(request.get_method(), 'POST')
        self.assertEqual(request.get_header('X-api-key'), 'synthetic-key')
        self.assertEqual(request.full_url, 'https://host.invalid/graphql')
        self.assertNotIn('synthetic-key', json.dumps(result))
        self.assertNotIn('extensions', result)

    def test_partial_graphql_errors_remain_visible(self):
        result = api.request('https://host.invalid', api.payload_for('system'), 'synthetic-key',
                             opener=opener_for({'data': {'info': None}, 'errors': [{'message': 'Denied', 'extensions': {'stack': 'hidden'}}]}))
        self.assertEqual(result, {'data': {'info': None}, 'errors': ['Denied']})

    def test_partial_response_has_failure_exit_status(self):
        with patch.dict('os.environ', {'UNRAID_API_KEY': 'synthetic-key'}, clear=True), \
                patch.object(api, 'request', return_value={'data': None, 'errors': ['Denied']}), \
                patch('sys.stdout', new=io.StringIO()):
            self.assertEqual(api.main(['system', '--url', 'https://host.invalid']), 1)

    def test_failed_mutation_is_not_retried(self):
        opener = Mock()
        opener.open.side_effect = urllib.error.URLError('synthetic-key')
        with self.assertRaises(api.APIError) as caught:
            api.request('https://host.invalid', api.payload_for('array-stop', write=True), 'synthetic-key', opener=opener)
        self.assertEqual(opener.open.call_count, 1)
        self.assertNotIn('synthetic-key', str(caught.exception))
        self.assertIn('read back state', str(caught.exception))

    def test_authentication_failure_is_explicit(self):
        opener = Mock()
        opener.open.side_effect = urllib.error.HTTPError('https://host.invalid/graphql', 401, 'synthetic-key', {}, None)
        with self.assertRaisesRegex(api.APIError, 'HTTP 401'):
            api.request('https://host.invalid', api.payload_for('system'), 'synthetic-key', opener=opener)

    def test_credentials_and_timeout_checked_before_transport(self):
        opener = Mock()
        for key, timeout in ((None, 20), ('synthetic\nkey', 20), ('synthetic-key', 61), ('synthetic-key', 0), ('synthetic-key', float('nan'))):
            with self.subTest(key=key, timeout=timeout), self.assertRaises(api.APIError):
                api.request('https://host.invalid', api.payload_for('system'), key, timeout, opener)
        opener.open.assert_not_called()

    def test_redirects_refused(self):
        with self.assertRaises(api.APIError):
            api.NoRedirect().redirect_request(None, None, 302, '', {}, 'https://other.invalid')

    def test_response_limits_and_json_shape(self):
        for raw in (b'x' * (api.MAX_RESPONSE_BYTES + 1), b'not json', b'[]', b'{}'):
            opener = Mock()
            opener.open.return_value = io.BytesIO(raw)
            with self.assertRaises(api.APIError):
                api.request('https://host.invalid', api.payload_for('system'), 'synthetic-key', opener=opener)


if __name__ == '__main__':
    unittest.main()
