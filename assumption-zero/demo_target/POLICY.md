# RapidRelief Emergency Assistance Program — Applicant Policy

**Document type:** Public eligibility & access policy
**Applies to:** RapidRelief Assistance Request Portal (`demo_target`)

## 1. Purpose

RapidRelief provides emergency financial and material assistance to people
affected by disasters (floods, earthquakes, displacement, fire). This portal
is often the *only* channel available to applicants, sometimes from a shared
phone in a relief camp with intermittent signal.

## 2. Who must be able to apply

This program explicitly serves populations who do not fit "standard" identity
or contact-information assumptions. The following requirements are binding:

### REQ-1 — Name
> Applicants must be able to apply regardless of whether they have a surname.
> A single legal name (mononym) is a valid, complete identity. The system
> MUST NOT require a last name / family name / surname field.

### REQ-2 — Address
> Applicants must be able to apply regardless of whether they have a
> permanent residential address. Displaced persons, shelter residents, and
> people who have lost their homes MUST be able to submit a request with no
> street address, or with a non-standard location description (e.g. "Camp 3,
> near the old mosque, Muzaffargarh").

### REQ-3 — Phone number format
> Applicants must be able to apply using an international or local-format
> phone number, not only a fixed domestic pattern. The system explicitly
> advertises international applicant support and MUST accept valid
> international phone numbers (E.164 format), including but not limited to
> Pakistani numbers (+92...).

### REQ-4 — Connectivity resilience
> Applicants often have unreliable internet access. The system MUST NOT lose
> a partially completed or submitted request due to a dropped connection,
> MUST NOT create duplicate assistance requests from a retried submission,
> and MUST leave the applicant in a clear, recoverable state after a network
> interruption.

### REQ-5 — Name script / Unicode (stretch)
> Applicant names and locations may be written in non-Latin scripts (Urdu,
> Arabic, etc). The system SHOULD preserve and correctly store these values
> without corruption or silent truncation.

## 3. Non-goals

This document does not cover authentication, payment processing, or
multi-tenant administration. Assistance requests are processed by relief
caseworkers after submission.

## 4. Compliance

Every deployed version of the RapidRelief portal must be verifiable against
REQ-1 through REQ-5 above. A request that satisfies these requirements is
considered **human-compatible**.
