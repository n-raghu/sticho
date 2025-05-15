import asyncio as aio
from datetime import datetime as dtm

import strawberry
from service.schemas.common import About, PyAbout


async def q_about() -> About:
    res = await get_about()
    return About.from_pydantic(res)


async def get_about():
    await aio.sleep(0.01)
    return PyAbout(
        env="dev",
        version="1.0.1",
        hosted_at="localhost",
        node="localhost",
        server_time=dtm.now().isoformat(),
    )


@strawberry.type
class Q:
    qry_about = strawberry.field(q_about)


@strawberry.type
class ModuleAbout:
    qry = strawberry.field(Q)
