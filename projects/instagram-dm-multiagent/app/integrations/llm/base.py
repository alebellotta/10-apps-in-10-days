from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel


StructuredT = TypeVar("StructuredT", bound=BaseModel)


class LLMAdapter(ABC):
    @abstractmethod
    async def generate_text(self, prompt: str) -> str:
        raise NotImplementedError

    @abstractmethod
    async def generate_structured(self, prompt: str, schema: type[StructuredT]) -> StructuredT:
        raise NotImplementedError
