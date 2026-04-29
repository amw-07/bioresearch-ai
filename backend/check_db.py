import asyncio
from sqlalchemy import text

from app.core.database import AsyncSessionLocal

async def check():
    async with AsyncSessionLocal() as db:
        result = await db.execute(text('SELECT count(*) FROM researchers'))
        print('Researchers in DB:', result.scalar())

if __name__ == '__main__':
    asyncio.run(check())
