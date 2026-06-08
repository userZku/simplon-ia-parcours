"""Shared fixtures for M1-B2 tests."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    """TestClient with lifespan triggered (model loaded)."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def valid_payload() -> dict:
    """Valid loan application payload aligned with model feature columns."""
    return {
        "loan_amnt": 10000.0,
        "term": "36 months",
        "int_rate": 12.5,
        "installment": 334.21,
        "annual_inc": 60000.0,
        "dti": 18.4,
        "delinq_2yrs": 0,
        "fico_range_low": 690,
        "revol_util": 45.2,
        "grade": "C",
        "home_ownership": "RENT",
        "verification_status": "Verified",
        "purpose": "debt_consolidation",
        "emp_length": "5 years",
    }
