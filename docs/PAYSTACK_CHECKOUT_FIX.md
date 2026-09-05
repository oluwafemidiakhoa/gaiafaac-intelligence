# Paystack checkout compatibility fix

This release normalizes the Paystack server request to the documented transaction-initialize contract:

- secret key is trimmed before use;
- `amount` is sent as a string in kobo;
- `metadata` is sent as a stringified JSON object;
- a normal User-Agent is included;
- provider HTTP failures are logged with sanitized status/message only (never credentials).

The same request contract is used by subscription and one-time purchase checkout.
