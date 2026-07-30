# GraphQL Mutations

This document describes the available GraphQL mutations.

## Overview

GraphQL mutations allow you to create, update, and delete data in the service.

## Basic Mutation Structure

```graphql
mutation {
  mutationName(input: { field: value }) {
    result {
      field
    }
  }
}
```

## Available Mutations

### Create Practitioner

```graphql
mutation {
  createPractitioner(input: {
    name: "Dr. John Doe"
    active: true
  }) {
    practitioner {
      id
      name
    }
  }
}
```

### Update Practitioner

```graphql
mutation {
  updatePractitioner(input: {
    id: "uuid"
    name: "Dr. Jane Doe"
  }) {
    practitioner {
      id
      name
    }
  }
}
```

### Delete Practitioner

```graphql
mutation {
  deletePractitioner(input: {
    id: "uuid"
  }) {
    success
  }
}
```

## Related Documentation

- [GraphQL Overview](overview.md)
- [GraphQL Examples](examples.md)

