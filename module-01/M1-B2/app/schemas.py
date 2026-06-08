"""Pydantic schemas for the Pyrenex Risk API."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class LoanApplication(BaseModel):
    """Strict input schema for /predict aligned with model feature columns."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    loan_amnt: float = Field(..., ge=500, le=40_000, description="Loan amount (USD)")
    int_rate: float = Field(..., ge=0, le=50, description="Interest rate (%)")
    installment: float = Field(..., ge=0, le=5_000, description="Monthly installment (USD)")
    annual_inc: float = Field(..., ge=0, le=10_000_000, description="Annual income (USD)")
    dti: float = Field(..., ge=0, le=100, description="Debt-to-income ratio (%)")
    delinq_2yrs: int = Field(..., ge=0, le=20, description="Delinquencies in the last 2 years")
    fico_range_low: int = Field(..., ge=300, le=850, description="Lower bound of FICO range")
    revol_util: float = Field(..., ge=0, le=150, description="Revolving utilization (%)")
    term: Literal["36 months", "60 months"] = Field(..., description="Loan term")
    grade: str = Field(..., min_length=1, max_length=2, description="Credit grade")
    home_ownership: str = Field(..., min_length=1, description="Home ownership status")
    verification_status: str = Field(..., min_length=1, description="Income verification status")
    purpose: str = Field(..., min_length=1, description="Purpose of the loan")
    emp_length: str = Field(..., min_length=1, description="Employment length bucket")


class Prediction(BaseModel):
    """Output schema for /predict."""

    prediction: int = Field(..., description="0 = Fully Paid, 1 = Charged Off")
    probability: float = Field(..., ge=0.0, le=1.0)
    model_version: str
    request_id: str


class HealthResponse(BaseModel):
    status: str
