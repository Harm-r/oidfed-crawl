# Compare against query execution time. Missing or non-numeric exp yields null.
now as $now
| with_entries(
    .value = (
      .value.configuration.exp
      | if type == "number" then . <= $now else null end
    )
  )
