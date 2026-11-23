# Inspect inline JWK Sets in configurations, including application metadata.
# Report parameter names only; never include private values in the result.
[
  to_entries[]
  | .key as $entity
  | .value.configuration
  | paths(objects) as $path
  | select($path[-3] == "jwks" and $path[-2] == "keys")
  | getpath($path)
  | select(.kty != null)
  | . as $key
  | ["d", "p", "q", "dp", "dq", "qi", "oth", "priv", "k"]
  | map(select(. as $parameter | $key | has($parameter)))
  | select(length > 0)
  | {
      entity: $entity,
      location: (["configuration"] + $path),
      kid: $key.kid,
      kty: $key.kty,
      private_parameters: .
    }
]
