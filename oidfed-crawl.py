import requests
import argparse
import jwt
import logging
import jq
import json
import tqdm

import socket
import urllib3.util.connection

urllib3.util.connection.allowed_gai_family = lambda: socket.AF_INET

CONFIGURATION_ENDPOINT = '/.well-known/openid-federation'

requests.urllib3.disable_warnings()

def parse_args():
    parser = argparse.ArgumentParser(
        prog='oidfed-crawl.py',
        description='Script that crawls an OpenID Federation to check properties like post-quantum readiness'
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    crawl_parser = subparsers.add_parser('crawl', help='Crawl an OpenID Federation')
    crawl_parser.add_argument(
        'url',
        help='URL of the root Trust Anchor, e.g. https://ta.example.com',
    )
    crawl_parser.add_argument(
        '-o', '--output', metavar='FILE',
        help='Save the full crawl as JSON, regardless of the query',
    )
    crawl_parser.add_argument(
        '-k', '--insecure', action='store_false',
        help='Do not validate TLS certificates',
    )

    query_parser = subparsers.add_parser('query', help='Query a saved crawl')
    query_parser.add_argument('input_file', help='Path to a saved crawl JSON file')

    for command_parser in (crawl_parser, query_parser):
        query_group = command_parser.add_mutually_exclusive_group(
            required=command_parser is query_parser,
        )
        query_group.add_argument(
            'query', nargs='?', metavar='EXPRESSION', help='jq expression to evaluate',
        )
        query_group.add_argument(
            '-f', '--query-file', metavar='FILE', help='Read the jq expression from a file',
        )

    return parser.parse_args()

def fetch_entity_configuration(entity_identifier, verifyTLS):
    try:
        r = requests.get(entity_identifier + CONFIGURATION_ENDPOINT, verify=verifyTLS)
        entity_configuration = jwt.decode(r.content, options={"verify_signature": False})
    except Exception as e:
        logging.error("Couldn't fetch or decode entity configuration:" + str(e))
        return None
    return entity_configuration

def list_subordinates(entity_configuration, verifyTLS):
    try:
        federation_list_endpoint = entity_configuration["metadata"]["federation_entity"]["federation_list_endpoint"]
    except (KeyError, TypeError):
        return []
    try:
        r = requests.get(federation_list_endpoint, verify=verifyTLS)
    except Exception as e:
        logging.error("Couldn't fetch listing endpoint '" + federation_list_endpoint + "':" + str(e))
        return []
    return r.json()

def supports_post_quantum(entity_configuration):
    for key in entity_configuration["jwks"]["keys"]:
        if key.get('kty') == 'AKP' and key.get('alg') in ['ML-DSA-44', 'ML-DSA-65', 'ML-DSA-87']:
            return True
    return False

def recursively_get_entity_configurations(entity_identifier, entity_configurations=None):
    if entity_configurations is None:
        entity_configurations = {}

    if entity_identifier in entity_configurations:
        return entity_configurations

    configuration = fetch_entity_configuration(
        entity_identifier, verifyTLS=args.insecure
    )

    # Register before recursing to avoid cycles.
    entity_configurations[entity_identifier] = {
        "configuration": configuration,
        "subordinates": [],
    }

    if configuration is None:
        return entity_configurations

    subordinates = list_subordinates(
        configuration, verifyTLS=args.insecure
    )

    entity_configurations[entity_identifier].update({
        "subordinates": subordinates,
    })

    for subordinate in tqdm.tqdm(subordinates, leave=False):
        recursively_get_entity_configurations(
            subordinate, entity_configurations
        )

    return entity_configurations
    

if __name__ == '__main__':
    args = parse_args()

    if args.command == "crawl":
        # We're crawling!
        entity_configurations = recursively_get_entity_configurations(args.url)

        if args.output:
            with open(args.output, 'w') as f:
                f.write(json.dumps(entity_configurations, indent=2))

    elif args.command == "query":
        with open(args.input_file) as f:
            entity_configurations = json.load(f)

    program = None
    if args.query_file:
        with open(args.query_file) as f:
            program = jq.compile(f.read())
    elif args.query:
        program = jq.compile(args.query)

    if program:
        for result in program.input_value(entity_configurations):
            print(result)
    elif args.command == "crawl" and not args.output:
        print(json.dumps(entity_configurations, indent=2))
