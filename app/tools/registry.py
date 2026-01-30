from typing import Any, Dict, List, Optional, Type
import logging

from .base import Tool, ToolContext
from ..schemas.tools import ToolDefinition, ToolCallRequest, ToolCallResult

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for managing and executing tools.

    The registry is responsible for:
    - Registering tools by name
    - Providing tool definitions to the LLM
    - Executing tool calls and returning results
    """

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool instance.

        Args:
            tool: The tool instance to register
        """
        if tool.name in self._tools:
            logger.warning(f"Overwriting existing tool: {tool.name}")
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")

    def register_class(self, tool_class: Type[Tool]) -> None:
        """Register a tool by its class (instantiates it).

        Args:
            tool_class: The tool class to register
        """
        tool = tool_class()
        self.register(tool)

    def unregister(self, name: str) -> None:
        """Unregister a tool by name.

        Args:
            name: The name of the tool to unregister
        """
        if name in self._tools:
            del self._tools[name]
            logger.info(f"Unregistered tool: {name}")

    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name.

        Args:
            name: The name of the tool

        Returns:
            The tool instance or None if not found
        """
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

    def get_definitions(self) -> List[ToolDefinition]:
        """Get definitions for all registered tools.

        Returns:
            List of tool definitions for LLM consumption
        """
        return [tool.get_definition() for tool in self._tools.values()]

    def get_definitions_openai(self) -> List[Dict[str, Any]]:
        """Get tool definitions in OpenAI format."""
        return [defn.to_openai_format() for defn in self.get_definitions()]

    def get_definitions_anthropic(self) -> List[Dict[str, Any]]:
        """Get tool definitions in Anthropic format."""
        return [defn.to_anthropic_format() for defn in self.get_definitions()]

    async def execute(
        self,
        request: ToolCallRequest,
        context: Optional[ToolContext] = None
    ) -> ToolCallResult:
        """Execute a tool call.

        Args:
            request: The tool call request
            context: Optional execution context

        Returns:
            The result of the tool execution
        """
        tool = self.get(request.tool_name)

        if tool is None:
            return ToolCallResult(
                tool_call_id=request.tool_call_id,
                tool_name=request.tool_name,
                result=None,
                success=False,
                error=f"Unknown tool: {request.tool_name}"
            )

        context = context or ToolContext()

        try:
            result = await tool(context, **request.arguments)
            return ToolCallResult(
                tool_call_id=request.tool_call_id,
                tool_name=request.tool_name,
                result=result,
                success=True
            )
        except Exception as e:
            logger.exception(f"Error executing tool {request.tool_name}")
            return ToolCallResult(
                tool_call_id=request.tool_call_id,
                tool_name=request.tool_name,
                result=None,
                success=False,
                error=str(e)
            )


# Global registry instance
_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """Get the global tool registry.

    Creates and initializes the registry on first call.
    """
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
        _initialize_default_tools(_registry)
    return _registry


def _initialize_default_tools(registry: ToolRegistry) -> None:
    """Initialize the registry with default tools."""
    # Import here to avoid circular imports
    from .discount_tools import (
        CalculateAgeDiscountTool,
        CalculateDisabilityDiscountTool,
        CalculateMedicalDiscountTool,
        GetBestDiscountTool,
    )
    from .customer_tools import (
        LookupCustomerTool,
        CreateCustomerTool,
        UpdateCustomerTool,
        ListCustomersTool,
    )
    from .rental_tools import (
        CreateRentalTool,
        GetRentalHistoryTool,
        CancelRentalTool,
    )
    from .info_tools import (
        GetPricingInfoTool,
        GetServiceInfoTool,
    )

    # Register all tools
    tools = [
        CalculateAgeDiscountTool(),
        CalculateDisabilityDiscountTool(),
        CalculateMedicalDiscountTool(),
        GetBestDiscountTool(),
        LookupCustomerTool(),
        CreateCustomerTool(),
        UpdateCustomerTool(),
        ListCustomersTool(),
        CreateRentalTool(),
        GetRentalHistoryTool(),
        CancelRentalTool(),
        GetPricingInfoTool(),
        GetServiceInfoTool(),
    ]

    for tool in tools:
        registry.register(tool)
