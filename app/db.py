from pymongo import AsyncMongoClient
from pymongo.server_api import ServerApi
from .config import get_settings

settings = get_settings()
client = AsyncMongoClient(
    settings.mongodb_uri,
    server_api=ServerApi("1", strict=False, deprecation_errors=False)
)
db = client[settings.mongodb_db]

async def ping_db():
    await client.admin.command("ping")
    return True

async def close_db():
    await client.close()
