"""CryQL V1: evidence-driven GraphQL schema intelligence."""

__version__ = "1.0.0"

from .config import CryQLConfig
from .schema import SchemaGraph

__all__ = ["CryQLConfig", "SchemaGraph", "__version__"]
