# Counts describe the saved snapshot, with expiration evaluated at query time.
# Algorithm counts refer to federation keys, not application metadata keys.
def counts:
  group_by(.) | map({key: .[0], value: length}) | from_entries;

now as $now
| [to_entries[] | .value.configuration] as $configurations
| {
    entities: length,
    missing_configurations: ([$configurations[] | select(. == null)] | length),
    expired_configurations: (
      [$configurations[] | .exp | numbers | select(. <= $now)] | length
    ),
    configurations_expiring_within_24h: (
      [$configurations[] | .exp | numbers
       | select(. > $now and . <= ($now + 86400))] | length
    ),
    configurations_without_numeric_exp: (
      [$configurations[] | select(. != null)
       | select(.exp | type != "number")] | length
    ),
    metadata_roles: (
      [$configurations[] | (.metadata // {}) | keys[]] | counts
    ),
    federation_key_types: (
      [$configurations[] | .jwks.keys[]? | .kty // "unspecified"] | counts
    ),
    federation_key_algorithms: (
      [$configurations[] | .jwks.keys[]? | .alg // "unspecified"] | counts
    )
  }
