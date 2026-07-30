# GraphQL Examples

This document provides practical examples of using the GraphQL API.

## Basic Query Example

```graphql
query GetPractitioners {
  practitioners {
    id
    name {
      given
      family
    }
    active
  }
}
```

## Query with Filters

```graphql
query GetActivePractitioners {
  practitioners(filters: { active: true }) {
    id
    name {
      given
      family
    }
  }
}
```

## Mutation Example

```graphql
mutation CreatePractitioner {
  createPractitioner(input: {
    name: {
      given: ["John"]
      family: "Doe"
    }
    active: true
  }) {
    practitioner {
      id
      name {
        given
        family
      }
    }
    errors {
      field
      message
    }
  }
}
```

## Using Variables

```graphql
query GetPractitioner($id: UUID!) {
  practitioner(id: $id) {
    id
    name {
      given
      family
    }
    roles {
      code
      specialty
    }
  }
}
```

Variables:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000"
}
```

## Related Documentation

- [GraphQL Overview](overview.md)
- [GraphQL Queries](queries.md)
- [GraphQL Mutations](mutations.md)

