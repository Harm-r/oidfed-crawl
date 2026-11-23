# Expiring within the next 24 hours, excluding already expired configurations.
# Missing or non-numeric exp yields null.
now as $now
| (24 * 60 * 60) as $window
| with_entries(
    .value = (
      .value.configuration.exp
      | if type == "number" then . > $now and . <= ($now + $window)
        else null
        end
    )
  )
