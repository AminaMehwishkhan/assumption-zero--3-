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
US_PHONE_PATTERN = re.compile(r"^\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$")

# Assumption: every applicant's name is written in Latin (ASCII) letters.
# This silently rejects names written in Urdu, Arabic, or any other
# non-Latin script, even though POLICY.md REQ-5 says such names must be
# preserved correctly, not rejected outright.
LATIN_NAME_PATTERN = re.compile(r"^[A-Za-z\s\-'.]+$")


class ApplicationCreate(BaseModel):
    first_name: str

    # Assumption: every applicant has a surname / family name.
    # POLICY.md REQ-1 explicitly says this must NOT be required.
    last_name: str

    # Assumption: every applicant has a permanent street address.
    # POLICY.md REQ-2 explicitly says this must NOT be required.
    address: str

    phone: str

    household_size: Optional[int] = 1
    description: Optional[str] = None

    @field_validator("first_name")
    @classmethod
    def first_name_must_be_latin_script(cls, v: str) -> str:
        # ASCII/Latin-only enforcement: rejects names written in Urdu,
        # Arabic, Chinese, or any other non-Latin script.
        if not LATIN_NAME_PATTERN.match(v.strip()):
            raise ValueError(
                "first_name must contain only Latin letters"
            )
        return v

    @field_validator("last_name")
    @classmethod
    def last_name_must_not_be_empty(cls, v: str) -> str:
        # min_length=1-style enforcement: rejects None / "" applicants.
        if v is None or len(v.strip()) == 0:
            raise ValueError("last_name must be a non-empty string")
        return v

    @field_validator("address")
    @classmethod
    def address_must_not_be_empty(cls, v: str) -> str:
        if v is None or len(v.strip()) == 0:
            raise ValueError("address is required")
        return v

    @field_validator("phone")
    @classmethod
    def phone_must_match_us_pattern(cls, v: str) -> str:
        if not US_PHONE_PATTERN.match(v.strip()):
            raise ValueError(
                "phone must be a valid US-format number, e.g. (555) 123-4567"
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
