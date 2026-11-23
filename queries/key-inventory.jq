# Inventory inline keys only; external jwks_uri endpoints are not fetched.
# Include locations and public descriptors, without exposing key material.
[
  to_entries[]
  | {
      entity: .key,
      keys: [
        .value.configuration
        | paths(objects) as $path
        | select($path[-3] == "jwks" and $path[-2] == "keys")
        | getpath($path)
        | {
            location: (["configuration"] + $path),
            kid: .kid,
            kty: .kty,
            alg: .alg,
            use: .use,
            key_ops: .key_ops,
            crv: .crv
          }
      ]
    }
]
