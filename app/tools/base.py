from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel

from ..schemas.tools import ToolDefinition, ToolParameter


class ToolContext:
    """Context passed to tools during execution.

    Contains shared resources like database access, configuration, etc.
    """

    def __init__(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.session_id = session_id
        self.user_id = user_id
        self.metadata = metadata or {}


class Tool(ABC):
    """Base class for all tools.

    Tools are the building blocks of the agent system. Each tool performs
    a specific action and returns a result that can be used by the LLM
    to continue the conversation.
    """

    # Tool metadata - override in subclasses
    name: str = ""
    description: str = ""

    @property
    @abstractmethod
    def parameters(self) -> List[ToolParameter]:
        """Define the parameters this tool accepts."""
        pass

    @abstractmethod
    async def execute(self, context: ToolContext, **kwargs) -> Any:
        """Execute the tool with the given arguments.

        Args:
            context: Execution context with shared resources
            **kwargs: Tool-specific arguments

        Returns:
            The result of the tool execution
        """
        pass

    def get_definition(self) -> ToolDefinition:
        """Get the tool definition for LLM consumption."""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=self.parameters
        )

    def validate_args(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize arguments.

        Override this method to add custom validation logic.

        Args:
            args: Raw arguments from the LLM

        Returns:
            Validated and normalized arguments

        Raises:
            ValueError: If validation fails
        """
        validated = {}
        param_map = {p.name: p for p in self.parameters}

        for name, param in param_map.items():
            if name in args:
                validated[name] = args[name]
            elif param.required:
                raise ValueError(f"Missing required parameter: {name}")
            elif param.default is not None:
                validated[name] = param.default

        return validated

    async def __call__(self, context: ToolContext, **kwargs) -> Any:
        """Make the tool callable.

        Validates arguments and executes the tool.
        """
        validated_args = self.validate_args(kwargs)
        return await self.execute(context, **validated_args)
