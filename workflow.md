# ChemDesignAI — Complete Workflow & Setup Guide

## Step-by-Step Development & Deployment Workflow

---

## PHASE 1 — Environment Setup

### 1.1 Install Prerequisites
```
Python 3.10+   → https://python.org/downloads
MySQL 8.0+     → https://dev.mysql.com/downloads
Git            → https://git-scm.com
```

### 1.2 Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate         # Windows
source venv/bin/activate      # Linux/Mac
pip install -r requirements.txt
```

### 1.3 Configure .env
Copy `.env.example` → `.env` and fill in:
```
SECRET_KEY=<random 32+ char string>
DATABASE_URL=mysql+pymysql://root:<password>@localhost/chem_design_db
GROQ_API_KEY=gsk_<your groq key>
```

Get a free Groq API key → https://console.groq.com

---

## PHASE 2 — Database Initialisation

```bash
# Create MySQL database
mysql -u root -p -e "CREATE DATABASE chem_design_db CHARACTER SET utf8mb4;"

# Run Flask-Migrate
flask db init
flask db migrate -m "Initial schema"
flask db upgrade

# Seed demo data
flask seed-db
```

After seeding, you will have:
- **admin** / `Admin@1234` (administrator role)
- **engineer1** / `Engineer@1234` (user role with sample designs)

---

## PHASE 3 — Running the Application

```bash
python run.py
# Opens at http://localhost:5000
```

Or with Flask CLI:
```bash
set FLASK_APP=run.py     # Windows
export FLASK_APP=run.py  # Linux/Mac
flask run --debug
```

---

## PHASE 4 — Calculation Workflow

### How a design calculation works:

```
User Input Form
    │
    ▼
app/routes/equipment.py (design_form)
    │  validate_equipment_inputs()
    ▼
app/calculations/<type>.py
    │  calculate_<type>(inputs)
    │  ─ returns dict with:
    │    - all numeric results
    │    - calculation_steps []
    │    - safety_notes []
    │    - errors []
    │    - cost estimates
    ▼
EquipmentDesign model saved to MySQL
    │
    ▼
Templates rendered with results
    │
    ├── Accordion of steps
    ├── Key metrics cards
    ├── Chart.js charts
    ├── Safety warnings
    └── AI analysis buttons
```

---

## PHASE 5 — AI Integration Workflow

```
User clicks "AI Optimize" or sends chat
    │
    ▼
JavaScript → POST /api/v1/chat  (or /optimize, /safety)
    │
    ▼
app/routes/api.py
    │
    ▼
app/ai/groq_client.py → GroqAIClient.suggest_optimization()
    │  Builds structured prompt with:
    │  - equipment type context
    │  - current design inputs
    │  - calculation results
    │  - engineering role instruction
    ▼
Groq API (Llama-3.3-70b-versatile)
    │
    ▼
Response saved to ChatHistory model
    │
    ▼
JSON response → JavaScript → DOM update
```

---

## PHASE 6 — 3D Visualization Workflow

```
Equipment results loaded into template
    │
    ▼
JavaScript: initVisualizer('viz-canvas', eq_type, { diameter, length })
    │
    ▼
app/static/js/visualizer.js
    │  Three.js scene:
    │  ├── Perspective camera
    │  ├── Directional + ambient + point lights
    │  ├── Grid floor
    │  ├── buildEquipmentModel(type, dims)
    │  │    ├── Unique geometry per equipment
    │  │    ├── Metal PhongMaterial
    │  │    ├── Edge wireframe overlay
    │  │    └── Nozzle attachments
    │  ├── Mouse/touch drag → orbit rotation
    │  ├── Scroll wheel → zoom
    │  └── requestAnimationFrame loop
    ▼
Interactive 3D model in canvas
```

---

## PHASE 7 — PDF Report Generation Workflow

```
User clicks "PDF Report"
    │
    ▼
GET /reports/generate/<design_id>
    │
    ▼
app/reports/pdf_generator.py → generate_pdf_report(design, app)
    │
    ├── Page setup (A4, margins)
    ├── Custom header/footer (every page)
    ├── Cover section (meta table)
    ├── Page 1: Design Inputs table
    ├── Page 2: Calculation Steps (step-by-step)
    ├── Page 3: Results Summary table
    ├── Cost Estimation section
    ├── Safety Recommendations (red)
    ├── AI Suggestions (if available)
    └── Disclaimer
    │
    ▼
PDF saved to app/static/reports/
    │
    ▼
Flask send_file() → browser download
```

---

## PHASE 8 — API Reference

### Authentication
All API endpoints require login (session cookie or JWT).

### Calculate Equipment
```http
POST /api/v1/calculate/heat_exchanger
Content-Type: application/json
X-CSRFToken: <token>

{
  "hot_inlet_temp": 150, "hot_outlet_temp": 80,
  "cold_inlet_temp": 25, "cold_outlet_temp": 65,
  "hot_flow_rate": 2.5, "cold_flow_rate": 3.0,
  "U_overall": 500, "tube_od": 0.019, "tube_id": 0.016,
  "tube_length": 4.0, "n_passes": 1, "material": "Carbon Steel"
}

Response 200:
{ "success": true, "design_id": 42, "results": { ... } }
```

### AI Chat
```http
POST /api/v1/chat
{ "message": "Explain LMTD and why it's used", "context": "heat_exchanger" }

Response:
{ "success": true, "response": "LMTD stands for...", "tokens_used": 210 }
```

### Unit Conversion
```http
POST /api/v1/convert
{ "category": "temperature", "conversion": "C_to_K", "value": 25 }

Response:
{ "success": true, "result": 298.15, "conversion": "C_to_K" }
```

Available categories & conversions:
```
temperature: C_to_K, K_to_C, C_to_F, F_to_C
pressure:    kPa_to_bar, bar_to_kPa, kPa_to_psi, psi_to_kPa, atm_to_kPa, kPa_to_atm
flow:        m3h_to_ls, ls_to_m3h, kgh_to_kgs, kgs_to_kgh
length:      m_to_ft, ft_to_m, m_to_in, in_to_m
```

---

## PHASE 9 — Security Configuration

| Feature | Implementation |
|---------|---------------|
| Password Hashing | Werkzeug `generate_password_hash` (scrypt) |
| CSRF Protection | Flask-WTF on all forms & API headers |
| Rate Limiting | Flask-Limiter (30/min calculations, 20/min AI) |
| Session Security | Secure, HttpOnly, SameSite cookies |
| SQL Injection | SQLAlchemy ORM (parameterised queries) |
| Admin Authorization | `@admin_required` decorator |
| XSS Prevention | Jinja2 auto-escaping |

---

## PHASE 10 — Production Deployment

### Gunicorn + Nginx (Linux)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 "run:app"
```

### Environment Variables (Production)
```env
FLASK_ENV=production
SECRET_KEY=<very-long-random-string>
DATABASE_URL=mysql+pymysql://user:pass@localhost/chem_design_prod
GROQ_API_KEY=gsk_...
```

### Database Backups
```bash
mysqldump chem_design_db > backup_$(date +%Y%m%d).sql
```

---

## Common Commands Reference

```bash
# Start dev server
python run.py

# Database migrations
flask db migrate -m "description"
flask db upgrade

# Seed demo data
flask seed-db

# List all routes
flask routes

# Open Flask shell
flask shell

# Run with Gunicorn (production)
gunicorn -w 4 "run:app"
```

---

*ChemDesignAI — AI-Based Chemical Process Equipment Design Platform*
