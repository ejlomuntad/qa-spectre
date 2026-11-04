TEST PLAN	Orders API (example)
Sources	docs/orders-prd.md (v1.2), openapi.yaml
Project rules	No project rules found — generic defaults used
Generated	2026-11-03

Status	Test Scenario	Verification / Note	Source	Tags

Feature Map:
├── Endpoints
│   ├── POST /orders (create)
│   ├── GET /orders/{id}
│   ├── GET /orders (list, cursor pagination)
│   ├── POST /orders/{id}/pay
│   ├── POST /orders/{id}/cancel
│   └── POST /orders/{id}/refunds (support role only)
└── Order states
    ├── PENDING → PAID → REFUNDED
    └── PENDING → CANCELLED

AUTOMATED TESTS
	Existing API test suite	⬅️ Run first, before manual testing		
	Contract tests against openapi.yaml	⬅️ Run at the start and again when the feature is code complete		

HAPPY PATHS
Properties (openapi.yaml): Order.id, Order.status, Order.items, Order.total, Order.paidAt, Refund.amount
	Create order with one valid item	⬅️ 201, status=PENDING, total = price x quantity	PRD §2.1; openapi POST /orders	api smoke regression
	Get order by id	⬅️ 200, body matches the created order	openapi GET /orders/{id}	api smoke regression
	Pay a PENDING order	⬅️ 200, status=PAID, paidAt set	PRD §2.3	api smoke regression
	Cancel a PENDING order	⬅️ 200, status=CANCELLED	PRD §2.4	api smoke regression
	Full refund of a PAID order	⬅️ 201, Refund.amount = Order.total, order status=REFUNDED	PRD §2.5	api smoke regression

INPUT VALIDATION & BOUNDARIES
Properties (openapi.yaml): Error.code, Error.message, Error.details[].field
	quantity = 1 (min)	⬅️ 201	openapi OrderItem.quantity minimum: 1	api regression
	quantity = 100 (max)	⬅️ 201	openapi OrderItem.quantity maximum: 100	api regression
	quantity = 0	⬅️ 400, code=VALIDATION_ERROR, details[].field=items[0].quantity	openapi OrderItem.quantity	api regression
	quantity = 101	⬅️ 400, code=VALIDATION_ERROR	openapi OrderItem.quantity	api regression
	Empty items array	⬅️ 400, code=VALIDATION_ERROR	openapi CreateOrder.items minItems: 1	api regression

AUTH & PERMISSIONS
	No bearer token	⬅️ 401	openapi securitySchemes	api smoke regression
	Customer reads another customer's order	⬅️ 404 (not 403, so IDs don't leak)	PRD §5.2	api regression
	Customer calls the refund endpoint	⬅️ 403, only role=support may refund	PRD §5.3	api regression

STATE TRANSITIONS
	Pay a CANCELLED order	⬅️ 409, code=INVALID_STATE, status unchanged	PRD §2.3	api regression
	Cancel a PAID order	⬅️ 409, code=INVALID_STATE, status unchanged	PRD §2.4	api regression
	Refund a PENDING order	⬅️ 409, code=INVALID_STATE	PRD §2.5	api regression
	Pay an order that is already PAID	💡 PRD is silent — see Q1	PRD §2.3	api regression

BUSINESS RULES & LIMITS
Properties (openapi.yaml): Refund.amount, Order.paidAt
Properties (docs): Refund.reason
⚠️ Not in spec — Refund.reason is named in PRD §2.5 only. Confirm with engineer.
	Refund 30 days after payment	⬅️ 201 (window counted from paidAt — see Q2)	PRD §3.1	api regression
	Refund 31 days after payment	⬅️ 422, code=REFUND_WINDOW_EXPIRED	PRD §3.1	api regression
	Partial refunds that add up to more than the total	⬅️ 422, code=REFUND_EXCEEDS_TOTAL on the refund that crosses the total	PRD §3.2	api regression

IDEMPOTENCY & CONCURRENCY
	Repeat pay with the same Idempotency-Key	⬅️ same response both times, customer charged once	PRD §4.1; openapi header Idempotency-Key	api regression
	Same Idempotency-Key with a different body	⬅️ 422, code=IDEMPOTENCY_KEY_REUSED	openapi POST /orders/{id}/pay responses	api regression
	Pay and cancel the same PENDING order at the same time	⬅️ one succeeds, the other gets 409; final state matches the winner	PRD §4.2	api regression

PAGINATION & FILTERING
Properties (openapi.yaml): OrderList.items, OrderList.nextCursor
	GET /orders?limit=100 (max)	⬅️ 200, at most 100 items, nextCursor set when more exist	openapi GET /orders limit maximum: 100	api regression
	GET /orders?limit=101	⬅️ 400, code=VALIDATION_ERROR	openapi GET /orders limit	api regression
	GET /orders?status=PAID	⬅️ only PAID orders returned	openapi GET /orders status	api regression

ERROR HANDLING
	Unknown order id	⬅️ 404, body matches Error schema (code, message)	openapi components.schemas.Error	api regression
	Malformed JSON body	⬅️ 400, body matches Error schema, no stack trace in message	openapi components.schemas.Error	api regression

PERSISTENCE & RECOVERY
	Payment provider times out during pay	⬅️ order stays PENDING; retry with the same key succeeds once	PRD §4.3	api regression
	Read order after a service restart	⬅️ status, items and total unchanged	PRD §4.3	api regression

QUESTIONS FOR CLARIFICATION
	Q1: Paying an order that is already PAID — return the existing payment (200) or reject (409)?
	Context: PRD §2.3 covers PENDING and CANCELLED only.
	Options: (A) 200, same body (idempotent) | (B) 409 INVALID_STATE | (C) Other
	Q2: Does the 30-day refund window start at payment or at delivery?
	Context: PRD §3.1 says "within 30 days" with no start point.
	Options: (A) paidAt | (B) delivery date | (C) createdAt

NOT COVERED (check none of these need tests)
	PRD §6 Analytics events	💡 Not testable through the API — skipped	PRD §6	
	Rate limits (standard check)	💡 Docs and spec define no rate limits — skipped	standard-checks.yml	
	Backwards compatibility (standard check)	💡 New API, no earlier version — skipped	standard-checks.yml	
