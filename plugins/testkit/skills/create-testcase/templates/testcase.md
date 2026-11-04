# Checkout Service Test Cases (BDD)

**Project:** checkout-service · **Format:** BDD (Given / When / Then) · **Generated:** 2026-06-03  
**Requirements:** `~/Desktop/Testkit/requirements/checkout-service/requirements-inventory.md` (built 2026-06-03)  
**Sources:** checkout-prd.docx, user-stories.md, payments-api.yaml, discount-rules.xlsx

| Metric | Count |
|--------|-------|
| Categories | 4 |
| Positive [P] | 6 |
| Negative [N] | 5 |
| Edge Case [E] | 5 |
| **Total Test Cases** | **16** |
| Clarification Questions | 2 |

| Type | Description |
|------|-------------|
| [P] Positive | Happy path -- expected behavior |
| [N] Negative | Invalid inputs, error handling |
| [E] Edge Case | Boundary conditions, limits |

---

## Feature Overview

```
Features:
├── Cart
│   ├── Add / remove items
│   └── Quantity limits (1-10 per item)
├── Discount Codes
│   ├── Percentage codes
│   ├── One code per order
│   └── Minimum order value
├── Payment
│   ├── Card payment
│   └── Duplicate payment protection
└── Order Confirmation
    ├── Confirmation page and email
    └── Order locked after payment
```

---

## Clarification Questions

| # | Category | Question | Options | Affected Test Cases |
|---|----------|----------|---------|---------------------|
| 1 | Inconsistencies | The user story caps quantity at 10, but the API doc allows up to 99. Which limit applies? | (A) 10 everywhere (B) 10 in the UI, 99 in the API (C) 99 everywhere | TC-002 Quantity 0 rejected<br>TC-003 Quantity 11 rejected by API |
| 2 | Ambiguities | The PRD says codes apply to "orders over 50.00". Does exactly 50.00 qualify? | (A) Yes, 50.00 and above (B) No, above 50.00 only | TC-006 Code at minimum order value |
