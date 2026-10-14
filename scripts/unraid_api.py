#!/usr/bin/env python3
"""Bounded GraphQL operations for Unraid; credentials stay in process memory."""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


READS = {
    'system': 'query { info { os { platform distro release uptime } cpu { manufacturer brand cores threads } } }',
    'array': 'query { array { state disks { id name size status temp } } }',
    'containers': 'query { docker { containers { id names state status autoStart } } }',
    'vms': 'query { vms { domains { id name state } } }',
    'shares': 'query { shares { name free used size } }',
}
WRITES = {
    'array-start': ('mutation { array { setState(input: { desiredState: START }) { state } } }', False),
    'array-stop': ('mutation { array { setState(input: { desiredState: STOP }) { state } } }', False),
}
for action in ('start', 'stop', 'restart'):
    WRITES['container-' + action] = (
        'mutation($id: PrefixedID!) { docker { ' + action + '(id: $id) { id names state status } } }', True,
    )
for action in ('start', 'stop', 'reboot'):
    WRITES['vm-' + action] = (
        'mutation($id: PrefixedID!) { vm { ' + action + '(id: $id) } }', True,
    )
MAX_RESPONSE_BYTES = 4 * 1024 * 1024


class APIError(Exception):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise APIError('Redirect refused; use the trusted canonical HTTPS hostname.')


def endpoint(origin):
    try:
        url = urllib.parse.urlsplit(origin)
        port = url.port
    except ValueError:
        raise APIError('Invalid server URL.') from None
    if (url.scheme != 'https' or not url.hostname or url.username is not None
            or url.password is not None or url.query or url.fragment
            or url.path not in ('', '/') or port not in (None, 443)
            or any(c.isspace() for c in origin)):
        raise APIError('Use a trusted HTTPS origin on port 443 without credentials or a path.')
    return origin.rstrip('/') + '/graphql'


def payload_for(operation, resource_id=None, write=False):
    if operation in READS:
        if resource_id is not None:
            raise APIError('--id is only valid for container/VM lifecycle operations.')
        return {'query': READS[operation]}
    if operation not in WRITES:
        raise APIError('Unknown operation.')
    if not write:
        raise APIError('Mutations require --write and task-specific authorization.')
    query, needs_id = WRITES[operation]
    if needs_id and (not resource_id or not resource_id.strip()):
        raise APIError('Use --id with the exact API ID returned by an inventory read.')
    if not needs_id and resource_id is not None:
        raise APIError('--id is not valid for array operations.')
    payload = {'query': query}
    if needs_id:
        payload['variables'] = {'id': resource_id}
    return payload


def redact(value, key):
    if isinstance(value, str):
        return value.replace(key, '[REDACTED]')
    if isinstance(value, list):
        return [redact(v, key) for v in value]
    if isinstance(value, dict):
        return {redact(k, key): redact(v, key) for k, v in value.items()}
    return value


def request(origin, payload, key, timeout=20, opener=None):
    url = endpoint(origin)
    if not key or '\r' in key or '\n' in key:
        raise APIError('UNRAID_API_KEY is missing or contains invalid header characters.')
    if not 0 < timeout <= 60:
        raise APIError('Timeout must be greater than zero and at most 60 seconds.')
    opener = opener or urllib.request.build_opener(NoRedirect())
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(), method='POST',
        headers={'Content-Type': 'application/json', 'Accept': 'application/json', 'x-api-key': key},
    )
    try:
        with opener.open(req, timeout=timeout) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise APIError('Response exceeded the size limit.')
            result = json.loads(raw)
    except urllib.error.HTTPError as error:
        raise APIError(f'Unraid returned HTTP {error.code}; check API authentication, permissions and endpoint.') from None
    except (urllib.error.URLError, OSError):
        raise APIError('Transport failed. Check inherited proxy, VPN, canonical hostname and TLS trust. '
                       'For a mutation, read back state before any retry.') from None
    except (ValueError, UnicodeError):
        raise APIError('Unraid returned invalid JSON.') from None
    if not isinstance(result, dict):
        raise APIError('Unraid returned an unexpected GraphQL response.')
    # Only expose selected data and error messages, never extensions/stack traces.
    output = {'data': redact(result.get('data'), key)}
    errors = result.get('errors')
    if errors:
        if not isinstance(errors, list) or any(not isinstance(e, dict) for e in errors):
            raise APIError('Unraid returned malformed GraphQL errors.')
        output['errors'] = [redact(str(e.get('message', 'GraphQL error')), key) for e in errors]
    if not errors and output['data'] is None:
        raise APIError('Unraid returned no GraphQL data.')
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=sorted(set(READS) | set(WRITES)))
    parser.add_argument('--url', default=os.environ.get('UNRAID_URL'), help='Trusted HTTPS origin; defaults to UNRAID_URL')
    parser.add_argument('--id', help='Exact PrefixedID from container or VM inventory')
    parser.add_argument('--write', action='store_true', help='Permit a predefined mutation; does not supply user authorization')
    parser.add_argument('--timeout', type=float, default=20, help='Request timeout in seconds (maximum 60)')
    args = parser.parse_args(argv)
    try:
        payload = payload_for(args.operation, args.id, args.write)
        if not args.url:
            raise APIError('Set UNRAID_URL or supply --url with the trusted HTTPS origin.')
        output = request(args.url, payload, os.environ.get('UNRAID_API_KEY'), args.timeout)
        print(json.dumps(output, indent=2))
        return 1 if output.get('errors') else 0
    except APIError as error:
        print(json.dumps({'error': str(error)}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
