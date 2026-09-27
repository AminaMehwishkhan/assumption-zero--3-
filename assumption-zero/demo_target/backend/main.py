"""
RapidRelief Emergency Assistance Portal — backend API.

This is the intentionally-flawed demo target analyzed by Assumption Zero.
It is a real, runnable FastAPI service with a real SQLite database — not a
mock. See POLICY.md for the human requirements it is supposed to satisfy.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from . import database
from .schemas import ApplicationCreate, ApplicationOut


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    yield


app = FastAPI(title="RapidRelief Assistance Portal", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/applications", response_model=ApplicationOut, status_code=201)
def create_application(
    payload: ApplicationCreate,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> ApplicationOut:
    """
    Submit a new assistance request.

    ASSUMPTION (connectivity / REQ-4): this endpoint does not honor an
    idempotency key. If a client's connection drops after the server has
    committed the row but before the response reaches the client, a naive
    retry creates a SECOND assistance request for the same person. There is
    no dedupe, and no way for the client to recover "did my submission go
    through?" state. This is the resilience_agent's target finding.
    """
    conn = database.get_connection()
    try:
        # REPAIRED (REQ-4): if this idempotency key was already used,
        # return the existing row instead of inserting a duplicate.
        if idempotency_key:
            existing = conn.execute(
                "SELECT * FROM applications WHERE idempotency_key = ?",
                (idempotency_key,),
            ).fetchone()
            if existing is not None:
                return ApplicationOut(**dict(existing))

        cursor = conn.execute(
            """
            INSERT INTO applications
                (first_name, last_name, address, phone, household_size, description, status, idempotency_key)
            VALUES (?, ?, ?, ?, ?, ?, 'submitted', ?)
            """,
            (
                payload.first_name,
                payload.last_name,
                payload.address,
                payload.phone,
                payload.household_size or 1,
                payload.description,
                idempotency_key,
            ),
        )
        conn.commit()
        new_id = cursor.lastrowid
        row = conn.execute(
            "SELECT * FROM applications WHERE id = ?", (new_id,)
        ).fetchone()
        return ApplicationOut(**dict(row))
    finally:
        conn.close()


@app.get("/applications/{application_id}", response_model=ApplicationOut)
def get_application(application_id: int) -> ApplicationOut:
    conn = database.get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM applications WHERE id = ?", (application_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Application not found")
        return ApplicationOut(**dict(row))
    finally:
        conn.close()


@app.get("/applications")
def list_applications() -> list[dict]:
    conn = database.get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM applications ORDER BY id DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
