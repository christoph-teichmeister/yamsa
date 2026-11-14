import inspect
import logging
import uuid
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class Message:
    uuid = str
    Context: dataclass

    @dataclass
    class Context:
        def __init__(self, *args: object, **kwargs: object) -> None:
            raise NotImplementedError

    @classmethod
    def _from_dict_to_dataclass(cls, context_data: dict) -> dataclass:
        return cls.Context(
            **{
                key: (context_data[key] if val.default == val.empty else context_data.get(key, val.default))
                for key, val in inspect.signature(cls.Context).parameters.items()
            }
        )

    def __name__(self) -> str:
        return str(self.__class__).replace("'", "").replace(">", "").split(".")[-1]

    def __str__(self) -> str:
        return f"{self.__class__} ({self.uuid})"

    def __init__(self, context_data: dict) -> None:
        self.uuid = str(uuid.uuid4())
        self.Context = self._from_dict_to_dataclass(context_data=context_data)

        logger.debug("Creating message '%s' (%s) with %s", self.__name__(), self.uuid, context_data)
