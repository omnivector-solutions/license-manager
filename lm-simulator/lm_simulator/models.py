from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class License(Base):
    __tablename__ = "licenses"

    name: Mapped[str] = mapped_column(String, primary_key=True)
    total: Mapped[int] = mapped_column(Integer, nullable=False)
    licenses_in_use: Mapped[list["LicenseInUse"]] = relationship(
        "LicenseInUse",
        back_populates="license",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    license_server_type: Mapped[str] = mapped_column(String, nullable=False)

    @property
    def in_use(self):
        return sum(license_in_use.quantity for license_in_use in self.licenses_in_use)


class LicenseInUse(Base):
    __tablename__ = "licenses_in_use"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    user_name: Mapped[str] = mapped_column(String, nullable=False)
    lead_host: Mapped[str] = mapped_column(String, nullable=False)
    license_name: Mapped[str] = mapped_column(String, ForeignKey("licenses.name"), nullable=False)

    license: Mapped["License"] = relationship("License", back_populates="licenses_in_use", lazy="selectin")
