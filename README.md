# Smart Parking Lot - Backend System

A concurrency-safe backend for a 2-floor smart parking lot. Handles vehicle check-in/out, spot allocation, and fee calculation with real-time availability.

Live Demo: `https://your-app.onrender.com` | API Docs: `/docs` | Dashboard: `/`

### Features
- **Auto Allocation** - Assigns free spot by vehicle size (Motorcycle→Small, Car→Medium, Bus→Large) using Strategy Pattern
- **Check-In / Check-Out** with entry/exit time tracking
- **Fee Calculation** - Hourly billing with 5-min grace period, `Decimal` for money, `ceil` to next hour. Ex: 2h30 = 3 hours
- **Real-time Availability** - No `occupied` column - free = spots NOT IN open sessions
- **Concurrency Safe** - `SELECT ... FOR UPDATE` + Partial Unique Index `WHERE exit_time IS NULL` prevents double booking
- **Live Dashboard** - Floor grid, parked now, recent exits, revenue

### Tech Stack
Python, FastAPI, SQLAlchemy 2.0, PostgreSQL 16, Docker, Pytest, Pydantic

### Architecture



**Layering:** `domain` knows nothing about DB/API - testable without Postgres. `services` owns transactions. `api` only translates HTTP.

### Database Schema
- `parking_spots(id, floor, number, spot_type)` + `Unique(floor, number)` - 24 spots [2 floors x (4 Small, 6 Medium, 2 Large)]
- `hourly_rates(vehicle_type PK, hourly_rate)` - 10/20/50
- `vehicles(id, registration_number UNIQUE, vehicle_type)`
- `parking_sessions(id, vehicle_id FK, spot_id FK, entry_time, exit_time NULL, fee_amount)` + `Partial Index UNIQUE(spot_id) WHERE exit_time IS NULL` and `UNIQUE(vehicle_id) WHERE exit_time IS NULL`

### API
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/check-in` | `{"registration_number": "KA01AB1234", "vehicle_type": "car"}` -> 201 |
| `POST` | `/check-out` | `{"registration_number": "KA01AB1234"}` -> fee |
| `GET` | `/availability` | free count per spot_type |
| `GET` | `/status` | full state for dashboard |

### Fee Logic
`billable_hours = ceil((stay - 5 min) / 1 hour)` if >0 else 0. `fee = rate * billable_hours`

| Stay | Charged |
|---|---|
| 0-5 min | 0 |
| 5m 1s | 1 hour |
| 1h05 | 1 hour |
| 1h05 1s | 2 hours |

### Concurrency
Problem: Two cars read free spots at same time -> both get spot 12.
Fix: `with_for_update()` locks free rows + `IntegrityError` catch + DB partial unique index as final guardrail. Proven with `ThreadPoolExecutor(10)` trying to park 10 buses into 4 spots -> only 4 succeed, no duplicates.

### Run Locally


### Tests


### Decisions Log
- **Floor as column not table:** Only 2 floors, no per-floor data. UniqueConstraint prevents duplicates.
- **Enum as text:** `native_enum=False` avoids Postgres `ALTER TYPE` migrations.
- **Fee on session:** Stored at exit so price changes don\'t rewrite history.
- **No occupied flag:** Single source of truth = open session exists.

### Future Work
- Alembic migrations, separate test DB, auth, payment gateway, per-floor pricing