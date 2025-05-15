import strawberry
import uvicorn
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter
from contextlib import asynccontextmanager
from service import qry
from service import init_supabase
from service.cfg import cfg
from service.middleware.auth import StytchAuthMiddleware, setup_auth_routes, require_auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # await init_supabase()
        yield
    finally:
        print("Shutting down...")


app = FastAPI(lifespan=lifespan)
gql_middlewares = []

# Add CORS middleware AFTER auth middleware
app.add_middleware(StytchAuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up authentication routes
setup_auth_routes(app)

# Create GraphQL schema
schema = strawberry.Schema(query=qry.Query)

# Define context getter function to pass request to resolvers
async def get_context(request: Request):
    print(f"GRAPHQL CONTEXT: Creating context for request to {request.url.path}")

    # Check if the request has been authenticated by the middleware
    if hasattr(request.state, "authenticated"):
        print(f"GRAPHQL CONTEXT: Request authenticated: {request.state.authenticated}")
        if hasattr(request.state, "user_id"):
            print(f"GRAPHQL CONTEXT: User ID: {request.state.user_id}")
    else:
        print("GRAPHQL CONTEXT: Request not authenticated by middleware!")

    return {"request": request}

# Add GraphQL router with context and authentication dependency
app.include_router(
    GraphQLRouter(
        schema,
        graphiql=True,
        context_getter=get_context
    ),
    prefix="/gql",
    tags=["graphql"],
    dependencies=[Depends(require_auth)]  # This ensures all GraphQL requests are authenticated
)


if __name__ == "__main__":
    uvicorn.run(
        "service.run:app",
        port=cfg.port,
        host="0.0.0.0",
        access_log=False,
    )
