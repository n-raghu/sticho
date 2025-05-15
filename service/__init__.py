from cfg import cfg
from supabase import AsyncClient, acreate_client

_URL = cfg.sbs_url
_KEY = cfg.sbs_key

_SBS_CNX: AsyncClient = None


async def init_supabase():
    global _SBS_CNX

    if _SBS_CNX is None:
        _SBS_CNX = await acreate_client(_URL, _KEY)


async def cnx_sbs() -> AsyncClient:
    if not _SBS_CNX:
        raise Exception("Supabase not initialised")
    return _SBS_CNX
