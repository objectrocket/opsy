import asyncio

if hasattr(asyncio, 'ensure_future'):
    async_task = asyncio.ensure_future  # pylint: disable=invalid-name,no-member
else:
    async_task = asyncio.async  # Deprecated since 3.4.4 pylint: disable=invalid-name,no-member
