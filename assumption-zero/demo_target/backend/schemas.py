"""
RapidRelief API schemas.

NOTE FOR REVIEWERS: this file intentionally contains real-world-style
validation bugs used as the Assumption Zero demo target. Nothing here is a
stub — these are the actual Pydantic models used by main.py.
"""
from __future__ import annotations

import re
from typing import Optional

from pydantic import BaseModel, field_validator

# Assumption: every applicant's phone number follows a US-style NANP pattern.
# This silently rejects Pakistani numbers (+92...) and most international
# numbers, even though POLICY.md REQ-3 promises international support.
# REPAIRED: accepts E.164 international numbers, e.g. +923001234567
INTL_PHONE_PATTERN = re.compile(r"^\+?[1-9]\d{7,14}$")

# REPAIRED: no Latin-script restriction on names (POLICY.md REQ-5).


class ApplicationCreate(BaseModel):
    first_name: str

    # REPAIRED: surname is optional (POLICY.md REQ-1).
    last_name: Optional[str] = None

    # REPAIRED: address is optional (POLICY.md REQ-2).
    address: Optional[str] = None

    phone: str

    household_size: Optional[int] = 1
    description: Optional[str] = None

    @field_validator("phone")
    @classmethod
    def phone_must_be_valid_international_number(cls, v: str) -> str:
        # REPAIRED: accepts international / E.164 numbers (POLICY.md REQ-3).
        normalized = re.sub(r"[^\d+]", "", v.strip())
        if not INTL_PHONE_PATTERN.match(normalized):
            raise ValueError(
                "phone must be a valid international number, e.g. +923001234567"
            )
        return v


class ApplicationOut(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str] = None
    address: Optional[str] = None
    phone: str
    household_size: int
    description: Optional[str] = None
    status: str
