"""Module for license server interface abstract base class."""
from typing import List

from pydantic import BaseModel, Field

from lm_agent.config import PRODUCT_FEATURE_RX


class LicenseServerInterface:
    """
    Abstract base class for License Server interface.

    The logic for obtaining the data output from the License Server should be encapsulated in
    the ``get_output_from_server`` method.

    After obtaining the output, the parsing and manipulation of the data should be implemented in
    the ``get_report_item`` method.

    The license information should be parsed into a ``LicenseReportItem``.
    """

    @classmethod
    def __subclasshook__(cls, subclass):
        return (
            all(
                [
                    hasattr(subclass, "get_output_from_server"),
                    callable(subclass.get_output_from_server),
                    hasattr(subclass, "get_report_item"),
                    callable(subclass.get_report_item),
                ]
            )
            or NotImplemented
        )

    def get_output_from_server(self, product_feature: str):
        """Return output from license server for the indicated features."""
        raise NotImplementedError("get_output_from_server not implemented")

    def get_report_item(self, feature_id: int, product_feature: str):
        """Parse license server output into a report item for the indicated feature."""
        raise NotImplementedError("get_report_item not implemented")


class LicenseUsesItem(BaseModel):
    """
    A list of usage information for a license.
    """

    username: str
    lead_host: str
    booked: int


class LicenseReportItem(BaseModel):
    """
    An item in a LicenseReport, a count of tokens for one product/feature.
    """

    feature_id: int
    product_feature: str = Field(..., pattern=PRODUCT_FEATURE_RX)
    used: int
    total: int
    uses: List[LicenseUsesItem] = []
