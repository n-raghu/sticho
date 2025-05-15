from pydantic import BaseModel


class Config(BaseModel):
    # Microservice
    port: int = 36016
    env: str = "test"
    enforce_iam: bool = True

    # Stytch
    secret: str = "secret-test-"
    project_id: str = "project-test-aaffe74a-8bd3-4bfd-bf42-a6efb8755d32"
    workspace_id: str = "organization-prod-7a9"
    public_token: str = "public-token-test-da0"
    redirect_url: str = "http://localhost:36016/auth/callback"

    # Supabase
    sbs_url: str = "https://supabase.co"
    sbs_key: str = "supabase_key"


cfg = Config()
