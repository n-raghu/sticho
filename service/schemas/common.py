import strawberry
from pydantic import BaseModel


class PyAbout(BaseModel):
    env: str
    version: str
    hosted_at: str
    node: str
    server_time: str


@strawberry.experimental.pydantic.type(model=PyAbout, all_fields=True)
class About:
    pass
