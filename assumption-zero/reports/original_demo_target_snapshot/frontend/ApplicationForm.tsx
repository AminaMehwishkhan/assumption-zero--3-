import { useState } from "react";

/**
 * RapidRelief assistance request form.
 *
 * NOTE FOR REVIEWERS: This component is the real, intentionally-flawed
 * demo-target frontend analyzed by Assumption Zero's frontend_agent.py.
 * It is rendered as plain static HTML+JS in demo_target/frontend/index.html
 * for zero-build-step local running, but this .tsx file is the canonical
 * source the analyzer parses for evidence (JSX + a real React project would
 * use this directly).
 */

const US_PHONE_REGEX = /^\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$/;
// ASSUMPTION: applicant names must be Latin-script only, contradicts POLICY.md REQ-5
const LATIN_NAME_REGEX = /^[A-Za-z\s\-'.]+$/;

export default function ApplicationForm() {
  const [firstName, setFirstName] = useState("");
  // ASSUMPTION: every applicant has a surname. POLICY.md REQ-1 says this
  // must not be required, but the field below is `required` in the DOM
  // and is validated as required in handleSubmit.
  const [lastName, setLastName] = useState("");
  // ASSUMPTION: every applicant has a permanent street address.
  // POLICY.md REQ-2 says this must not be required.
  const [address, setAddress] = useState("");
  const [phone, setPhone] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function validate(): string | null {
    if (!firstName.trim()) return "First name is required.";
    if (!LATIN_NAME_REGEX.test(firstName.trim())) {
      // ASSUMPTION: name must use Latin letters only.
      // POLICY.md REQ-5 says non-Latin names (Urdu, Arabic, etc) must be
      // preserved, not rejected.
      return "First name must use Latin letters only.";
    }
    if (!lastName.trim()) return "Last name is required."; // <- required
    if (!address.trim()) return "Street address is required."; // <- required
    if (!US_PHONE_REGEX.test(phone.trim())) {
      // ASSUMPTION: phone must match a US-style pattern like (555) 123-4567.
      // POLICY.md REQ-3 promises international applicant support, but a
      // Pakistani number like +923001234567 fails this check.
      return "Please enter a valid US phone number, e.g. (555) 123-4567.";
    }
    return null;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const validationError = validate();
    if (validationError) {
      setError(validationError);
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      // ASSUMPTION (REQ-4): no idempotency key is sent, and there is no
      // retry/resume logic. If this request times out, the applicant has
      // no way to know whether it succeeded, and resubmitting creates a
      // duplicate assistance request.
      const res = await fetch("/applications", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          first_name: firstName,
          last_name: lastName,
          address,
          phone,
        }),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail ?? "Submission failed");
      }
    } catch (err: any) {
      setError(err.message ?? "Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <label>
        First name
        <input
          required
          value={firstName}
          onChange={(e) => setFirstName(e.target.value)}
        />
      </label>
      <label>
        Last name
        <input
          required
          value={lastName}
          onChange={(e) => setLastName(e.target.value)}
        />
      </label>
      <label>
        Street address
        <input
          required
          value={address}
          onChange={(e) => setAddress(e.target.value)}
        />
      </label>
      <label>
        Phone (US format)
        <input
          required
          placeholder="(555) 123-4567"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
        />
      </label>
      {error && <p role="alert">{error}</p>}
      <button type="submit" disabled={submitting}>
        {submitting ? "Submitting..." : "Submit Request"}
      </button>
    </form>
  );
}
