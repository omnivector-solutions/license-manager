from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from lm_simulator.database import Base


class License(Base):
    __tablename__ = "licenses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, unique=True, nullable=False)
    total = Column(Integer, nullable=False)

    # this relationship is a must to be able to calculate the in_use value, we don't store the in_use value.
    licenses_in_use = relationship("LicenseInUse", back_populates="license")


class LicenseInUse(Base):
    __tablename__ = "licenses_in_use"

    id = Column(Integer, primary_key=True, index=True)
    quantity = Column(Integer, nullable=False)
    user_name = Column(String, nullable=False)
    lead_host = Column(String, nullable=False)
    license_name = Column(String, ForeignKey("licenses.name"), nullable=False)

    license = relationship("License", back_populates="licenses_in_use")

    # the quantity, user_name, lead_host and license_name must be unique.
    __table_args__ = (
        UniqueConstraint("quantity", "user_name", "lead_host", "license_name", name="_unique_contraint"),
    )
