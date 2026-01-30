from .base import Tool, ToolContext
from .registry import ToolRegistry, get_registry
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
