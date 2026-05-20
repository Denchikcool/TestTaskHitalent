from datetime import date, datetime
from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("departments.id", ondelete="CASCADE"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    children: Mapped[list["Department"]] = relationship("Department", back_populates="parent", cascade="all, delete-orphan")
    parent: Mapped["Department | None"] = relationship("Department", back_populates="children", remote_side="Department.id")
    employees: Mapped[list["Employee"]] = relationship("Employee", back_populates="department", cascade="all, delete-orphan")

class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    department_id: Mapped[int] = mapped_column(Integer, ForeignKey("departments.id", ondelete="CASCADE"), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    position: Mapped[str] = mapped_column(String(200), nullable=False)
    hired_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    department: Mapped["Department"] = relationship("Department", back_populates="employees")