"""Module for license server interface abstract base class."""


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
