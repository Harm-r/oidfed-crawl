# Preserve entity and metadata role so each name has a clear source.
[
  to_entries[]
  | .key as $entity
  | (.value.configuration.metadata // {})
  | to_entries[]
  | select(.value | type == "object")
  | select(.value.organization_name | type == "string")
  | {
      entity: $entity,
      role: .key,
      organization_name: .value.organization_name
    }
]
| sort_by(.organization_name, .entity, .role)
