from typing import Dict, List
from pydantic import BaseModel


class OldConfiguration(BaseModel):
    """
    A configuration in the old data structure format.
    """

    id: int
    name: str
    product: str
    features: Dict[str, Dict[str, int]]
    license_servers: List[str]
    license_server_type: str
    grace_time: int
    client_id: str
