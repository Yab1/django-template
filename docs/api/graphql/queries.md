# GraphQL Queries

This document describes the available GraphQL queries.

## Overview

GraphQL queries allow you to retrieve data from the service.

## Basic Query Structure

```graphql
query {
  fieldName {
    subField
  }
}
```

## Available Queries

### Practitioner Queries

Query practitioners with filtering and pagination.

```graphql
query {
  practitioners {
    id
    name
    active
  }
}
```

## Filtering

Queries support filtering:

```graphql
query {
  practitioners(filters: { active: true }) {
    id
    name
  }
}
```

## Pagination

Queries support pagination:

```graphql
query {
  practitioners(first: 10, after: "cursor") {
    edges {
      node {
        id
        name
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

## Related Documentation

- [GraphQL Overview](overview.md)
- [GraphQL Examples](examples.md)

