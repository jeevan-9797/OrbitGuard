# Satellite Multi-Agent AI — Database War Room Documentation

Detailed production-grade database guide for the Satellite Multi-Agent AI System.

---

## 1. Database Mission
> **Create one reliable source of truth for satellites, telemetry, anomalies, incidents, agent decisions, recovery plans, safety validations, executions, and audit events.**

- **Database Stack**: PostgreSQL 14+ / Supabase
- **Design Philosophy**: Single PostgreSQL monolith. Avoid unnecessary microservices. Relational integrity with JSONB flexibility for agent outputs and append-only audit tracking.

---

## 2. Directory Structure

```
database/
├── migrations/
│   ├── 001_initial_core_schema.sql         # 11 Core operational tables
│   ├── 002_knowledge_and_config.sql       # 6 Knowledge & configuration tables
│   ├── 003_indexes_and_constraints.sql     # Telemetry & workflow indexes
│   └── 004_context_and_contracts.sql       # Pre-aggregated build_incident_context() function
├── seed/
│   ├── knowledge.sql                       # Flight modes, actions, rules, runbooks
│   ├── satellites.sql                      # Fleet constellations and subsystems
│   ├── telemetry.sql                       # Baselines & initial telemetry streams
│   └── scenarios.sql                       # Scenario A & Scenario B demonstration data
├── connection.py                           # Pool management, health check & permission checks
├── migrate.py                              # Migration tracking & execution CLI
├── seed.py                                 # Seed sequence runner
├── reset.py                                # Demo reset runner
├── schema.sql                              # Consolidated master schema
├── reset_demo.sql                          # Callable demo reset script & function
├── verify_setup.py                         # Phase 2 setup verification suite
└── README.md                               # This guide
```

---

## 3. Configuration & Environment Variables

### Setup `.env`
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

### Required Environment Variables
| Variable | Description | Example |
| :--- | :--- | :--- |
| `DATABASE_URL` | Complete PostgreSQL / Supabase connection URL. | `postgresql://postgres:password@localhost:5432/satellite_ai?sslmode=prefer` |
| `SUPABASE_URL` | *(Optional)* Supabase API URL if using Supabase client. | `https://your-project.supabase.co` |
| `SUPABASE_ANON_KEY` | *(Optional)* Public anonymous JWT key for frontend. | `eyJhbGciOi...` |
| `SUPABASE_SERVICE_ROLE_KEY` | *(Optional)* Elevated service key for backend/AI. | `eyJhbGciOi...` |
| `DB_POOL_MIN_CONNECTIONS` | Minimum connections in pool (default: `2`). | `2` |
| `DB_POOL_MAX_CONNECTIONS` | Maximum connections in pool (default: `10`). | `10` |

> [!NOTE]
> Never commit `.env` or any file containing passwords or private keys. The `.gitignore` file is configured to strictly exclude `.env`, `.env.*.local`, `*.key`, and `*.pem`.

---

## 4. Running Migrations

The migration system tracks applied versions inside the `schema_migrations` table with SHA256 checksums.

```bash
# Check current migration status:
python -m database.migrate status

# Preview pending migrations without applying:
python -m database.migrate dry-run

# Apply all pending migrations sequentially:
python -m database.migrate up
```

Alternatively, if using `psql` or the Supabase SQL Editor, you can execute the migration files sequentially or execute `database/schema.sql` directly:
```bash
psql $DATABASE_URL -f database/schema.sql
```

---

## 5. Seeding the Database

Seed files are executed in strict dependency order:
1. `knowledge.sql` (modes, action catalog, safety rules, runbooks, config)
2. `satellites.sql` (6 constellation satellites, 36 subsystems)
3. `telemetry.sql` (mode baselines, normal telemetry windows)
4. `scenarios.sql` (Scenario A: Battery Overheat & Scenario B: Reaction Wheel)

```bash
# Run the automated seed runner:
python -m database.seed
```

---

## 6. Resetting the Demo Database

For live judge demonstrations and continuous testing, the database can be wiped of operational incident history and restored to a nominal fleet baseline in `< 100ms`:

```bash
# Via Python CLI runner:
python -m database.reset
```

Or via direct SQL / Supabase RPC:
```sql
SELECT reset_demo();
```

---

## 7. Verifying the Database Setup

Run the Phase 2 setup verification suite to validate connection loading, permission check logic, migration tracking, and secrets auditing:

```bash
python -m database.verify_setup
```
