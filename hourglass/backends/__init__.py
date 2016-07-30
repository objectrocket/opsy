#pylint: disable=invalid-name,no-member
import asyncio

if hasattr(asyncio, 'ensure_future'):
    async_task = asyncio.ensure_future
else:
    async_task = asyncio.async # Deprecated since 3.4.4
