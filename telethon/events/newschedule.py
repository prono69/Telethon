import re

from .common import EventBuilder, EventCommon, name_inner_event, _into_id_set
from .. import utils
from ..tl import types


@name_inner_event
class NewScheduled(EventBuilder):
    def __init__(
        self, chats=None, *, blacklist_chats=False, func=None, pattern=None
    ):
        super().__init__(chats, blacklist_chats=blacklist_chats, func=func)
        if isinstance(pattern, str):
            self.pattern = re.compile(pattern).match
        elif not pattern or callable(pattern):
            self.pattern = pattern
        elif hasattr(pattern, "match") and callable(pattern.match):
            self.pattern = pattern.match
        else:
            raise TypeError("Invalid pattern type given")

        self._no_check = all(
            x is None
            for x in (
                self.chats,
                self.func,
                self.pattern,
            )
        )

    @classmethod
    def build(cls, update, others=None, self_id=None):
        if isinstance(update, types.UpdateNewScheduledMessage):
            return cls.Event(update.message)
        return

    def filter(self, event):
        if self._no_check:
            return event

        if self.pattern:
            match = self.pattern(event.message.message or "")
            if not match:
                return
            event.pattern_match = match

        return super().filter(event)

    class Event(EventCommon):
        def __init__(self, message):
            self.__dict__["_init"] = False
            super().__init__(
                chat_peer=message.peer_id,
                msg_id=message.id,
                broadcast=bool(message.post),
            )

            self.pattern_match = None
            self.message = message

        def _set_client(self, client):
            super()._set_client(client)
            m = self.message
            m._finish_init(client, self._entities, None)
            self.__dict__["_init"] = True  # No new attributes can be set

        def __getattr__(self, item):
            if item in self.__dict__:
                return self.__dict__[item]
            else:
                return getattr(self.message, item)

        def __setattr__(self, name, value):
            if not self.__dict__["_init"] or name in self.__dict__:
                self.__dict__[name] = value
            else:
                setattr(self.message, name, value)

        async def edit(self, *args, **kwargs):
            return await self.message.edit(*args, **kwargs)

        async def delete(self, *args, **kwargs):
            kwargs["is_scheduled"] = True
            return await self.message.delete(*args, **kwargs)
        
