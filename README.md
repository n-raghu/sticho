# OMS Backend Service

A sample Strawberry GraphQL microservice with Stytch OAuth authentication.

## Features

- FastAPI for the web framework
- Strawberry GraphQL for the API
- Stytch for OAuth authentication
- Authentication middleware for secure endpoints

## Setup

1. Install dependencies:

```bash
pip install -e .
```

2. Set up environment variables:

Create a `.env` file in the root directory with the following variables:

```
STYTCH_SECRET=your_stytch_secret
STYTCH_PROJECT_ID=your_stytch_project_id
STYTCH_PUBLIC_TOKEN=your_stytch_public_token
STYTCH_ENV=test  # or 'live' for production
REDIRECT_URL=http://localhost:36016/auth/callback
```

## Running the Service

```bash
cd service
uvicorn run:app --reload --port 36016
```

## Authentication Flow

1. Users are redirected to the Stytch OAuth page via `/auth/sso/google`
2. After successful authentication, they are redirected back to `/auth/callback`
3. A session cookie is set and they are redirected to the GraphQL endpoint
4. All GraphQL operations require authentication by default

## GraphQL Endpoints

- `/graphql` - The GraphQL API endpoint
- `/graphql/graphiql` - The GraphiQL interface for testing (in development)

### Sample Queries

```graphql
query {
  hello {
    ok
    msg
  }
}
```

### Sample Mutations

```graphql
mutation {
  ping {
    ok
    msg
  }
}
```

## Testing

Run tests with pytest:

```bash
pytest
```