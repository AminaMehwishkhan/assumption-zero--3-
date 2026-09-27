"""
Fix Planner + Patch Applier

Generates a repair plan grouped by layer, and can APPLY real text patches
to the actual demo_target source files (not a simulated diff). Every patch
here is a plain string replacement against the real file contents, so
"Apply Demo Fix" in the dashboard produces a real, diffable code change
that persists on disk and is what the Verifier re-analyzes and re-runs
the Noor journey against.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RepairAction:
    layer: str
    title: str
    file: str
    description: str


@dataclass
class RepairPlan:
    actions: list[RepairAction] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"actions": [a.__dict__ for a in self.actions]}


def _rel(path: Path) -> str:
    """Return a forward-slash relative path from the repo root for display."""
    try:
        from analyzer.models import _REPO_ROOT
        return str(path.resolve().relative_to(_REPO_ROOT)).replace("\\", "/")
    except (ValueError, OSError):
        return str(path).replace("\\", "/")


def generate_plan(demo_target_root: str | Path) -> RepairPlan:
    root = Path(demo_target_root)
    return RepairPlan(
        actions=[
            RepairAction(
                layer="frontend",
                title="Make surname & address optional; accept international phone and non-Latin names",
                file=_rel(root / "frontend" / "index.html"),
                description=(
                    "Remove `required` from last name and address inputs; "
                    "replace the US-only phone regex with E.164 validation; "
                    "remove the Latin-only name check."
                ),
            ),
            RepairAction(
                layer="backend",
                title="Allow nullable last_name / address; accept E.164 phone, Unicode names",
                file=_rel(root / "backend" / "schemas.py"),
                description=(
                    "Change `last_name`/`address` to Optional[str] = None and "
                    "swap the US phone validator for an E.164 pattern; remove "
                    "the Latin-only name validator."
                ),
            ),
            RepairAction(
                layer="database",
                title="Migrate last_name / address to nullable columns",
                file=_rel(root / "database" / "migration.sql"),
                description="Drop the NOT NULL constraint on last_name and address.",
            ),
            RepairAction(
                layer="tests",
                title="Add regression tests for the repaired journeys",
                file=_rel(root / "tests" / "test_applications.py"),
                description=(
                    "Add tests for: no-surname applicant, no-address applicant, "
                    "international phone number, idempotent resubmission, and "
                    "non-Latin-script name."
                ),
            ),
            RepairAction(
                layer="resilience",
                title="Add idempotency-key based dedupe to the submit endpoint",
                file=_rel(root / "backend" / "main.py"),
                description=(
                    "Accept an `Idempotency-Key` header; if a row with that key "
                    "already exists, return it instead of inserting a new one."
                ),
            ),
        ]
    )


# --- Patch application -----------------------------------------------------

def _replace_once(path: Path, old: str, new: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        return False
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    return True


def apply_all_fixes(demo_target_root: str | Path) -> list[str]:
    """Applies every fix directly to the real demo_target source files.
    Returns a list of human-readable change descriptions actually made."""
    root = Path(demo_target_root)
    applied: list[str] = []

    # --- schemas.py: nullable last_name/address + E.164 phone ---
    schemas_path = root / "backend" / "schemas.py"
    text = schemas_path.read_text(encoding="utf-8")
    if "from typing import Optional" in text:
        new_text = text
        new_text = new_text.replace(
            "US_PHONE_PATTERN = re.compile(r\"^\\(?\\d{3}\\)?[-.\\s]?\\d{3}[-.\\s]?\\d{4}$\")",
            "# REPAIRED: accepts E.164 international numbers, e.g. +923001234567\n"
            "INTL_PHONE_PATTERN = re.compile(r\"^\\+?[1-9]\\d{7,14}$\")",
        )
        new_text = new_text.replace(
            '    @field_validator("first_name")\n'
            "    @classmethod\n"
            "    def first_name_must_be_latin_script(cls, v: str) -> str:\n"
            "        # ASCII/Latin-only enforcement: rejects names written in Urdu,\n"
            "        # Arabic, Chinese, or any other non-Latin script.\n"
            "        if not LATIN_NAME_PATTERN.match(v.strip()):\n"
            "            raise ValueError(\n"
            '                "first_name must contain only Latin letters"\n'
            "            )\n"
            "        return v\n\n"
            '    @field_validator("last_name")\n',
            # REPAIRED: no Latin-script restriction on first_name (POLICY.md REQ-5).
            '    @field_validator("last_name")\n',
        )
        new_text = new_text.replace(
            "    # Assumption: every applicant has a surname / family name.\n"
            "    # POLICY.md REQ-1 explicitly says this must NOT be required.\n"
            "    last_name: str",
            "    # REPAIRED: surname is optional (POLICY.md REQ-1).\n"
            "    last_name: Optional[str] = None",
        )
        new_text = new_text.replace(
            "    # Assumption: every applicant has a permanent street address.\n"
            "    # POLICY.md REQ-2 explicitly says this must NOT be required.\n"
            "    address: str",
            "    # REPAIRED: address is optional (POLICY.md REQ-2).\n"
            "    address: Optional[str] = None",
        )
        new_text = new_text.replace(
            '    @field_validator("last_name")\n'
            "    @classmethod\n"
            "    def last_name_must_not_be_empty(cls, v: str) -> str:\n"
            "        # min_length=1-style enforcement: rejects None / \"\" applicants.\n"
            "        if v is None or len(v.strip()) == 0:\n"
            '            raise ValueError("last_name must be a non-empty string")\n'
            "        return v\n\n"
            '    @field_validator("address")\n'
            "    @classmethod\n"
            "    def address_must_not_be_empty(cls, v: str) -> str:\n"
            "        if v is None or len(v.strip()) == 0:\n"
            '            raise ValueError("address is required")\n'
            "        return v\n\n"
            '    @field_validator("phone")\n'
            "    @classmethod\n"
            "    def phone_must_match_us_pattern(cls, v: str) -> str:\n"
            "        if not US_PHONE_PATTERN.match(v.strip()):\n"
            "            raise ValueError(\n"
            '                "phone must be a valid US-format number, e.g. (555) 123-4567"\n'
            "            )\n"
            "        return v\n",
            '    @field_validator("phone")\n'
            "    @classmethod\n"
            "    def phone_must_be_valid_international_number(cls, v: str) -> str:\n"
            "        # REPAIRED: accepts international / E.164 numbers (POLICY.md REQ-3).\n"
            "        normalized = re.sub(r\"[^\\d+]\", \"\", v.strip())\n"
            "        if not INTL_PHONE_PATTERN.match(normalized):\n"
            "            raise ValueError(\n"
            '                "phone must be a valid international number, e.g. +923001234567"\n'
            "            )\n"
            "        return v\n",
        )
        new_text = new_text.replace(
            "\n# Assumption: every applicant's name is written in Latin (ASCII) letters.\n"
            "# This silently rejects names written in Urdu, Arabic, or any other\n"
            "# non-Latin script, even though POLICY.md REQ-5 says such names must be\n"
            "# preserved correctly, not rejected outright.\n"
            "LATIN_NAME_PATTERN = re.compile(r\"^[A-Za-z\\s\\-'.]+$\")\n",
            "\n# REPAIRED: no Latin-script restriction on names (POLICY.md REQ-5).\n",
        )
        if new_text != text:
            schemas_path.write_text(new_text, encoding="utf-8")
            applied.append(f"Patched {_rel(schemas_path)}: nullable last_name/address, E.164 phone, Unicode name support")

    # --- migration.sql: drop NOT NULL on last_name/address ---
    mig_path = root / "database" / "migration.sql"
    text = mig_path.read_text(encoding="utf-8")
    new_text = text.replace(
        "    last_name TEXT NOT NULL,              -- ASSUMPTION: surname required\n"
        "    address TEXT NOT NULL,                -- ASSUMPTION: permanent address required\n",
        "    last_name TEXT,                       -- REPAIRED: surname optional (REQ-1)\n"
        "    address TEXT,                         -- REPAIRED: address optional (REQ-2)\n",
    )
    if new_text != text:
        mig_path.write_text(new_text, encoding="utf-8")
        applied.append(f"Patched {_rel(mig_path)}: last_name/address are now nullable columns")

    # --- main.py: idempotency-key dedupe ---
    main_path = root / "backend" / "main.py"
    text = main_path.read_text(encoding="utf-8")
    if "Idempotency-Key" not in text:
        new_text = text.replace(
            "from fastapi import FastAPI, HTTPException",
            "from fastapi import FastAPI, HTTPException, Header",
        )
        new_text = new_text.replace(
            "def create_application(payload: ApplicationCreate) -> ApplicationOut:",
            "def create_application(\n"
            "    payload: ApplicationCreate,\n"
            "    idempotency_key: str | None = Header(default=None, alias=\"Idempotency-Key\"),\n"
            ") -> ApplicationOut:",
        )
        new_text = new_text.replace(
            "    conn = database.get_connection()\n"
            "    try:\n"
            "        cursor = conn.execute(\n"
            "            \"\"\"\n"
            "            INSERT INTO applications\n"
            "                (first_name, last_name, address, phone, household_size, description, status)\n"
            "            VALUES (?, ?, ?, ?, ?, ?, 'submitted')\n"
            "            \"\"\",\n",
            "    conn = database.get_connection()\n"
            "    try:\n"
            "        # REPAIRED (REQ-4): if this idempotency key was already used,\n"
            "        # return the existing row instead of inserting a duplicate.\n"
            "        if idempotency_key:\n"
            "            existing = conn.execute(\n"
            "                \"SELECT * FROM applications WHERE idempotency_key = ?\",\n"
            "                (idempotency_key,),\n"
            "            ).fetchone()\n"
            "            if existing is not None:\n"
            "                return ApplicationOut(**dict(existing))\n"
            "\n"
            "        cursor = conn.execute(\n"
            "            \"\"\"\n"
            "            INSERT INTO applications\n"
            "                (first_name, last_name, address, phone, household_size, description, status, idempotency_key)\n"
            "            VALUES (?, ?, ?, ?, ?, ?, 'submitted', ?)\n"
            "            \"\"\",\n",
        )
        new_text = new_text.replace(
            "                payload.household_size or 1,\n"
            "                payload.description,\n"
            "            ),\n"
            "        )\n"
            "        conn.commit()",
            "                payload.household_size or 1,\n"
            "                payload.description,\n"
            "                idempotency_key,\n"
            "            ),\n"
            "        )\n"
            "        conn.commit()",
        )
        if new_text != text:
            main_path.write_text(new_text, encoding="utf-8")
            applied.append(f"Patched {_rel(main_path)}: idempotency-key based dedupe on submission")

    # --- frontend index.html: relax required fields + accept intl phone ---
    html_path = root / "frontend" / "index.html"
    text = html_path.read_text(encoding="utf-8")
    new_text = text
    new_text = new_text.replace(
        "    <!-- ASSUMPTION: surname required in the DOM, contradicts POLICY.md REQ-1 -->\n"
        "    <label>Last name\n"
        '      <input id="last_name" required />\n'
        "    </label>",
        "    <!-- REPAIRED: surname optional (POLICY.md REQ-1) -->\n"
        "    <label>Last name (optional)\n"
        '      <input id="last_name" />\n'
        "    </label>",
    )
    new_text = new_text.replace(
        "    <!-- ASSUMPTION: street address required in the DOM, contradicts POLICY.md REQ-2 -->\n"
        "    <label>Street address\n"
        '      <input id="address" required />\n'
        "    </label>",
        "    <!-- REPAIRED: address optional (POLICY.md REQ-2) -->\n"
        "    <label>Street address / current location (optional)\n"
        '      <input id="address" />\n'
        "    </label>",
    )
    new_text = new_text.replace(
        "const US_PHONE_REGEX = /^\\(?\\d{3}\\)?[-.\\s]?\\d{3}[-.\\s]?\\d{4}$/;\n"
        "// ASSUMPTION: applicant names must be Latin-script only, contradicts POLICY.md REQ-5\n"
        "const LATIN_NAME_REGEX = /^[A-Za-z\\s\\-'.]+$/;",
        "// REPAIRED: accepts international / E.164 numbers (POLICY.md REQ-3)\n"
        "const US_PHONE_REGEX = /^\\+?[1-9]\\d{7,14}$/;\n"
        "// REPAIRED: no Latin-script restriction on names (POLICY.md REQ-5)",
    )
    new_text = new_text.replace(
        "  if (!first_name) { return showError('First name is required.'); }\n"
        "  if (!LATIN_NAME_REGEX.test(first_name)) {\n"
        "    return showError('First name must use Latin letters only.');\n"
        "  }\n"
        "  if (!last_name) { return showError('Last name is required.'); }\n"
        "  if (!address) { return showError('Street address is required.'); }\n",
        "  if (!first_name) { return showError('First name is required.'); }\n",
    )
    if new_text != text:
        html_path.write_text(new_text, encoding="utf-8")
        applied.append(f"Patched {_rel(html_path)}: optional surname/address, international phone, Unicode names accepted")

    # --- ApplicationForm.tsx: mirror the same repairs in the canonical React source ---
    tsx_path = root / "frontend" / "ApplicationForm.tsx"
    text = tsx_path.read_text(encoding="utf-8")
    new_text = text
    new_text = new_text.replace(
        "const US_PHONE_REGEX = /^\\(?\\d{3}\\)?[-.\\s]?\\d{3}[-.\\s]?\\d{4}$/;\n"
        "// ASSUMPTION: applicant names must be Latin-script only, contradicts POLICY.md REQ-5\n"
        "const LATIN_NAME_REGEX = /^[A-Za-z\\s\\-'.]+$/;",
        "// REPAIRED: accepts international / E.164 numbers (POLICY.md REQ-3)\n"
        "const INTL_PHONE_REGEX = /^\\+?[1-9]\\d{7,14}$/;\n"
        "// REPAIRED: no Latin-script restriction on names (POLICY.md REQ-5)",
    )
    new_text = new_text.replace(
        "    if (!firstName.trim()) return \"First name is required.\";\n"
        "    if (!LATIN_NAME_REGEX.test(firstName.trim())) {\n"
        "      // ASSUMPTION: name must use Latin letters only.\n"
        "      // POLICY.md REQ-5 says non-Latin names (Urdu, Arabic, etc) must be\n"
        "      // preserved, not rejected.\n"
        "      return \"First name must use Latin letters only.\";\n"
        "    }\n"
        "    if (!lastName.trim()) return \"Last name is required.\"; // <- required\n"
        "    if (!address.trim()) return \"Street address is required.\"; // <- required\n"
        "    if (!US_PHONE_REGEX.test(phone.trim())) {",
        "    if (!firstName.trim()) return \"First name is required.\";\n"
        "    if (!INTL_PHONE_REGEX.test(phone.trim().replace(/[^\\d+]/g, \"\"))) {",
    )
    new_text = new_text.replace(
        '      <label>\n'
        '        Last name\n'
        '        <input\n'
        '          required\n'
        '          value={lastName}\n'
        '          onChange={(e) => setLastName(e.target.value)}\n'
        '        />\n'
        '      </label>\n'
        '      <label>\n'
        '        Street address\n'
        '        <input\n'
        '          required\n'
        '          value={address}\n'
        '          onChange={(e) => setAddress(e.target.value)}\n'
        '        />\n'
        '      </label>',
        '      <label>\n'
        '        Last name (optional)\n'
        '        <input\n'
        '          value={lastName}\n'
        '          onChange={(e) => setLastName(e.target.value)}\n'
        '        />\n'
        '      </label>\n'
        '      <label>\n'
        '        Street address (optional)\n'
        '        <input\n'
        '          value={address}\n'
        '          onChange={(e) => setAddress(e.target.value)}\n'
        '        />\n'
        '      </label>',
    )
    new_text = new_text.replace(
        '  const [firstName, setFirstName] = useState("");\n'
        "  // ASSUMPTION: every applicant has a surname. POLICY.md REQ-1 says this\n"
        "  // must not be required, but the field below is `required` in the DOM\n"
        "  // and is validated as required in handleSubmit.\n"
        '  const [lastName, setLastName] = useState("");\n'
        "  // ASSUMPTION: every applicant has a permanent street address.\n"
        "  // POLICY.md REQ-2 says this must not be required.\n"
        '  const [address, setAddress] = useState("");',
        '  const [firstName, setFirstName] = useState("");\n'
        "  // REPAIRED: surname is optional (POLICY.md REQ-1).\n"
        '  const [lastName, setLastName] = useState("");\n'
        "  // REPAIRED: address is optional (POLICY.md REQ-2).\n"
        '  const [address, setAddress] = useState("");',
    )
    if new_text != text:
        tsx_path.write_text(new_text, encoding="utf-8")
        applied.append(f"Patched {_rel(tsx_path)}: optional surname/address, international phone accepted")

    # --- tests: add regression coverage ---
    tests_path = root / "tests" / "test_applications.py"
    text = tests_path.read_text(encoding="utf-8")
    marker = "# --- Coverage gaps intentionally left for Assumption Zero to discover ---"
    if marker in text and "test_applicant_without_surname_is_accepted" not in text:
        regression_tests = '''

def test_applicant_without_surname_is_accepted():
    """Regression test for POLICY.md REQ-1 (single legal name / no surname)."""
    payload = make_payload()
    payload["last_name"] = None
    res = client.post("/applications", json=payload)
    assert res.status_code == 201


def test_applicant_without_address_is_accepted():
    """Regression test for POLICY.md REQ-2 (no permanent address)."""
    payload = make_payload()
    payload["address"] = None
    res = client.post("/applications", json=payload)
    assert res.status_code == 201


def test_international_phone_number_is_accepted():
    """Regression test for POLICY.md REQ-3 (international phone support)."""
    payload = make_payload()
    payload["phone"] = "+923001234567"
    res = client.post("/applications", json=payload)
    assert res.status_code == 201


def test_retried_submission_with_same_idempotency_key_is_not_duplicated():
    """Regression test for POLICY.md REQ-4 (no duplicate on retry)."""
    payload = make_payload()
    headers = {"Idempotency-Key": "test-key-123"}
    first = client.post("/applications", json=payload, headers=headers)
    second = client.post("/applications", json=payload, headers=headers)
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]


def test_applicant_with_non_latin_name_is_accepted():
    """Regression test for POLICY.md REQ-5 (non-Latin script names)."""
    payload = make_payload()
    payload["first_name"] = "\u0646\u0648\u0631"  # "Noor" written in Urdu/Arabic script
    res = client.post("/applications", json=payload)
    assert res.status_code == 201
'''
        new_text = text.split(marker)[0] + marker + regression_tests
        tests_path.write_text(new_text, encoding="utf-8")
        applied.append(f"Patched {_rel(tests_path)}: added 5 regression tests for REQ-1..REQ-5")

    return applied
