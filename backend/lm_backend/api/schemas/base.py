"""Base schemas for the License Manager API."""


from pydantic import BaseModel


class BaseCreateSchema(BaseModel):
    """
    Base class for creating objects in the database.
    """

    pass


class BaseUpdateSchema(BaseModel):
    """
    Base class for updating objects in the database.
    """

    pass
