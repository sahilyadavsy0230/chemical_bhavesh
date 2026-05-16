# ChemDesignAI

## AI-Based Web Platform for Automated Design of Chemical Process Equipment

[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-green?logo=flask)](https://flask.palletsprojects.com)
[![Groq](https://img.shields.io/badge/AI-Groq%20Llama%203-orange?logo=ai)](https://groq.com)
[![Bootstrap](https://img.shields.io/badge/UI-Bootstrap%205-purple?logo=bootstrap)](https://getbootstrap.com)
[![Three.js](https://img.shields.io/badge/3D-Three.js-black?logo=three.js)](https://threejs.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 📋 Project Overview

**ChemDesignAI** is a full-stack, AI-powered web platform for automated design of chemical process equipment. Built as a final-year chemical engineering project, it provides:

- **Engineering-grade calculations** using real industry equations (Kern, Treybal, Levenspiel, McCabe-Smith)
- **AI assistant** powered by Groq Llama 3.3-70b — explains formulas, optimizes designs, analyses safety
- **Interactive 3D visualization** using Three.js with rotatable, zoomable equipment models
- **Professional PDF reports** generated with ReportLab
- **Full user authentication**, project management, and design history

---

## ✨ Features

### Chemical Equipment Modules
| Equipment | Methods Used |
|-----------|-------------|
| **Heat Exchanger** | LMTD, F-correction, NTU-effectiveness, Dittus-Boelter, Darcy-Weisbach |
| **Reactor (CSTR/PFR)** | Levenspiel design equations, Damköhler number, Arrhenius |
| **Distillation Column** | McCabe-Thiele, Fenske, Gilliland, Kirkbride, Fair flooding |
| **Evaporator** | Multi-effect mass balance, steam economy, Antoine equation |
| **Absorber** | NTU-HTU, Underwood operating line, GPDC flooding |
| **Pump** | Colebrook-White friction, TDH, NPSH, Swamee-Jain |
| **Compressor** | Isentropic work, Arrhenius temperature rise, impeller sizing |

### AI Features (Groq Llama 3)
- 💬 **AI Chatbot Assistant** — engineering Q&A with conversation history
- 🔧 **Design Optimization** — temperature, pressure, flow rate suggestions
- 📐 **Formula Explanation** — detailed derivations and worked examples
- 🛡️ **Safety Analysis** — ASME/API/OSHA recommendations
- 🪛 **Input Debugging** — fixes invalid inputs with explanations
- 🔩 **Material Selection** — ASTM-grade recommendations

### Platform Features
- 🔐 User authentication & role management (admin/user)
- 📁 Project organisation & design history
- 📄 Downloadable PDF reports with full calculations
- 📊 Chart.js dashboards (efficiency, cost, activity)
- 🌓 Dark/light mode toggle
- 🔄 Unit converter (SI ↔ Imperial)
- 🏗️ REST API for external integrations
- 🔒 CSRF protection, password hashing, rate limiting

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10+, Flask 3.0, Flask-SQLAlchemy, Flask-Migrate |
| Auth | Flask-Login, Werkzeug, PyJWT |
| Database | MySQL (PyMySQL driver) |
| AI | Groq API (Llama-3.3-70b-versatile) |
| PDF | ReportLab |
| Frontend | Bootstrap 5.3, Bootstrap Icons, Chart.js, Three.js |
| Security | Flask-WTF (CSRF), Flask-Limiter |
| Fonts | Google Fonts — Inter, JetBrains Mono |

---

## 🚀 Installation

### Prerequisites
- Python 3.10+
- MySQL 8.0+
- Groq API key (free at https://console.groq.com)

### 1. Clone the Repository
```bash
git clone https://github.com/yourname/chemdesignai.git
cd chemdesignai
```

### 2. Create Virtual Environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
cp .env.example .env
# Edit .env with your MySQL credentials and Groq API key
```

### 5. Create MySQL Database
```sql
CREATE DATABASE chem_design_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 6. Initialise Database
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
flask seed-db        # Insert demo data (admin + sample designs)
```

### 7. Run the Application
```bash
python run.py
```

Open your browser at: **http://localhost:5000**

### Demo Credentials
| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `Admin@1234` |
| Engineer | `engineer1` | `Engineer@1234` |

---

## 📖 Usage

1. **Register** or log in with demo credentials
2. Select an **Equipment Module** from the dashboard
3. Enter design **inputs** (defaults pre-filled with realistic values)
4. Click **Calculate Design** to run engineering equations
5. View **step-by-step results** in the accordion panel
6. Click **AI Optimize** for Llama 3 optimization suggestions
7. Click **Safety AI** for industrial safety analysis
8. Click **PDF Report** to download a professional report
9. Use the **AI Chat** sidebar for any engineering questions
10. Browse **Design History** to compare past designs

---

## 📁 Folder Structure

```
chemdesignai/
├── run.py                    # Application entry point
├── config.py                 # Environment configurations
├── requirements.txt          # Python dependencies
├── .env.example              # Environment template
├── .gitignore
├── README.md
├── workflow.md               # Detailed workflow documentation
│
└── app/
    ├── __init__.py           # Application factory
    ├── routes/               # Flask Blueprints
    │   ├── auth.py           # Login, register, logout
    │   ├── dashboard.py      # Dashboard + history
    │   ├── equipment.py      # Equipment design forms & results
    │   ├── api.py            # REST API endpoints
    │   ├── reports.py        # PDF generation
    │   ├── profile.py        # User profile & projects
    │   └── admin.py          # Admin panel
    ├── models/               # SQLAlchemy ORM models
    │   ├── user.py
    │   ├── project.py
    │   ├── equipment.py
    │   └── chat.py
    ├── calculations/         # Engineering calculation engines
    │   ├── heat_exchanger.py
    │   ├── reactor.py
    │   ├── distillation.py
    │   ├── evaporator.py
    │   ├── absorber.py
    │   ├── pump.py
    │   └── compressor.py
    ├── ai/                   # Groq AI integration
    │   ├── groq_client.py
    │   └── prompts.py
    ├── reports/              # PDF generation
    │   └── pdf_generator.py
    ├── utils/                # Validators, seed data
    │   ├── validators.py
    │   └── seed_data.py
    ├── static/
    │   ├── css/main.css      # Complete dark/light theme
    │   ├── js/main.js        # Core JS (chat, theme, loader)
    │   ├── js/visualizer.js  # Three.js 3D equipment models
    │   ├── images/
    │   └── reports/          # Generated PDF files
    └── templates/
        ├── base.html         # Base layout with nav + chat
        ├── landing.html      # Public landing page
        ├── auth/             # login, register, change_password
        ├── dashboard/        # index, history
        ├── equipment/        # design_form, result_detail, compare
        ├── profile/          # index, edit, projects
        ├── admin/            # index, users, designs
        └── errors/           # 400, 403, 404, 429, 500
```

---

## 🔌 API Documentation

### Base URL: `/api/v1`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/calculate/<type>` | Run equipment calculation |
| `POST` | `/chat` | AI chatbot message |
| `POST` | `/optimize/<id>` | AI design optimization |
| `POST` | `/safety/<id>` | AI safety analysis |
| `POST` | `/explain-formula` | Formula explanation |
| `POST` | `/material-recommendation` | Material selection |
| `POST` | `/convert` | Unit conversion |
| `GET`  | `/designs` | List user designs |
| `GET`  | `/chat-history` | Chat history |
| `GET`  | `/stats` | Dashboard statistics |

---

## 🖼️ Screenshots

> *Place screenshots in `/docs/screenshots/` and update paths below.*

| Dashboard | Heat Exchanger Design | 3D Visualization |
|-----------|----------------------|------------------|
| ![Dashboard](docs/screenshots/dashboard.png) | ![HX Design](docs/screenshots/hx_design.png) | ![3D Model](docs/screenshots/3d_model.png) |

---

## 🔮 Future Improvements

- [ ] Multi-component distillation (shortcut methods)
- [ ] Process Flow Diagram (PFD) generation with SVG
- [ ] Pressure vessel wall thickness (ASME VIII)
- [ ] Economic evaluation (NPV, payback period)
- [ ] Simulation history comparison charts
- [ ] Export to Excel/CSV
- [ ] Docker containerisation
- [ ] Cloud deployment (AWS/GCP/Azure)
- [ ] Mobile-responsive PWA

---

## 📚 References

- Kern, D.Q. (1950). *Process Heat Transfer*. McGraw-Hill.
- Levenspiel, O. (1999). *Chemical Reaction Engineering*, 3rd Ed. Wiley.
- McCabe, W.L., Smith, J.C., Harriott, P. (2005). *Unit Operations of Chemical Engineering*, 7th Ed.
- Treybal, R.E. (1981). *Mass-Transfer Operations*, 3rd Ed.
- Perry, R.H. & Green, D.W. (2007). *Perry's Chemical Engineers' Handbook*, 8th Ed.
- Towler, G. & Sinnott, R. (2013). *Chemical Engineering Design*, 2nd Ed. Butterworth-Heinemann.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

Pull requests are welcome. Please open an issue first to discuss changes.

---

*Built with ❤️ for the Final Year Chemical Engineering Project*
