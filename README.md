# Order-to-Audit ERP — Sri Lakshmi Snacks (Tiruchirappalli)

An enterprise-grade, transaction-driven ERP system tailored for **Sri Lakshmi Snacks**, a regional snack manufacturer (murukku, mixture, chips, sweets) based in Thuvakudi Industrial Estate, Tiruchirappalli, Tamil Nadu.

The core philosophy of this system is **"Enter Once, Audit Everywhere"**: every transaction is entered exactly once at its physical point of occurrence and immutably ripples across inventory, production, product costing, GST compliance, and accounting registers.

---

## 1. Architectural Rules & Guarantees

The system strictly enforces the following rules across database constraints, service domain layers, and API dependencies:

1. **Single Append-Only Stock Ledger as Source of Truth**:
   - The `stock_ledger` table is strictly append-only (no updates, no deletes).
   - Every movement records item type (`raw_material` / `packaging` / `finished_goods`), location type (`raw` / `packaging` / `finished`), quantity in base unit, movement direction (`IN` / `OUT`), source document type (`PURCHASE`, `PRODUCTION_RUN`, `DISPATCH`, `CREDIT_NOTE`), source document ID, batch number, operator user ID, and timestamp.
   - **Current inventory is always calculated dynamically using SQL `SUM()`**. Balance columns are never stored or overwritten.
2. **Zero Float Policy & Base Units**:
   - All physical quantities are stored in **base units** (`g` for weight, `ml` for volume, `piece` for discrete counts) using arbitrary-precision `Decimal`. Conversion to commercial units (`kg`, `litre`, `packet`, `carton`) occurs exclusively at user input and display boundaries.
   - All monetary figures are stored as **integer paise** (`BIGINT`). Unit costs in the ledger support fractional paise via `Numeric(14, 4)` for exact Weighted Average Cost (WAC) calculations. Floating-point numbers are strictly forbidden.
3. **Immutability of Invoices & Credit Notes**:
   - Once posted, an invoice cannot be updated or deleted.
   - Any correction or cancellation is executed strictly through an offsetting **Credit Note**, recording reason, invoice reference, and atomic ledger `IN` reversal upon receipt.
   - Invoice numbers follow the Indian financial year sequence: `TN/2026-27/0001`.
4. **Append-Only Audit Trail**:
   - Critical domain modifications (invoices, production runs) automatically write immutable entries to `audit_log` capturing user ID, timestamp, entity type, entity ID, action (`CREATE`, `UPDATE`, `CANCEL`), and full before/after JSON state snapshots.
5. **Backend Role-Based Access Control (RBAC)**:
   - Enforced cryptographically via JWT claims and FastAPI dependencies (`require_roles(...)`), not merely by hiding UI buttons.
   - Distinct roles: `salesman`, `admin`, `production`, `accountant` (read-only audit), `owner` (executive dashboard).
6. **Dispatch-Driven Inventory Movements**:
   - Placing or approving an order does **not** deduct physical inventory.
   - Stock `OUT` ledger movements occur strictly when the order is physically dispatched with vehicle details recorded.

---

## 2. Technology Stack & Rationale

| Layer | Technology | Selection Rationale |
|---|---|---|
| **Backend Framework** | Python 3.10+ / FastAPI | High throughput asynchronous API framework with automatic OpenAPI documentation and native Pydantic schema validation. |
| **ORM & Migrations** | SQLAlchemy 2.0 / Alembic | Strict relational mapping, transactional DDL migrations, and SQL expression builder preventing SQL injection. |
| **Primary Database** | PostgreSQL 16 | ACID-compliant relational storage with robust `BIGINT`, `NUMERIC`, and JSONB support. SQLite memory/file fallback supported for rapid zero-dependency local testing. |
| **Testing Harness** | pytest / pytest-asyncio / Starlette TestClient | Automated test suite validating unit conversions, ledger calculations, GST splits, WAC costing, and the 8-step industrial benchmark. |
| **Document Generation**| ReportLab | High-precision commercial PDF generation for GST Tax Invoices formatted with Tamil Nadu supplier headers, HSN codes, and CGST/SGST/IGST tax breakdowns. |
| **Spreadsheet Exports**| openpyxl / csv | Native streaming CSV and styled `.xlsx` workbook export with header styling and number formatting for accountant registers. |
| **Frontend Framework** | React 18 / TypeScript / Vite | Mobile-first Progressive Web App (PWA) delivering sub-second load times and offline service worker capability. |
| **Styling & Theming** | Tailwind CSS / CSS Variables | High-contrast factory day mode for outdoor sunlight and night mode, using warm South Indian brand tones (turmeric yellow `#D97706`, chilli red `#DC2626`, banana-leaf green `#15803D`, cream `#FFFDF7`). No generic AI blues/purples. |
| **Internationalization**| react-i18next | Seamless language toggle between English and authentic Tamil (`தமிழ்`) with typography configured for **Noto Sans Tamil**. Invoices remain in English per GST rules. |
| **Field Automation** | Web Speech API & IndexedDB | Hands-free voice ordering for field salesmen with mandatory review confirmation dialogs, and offline order queueing with background network sync. |
| **Containerization** | Docker Compose | Single-command multi-service deployment orchestrating PostgreSQL database, automated Alembic migrations, database seeding, backend API, and frontend PWA. |

---

## 3. Quickstart & Deployment

### Option A: Docker Compose (Recommended)

To run the entire system (PostgreSQL 16, FastAPI backend, automated seed script, and React PWA frontend):

```bash
docker compose up --build
```

- **Frontend ERP Web App**: [http://localhost:3000](http://localhost:3000)
- **Backend Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check Endpoint**: [http://localhost:8000/health](http://localhost:8000/health)

### Option B: Local Development Setup

#### 1. Backend Setup
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Run migrations and seed data
python -m app.seeds.seed

# Start FastAPI server on port 8000
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Frontend Setup
```powershell
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

#### 3. Running Automated Tests
```powershell
$env:PYTHONPATH='backend'
.\backend\.venv\Scripts\pytest.exe -v backend\tests
```

---

## 4. Default Seed Accounts & Role Permissions

The database seed script automatically provisions test accounts for each operational role:

| Username | Password | Role | Access Scope & Responsibilities |
|---|---|---|---|
| `owner` | `owner123` | `owner` | Executive dashboard, live inventory, variance alerts, unit margins, customer debt ageing. |
| `admin` | `admin123` | `admin` | Order approvals, GST invoice generation, dispatch recordings, payment collections, full view. |
| `salesman_a` | `sales123` | `salesman` | Mobile-first ordering, voice dictation, live stock checks, offline queue, submitted orders. |
| `salesman_b` | `sales123` | `salesman` | Mobile-first ordering, interstate client servicing, shortage alerts. |
| `production` | `prod123` | `production` | BOM recipe pre-fills, batch execution, actual issue tracking, variance analysis, batch planning. |
| `accountant` | `acct123` | `accountant` | Read-only audit access: Sales Register, GSTR-1/3B Summary, Purchase Register, Ageing, CSV/Excel. |

---

## 5. Industrial Benchmark Scenario & Verification

The system includes an automated, end-to-end benchmark test (`backend/tests/test_benchmark_full.py`) verifying the complete operational cycle:

### Standard BOM Specification (Kai Murukku 200 g)
- **1 Batch Standard Yield**: 200 packets (40,000 g finished goods).
- **Raw Materials**: Raw Rice Flour 40 kg, Refined Sunflower Oil 10 L, Salt & Spices 1.2 kg.
- **Packaging Materials**: 200 g Printed Pouches 200 pcs, 20-Pack Master Cartons 10 pcs (1 carton holds 20 packets).
- **Master Rates**: Opening Flour Rs 42/kg; Sunflower Oil Rs 140/L; Spice Mix Rs 200/kg; Pouch Rs 2.50/pc; Carton Rs 15/pc; Selling Price Rs 50/pkt + 5% GST. Factory located in Tamil Nadu (`TN-33`).

### Benchmark Step-by-Step Execution & Results

| Step | Operation Description | Input Values | Result / Output Verification | Status |
|---|---|---|---|---|
| **0** | Opening Stock Seed | Flour 100 kg, Oil 30 L, Spice 5 kg, Pouches 500 pcs, Cartons 30 pcs, Murukku 50 pkts. | Ledger balances verified via dynamic SQL `SUM()`. | Verified |
| **1** | Raw Material Purchase | Inward purchase of 60 kg Flour @ Rs 45/kg (Rs 2,700). | Stock: 100 kg + 60 kg = **160 kg**.<br>Flour WAC: $\frac{(100 \times 42) + (60 \times 45)}{160} = \mathbf{43.125\text{ Rs/kg}}$ (4.3125 paise/g). | Verified |
| **2 & 3** | Production Run Execution | User issues 40 kg Flour, 10.5 L Oil, 1.2 kg Spice Mix.<br>Actual output: 188 packets, 6 damaged pouches, 9 cartons used. | - Flour stock: $160 - 40 = \mathbf{120\text{ kg}}$.<br>- Oil stock: $30 - 10.5 = \mathbf{19.5\text{ L}}$.<br>- Pouches stock: $500 - (188 + 6) = \mathbf{306\text{ pcs}}$.<br>- FG Murukku stock: $50 + 188 = \mathbf{238\text{ pkts}}$.<br>- **Yield Variance**: 188 vs 200 std = $\mathbf{-6.00\%}$ (Flagged, $> 3\%$).<br>- **Oil Usage Variance**: 10.5 vs 10 std = $\mathbf{+5.00\%}$ (Flagged, $+0.5\text{ L}$ extra, $\approx \text{Rs } 70$). | Verified |
| **4** | Intra-state Sales Order | Salesman A books 150 pkts for Retailer A (Tamil Nadu, State 33) @ Rs 50/pkt. | Order `#1` created. Stock check confirms 238 pkts available (sufficient). | Verified |
| **5** | Admin Approval, GST Invoice & Dispatch | Admin approves Order `#1`, generates Invoice `TN/2026-27/0001`, records dispatch (`TN-45-AT-1234`). | - Base taxable: $150 \times 50 = \text{Rs } 7,500$.<br>- Intra-state Tax: **CGST 2.5%** (Rs 187.50) + **SGST 2.5%** (Rs 187.50).<br>- Total Invoice Amount: **Rs 7,875.00**.<br>- Stock `OUT` posted at dispatch: $238 - 150 = \mathbf{88\text{ pkts}}$ remaining. | Verified |
| **6** | Interstate Sales Order & Shortage Flag | Salesman B books 120 pkts for Distributor B (Karnataka, State 29). | Stock check flags shortage: Only **88 packets** in stock, **short by 32 packets**.<br>If invoiced, IGST 5% (Rs 300) applies. | Verified |
| **7** | Payment Collection | Customer Retailer A pays Rs 4,000 via NEFT/UPI. | Customer Outstanding Dues: $7,875 - 4,000 = \mathbf{\text{Rs } 3,875.00}$. | Verified |
| **8** | Overhead Allocation & Costing | Allocate Labour Rs 1,200 and Gas/Power Rs 600 to Run `#1`. | - Absorbed Overheads: Rs 1,800.<br>- Total Run Cost: Material Rs 4,054.40 + Overheads Rs 1,800 = **Rs 5,854.40**.<br>- **Cost Per Packet**: $\frac{5854.40}{188} = \mathbf{\text{Rs } 31.14}$.<br>- **Gross Margin**: Rs $50.00 - 31.14 = \mathbf{\text{Rs } 18.86}$ (**37.7% margin**). | Verified |

---

## 6. Features by Role & Tier

### 1. Salesman Workspace (Mobile-First)
- **High-Contrast Touch UI**: Minimum 48px touch targets for sunlight readability in retail bazaars.
- **Voice Order Entry**: Speak in English or Tamil (*"Retailer A, Kai Murukku 150 packets"*); parsed by speech grammar with a mandatory verification modal before submission.
- **Real-Time Stock Availability**: Displays live stock status and generates explicit shortage warnings (*"Only 88 packets in stock. Short by 32"*).
- **Offline Order Queue**: Stores orders in browser IndexedDB when offline, auto-syncing seamlessly upon network restoration.
- **Order Tracking**: Real-time order status tracking (`submitted`, `approved`, `invoiced`, `dispatched`).

### 2. Factory Admin Workspace (Desktop)
- **Order Queue & Verification**: Review incoming orders with customer GSTIN and stock verification.
- **One-Click GST Invoice**: Creates immutable FY-numbered tax invoices (`TN/2026-27/0001`).
- **Commercial PDF Download**: Formatted A4 Tax Invoice PDF using ReportLab with Tamil Nadu registered office header, HSN codes, and tax breakout.
- **Direct WhatsApp Sharing**: Generates pre-formatted `https://wa.me/?text=...` dispatch notification links with invoice number, transporter vehicle, and payment details.
- **Dispatch Engine**: Records vehicle number, driver details, and atomically posts ledger `OUT` transactions.
- **Payment Collection**: Records partial or full payment receipts, adjusting customer outstanding balance.

### 3. Production Workspace
- **Standard BOM Pre-fill**: Select product and batch count; auto-populates theoretical consumption for all ingredients and packaging.
- **Execution & Variance Capture**: Enter actual good output, damaged pouches, and actual ingredient weights.
- **Dual Variance Alerts**: Visual flags when $|\text{variance}| > 3\%$, displaying both physical deviation (kg/L) and monetary rupee impact based on current WAC.
- **Batch Planning from Orders**: Automatically scans approved pending demand and calculates: *"To fulfil approved orders, make N batches"*, listing raw material sufficiency.

### 4. Accountant Workspace (Read-Only)
- **Dense Practical Registers**:
  - **Sales Register**: Invoice number, date, customer, GSTIN, taxable amount, CGST, SGST, IGST, total.
  - **GST Summary (GSTR-1 / 3B)**: Outward taxable supplies categorized by B2B vs Interstate, tax collected by component.
  - **Purchase Register**: Vendor invoices, inward quantities, and purchase amounts.
  - **Customer Outstanding & Ageing**: 0–30 days, 31–60 days, 61–90 days, 90+ days overdue analysis.
- **Export Engine**: One-click download of all registers in clean CSV or formatted openpyxl Excel workbooks.

### 5. Owner Dashboard
- **Executive KPI Cards**: Today's order bookings, finished goods inventory, total market receivables.
- **Variance Warning Center**: Immediate visibility into batch yield discrepancies and ingredient losses.
- **Costing & Profitability**: Real-time Cost per Packet and Gross Margin tracking.
- **Interactive Stock Drill-Down**: Click any stock balance to open the **Immutable Stock Ledger Modal**, displaying every historical IN/OUT movement, source document ID, operator user, and valuation.

---

## 7. Assumptions & Known Gaps

1. **Production Scrap Recycling**: Dough scraps and reworkable trims in sweet/murukku frying are assumed to be reused in subsequent shifts without separate ledger re-entry.
2. **E-Way Bill Integration**: E-Way bill numbers and transport distance are supported as metadata fields, but direct NIC API auto-generation is not included in this solo prototype.
3. **Multi-Warehouse Storage**: Designed for single-factory locations (Thuvakudi Industrial Estate) with three segregated internal location types (`raw`, `packaging`, `finished`). Inter-depot stock transfers are outside the current scope.
