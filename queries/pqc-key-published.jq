with_entries(
  .value = any(.value.configuration.jwks.keys[]?;
    .kty == "AKP"
    and (.alg == "ML-DSA-44"
         or .alg == "ML-DSA-65"
         or .alg == "ML-DSA-87")
  )
)