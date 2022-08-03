"""
Functions to help with field validations for sorting model instances.
"""
from typing import Optional

from fastapi import HTTPException, status

from lm_backend.api_schemas import LicenseUseWithBooking


class LicenseUseWithBookingSortFieldChecker:
    """
    Validate if the sort field is a valid field in the model.
    """
    _model = LicenseUseWithBooking

    def __call__(self, sort_field: Optional[str] = None) -> str:
        if sort_field is not None:
            if sort_field not in LicenseUseWithBooking.__fields__.keys():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid sorting column requested: {sort_field}. Must be one of {self.available_fields()}.",
                )
        return sort_field

    @classmethod
    def available_fields(cls):
        return list(cls._model.__fields__.keys())
