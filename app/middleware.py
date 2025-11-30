# middleware.py
from aiogram import BaseMiddleware, types
from typing import Dict, List, Any, Callable, Awaitable
import asyncio


class AlbumMiddleware(BaseMiddleware):
    """Middleware to handle media groups (albums)"""
    album_data: Dict[str, List[types.Message]] = {}

    async def __call__(
            self,
            handler: Callable[[types.Message, Dict[str, Any]], Awaitable[Any]],
            message: types.Message,
            data: Dict[str, Any]
    ) -> Any:
        if not message.media_group_id:
            return await handler(message, data)

        if message.media_group_id not in self.album_data:
            self.album_data[message.media_group_id] = []
            asyncio.create_task(self._process_album(handler, message.media_group_id, data))

        self.album_data[message.media_group_id].append(message)
        return

    async def _process_album(
            self,
            handler: Callable[[types.Message, Dict[str, Any]], Awaitable[Any]],
            media_group_id: str,
            data: Dict[str, Any]
    ):
        await asyncio.sleep(1)

        if media_group_id in self.album_data and self.album_data[media_group_id]:
            album_messages = self.album_data.pop(media_group_id)
            data["album"] = album_messages
            await handler(album_messages[0], data)
