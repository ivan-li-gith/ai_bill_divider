from datetime import datetime, date
from sqlalchemy import String, Integer, Numeric, Boolean, ForeignKey, DateTime, Date, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import List, Optional

class Base(DeclarativeBase):
    pass

class Profile(Base):
    __tablename__ = "profiles"
    user_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(255))
    email: Mapped[Optional[str]] = mapped_column(String(255))

class Group(Base):
    __tablename__ = "groups"
    group_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_name: Mapped[Optional[str]] = mapped_column(String(255))
    owner_id: Mapped[Optional[str]] = mapped_column(String(255))
    group_type: Mapped[str] = mapped_column(String(50), default="group")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    members: Mapped[List["GroupMember"]] = relationship(back_populates="group", cascade="all, delete-orphan")

class GroupMember(Base):
    __tablename__ = "group_members"
    group_member_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[Optional[int]] = mapped_column(ForeignKey("groups.group_id", ondelete="CASCADE"))
    member_name: Mapped[Optional[str]] = mapped_column(String(255))
    member_email: Mapped[Optional[str]] = mapped_column(String(255))
    user_id: Mapped[Optional[str]] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), default="member")
    group: Mapped["Group"] = relationship(back_populates="members")

class UtilityBill(Base):
    __tablename__ = "utility_bills"
    bill_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(255))
    group_id: Mapped[Optional[int]] = mapped_column(Integer)
    billing_month: Mapped[Optional[str]] = mapped_column(String(255))
    service_name: Mapped[Optional[str]] = mapped_column(String(255))
    service_period: Mapped[Optional[str]] = mapped_column(String(255))
    total_amount_due: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))

class UtilitySplit(Base):
    __tablename__ = "utility_splits"
    split_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(255))
    group_id: Mapped[Optional[int]] = mapped_column(Integer)
    billing_month: Mapped[Optional[str]] = mapped_column(String(255))
    roommate_name: Mapped[Optional[str]] = mapped_column(String(255))
    current_month_split: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    rollover_amount: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    total_owed: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    is_paid: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)

class Subscription(Base):
    __tablename__ = "subscriptions"
    subscription_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(255))
    group_id: Mapped[Optional[int]] = mapped_column(ForeignKey("groups.group_id", ondelete="CASCADE"))
    expense_name: Mapped[Optional[str]] = mapped_column(String(255))
    amount: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    billing_day: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    group: Mapped["Group"] = relationship()

class Expense(Base):
    __tablename__ = "expenses"
    expense_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(255))
    group_id: Mapped[Optional[int]] = mapped_column(ForeignKey("groups.group_id", ondelete="CASCADE"))
    expense_date: Mapped[Optional[date]] = mapped_column(Date)
    description: Mapped[Optional[str]] = mapped_column(String(255))
    amount: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    payer_id: Mapped[Optional[str]] = mapped_column(String(255))
    split_method: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    splits: Mapped[List["ExpenseSplit"]] = relationship(back_populates="expense", cascade="all, delete-orphan")
    group: Mapped["Group"] = relationship()

class ExpenseSplit(Base):
    __tablename__ = "expense_splits"
    split_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    expense_id: Mapped[Optional[int]] = mapped_column(ForeignKey("expenses.expense_id", ondelete="CASCADE"))
    roommate_name: Mapped[Optional[str]] = mapped_column(String(255))
    amount_owed: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    is_paid: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    expense: Mapped["Expense"] = relationship(back_populates="splits")