A sample Strawberry GraphQL microservice with Stytch OAuth authentication.

## Features

- FastAPI for the web framework
- Strawberry GraphQL for the API
- Stytch for OAuth authentication
- Authentication middleware for secure endpoints

## Setup

1. Install dependencies:

```bash
poetry install
```

## Running the Service
```python
python service/run.py
```

```bash
cd service
uvicorn run:app --reload --port 36016
```

## Authentication Flow

1. Users are redirected to the Stytch OAuth page via `/auth/sso/google`
2. After successful authentication, they are redirected back to `/auth/callback`
3. A session cookie is set and they are redirected to the GraphQL endpoint
4. All GraphQL operations require authentication by session or Authorization header

## GraphQL Endpoints
- `/gql` - The GraphQL API endpoint

### Sample Queries

```graphql
query about {
  qryAbout {
		env
		version
		node
	}
}
```
