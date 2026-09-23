# AquaAlert Odisha

Hyperlocal (ward-level) flood nowcasting prototype for six flood-prone Odisha
cities — Cuttack, Bhubaneswar, Puri, Balasore, Kendrapara, and Sambalpur.
Built for SIH 2026.

- **Citizens**: open the site, it auto-detects your location, shows your
  zone's flood risk (Low/Medium/High) on a map, lets you opt in to SMS
  alerts with just a phone number, and lets you report choked
  drains/waterlogging with a photo.
- **Municipal admins**: a dashboard showing all zones' risk, citizen reports,
  a "Send Alert" button, and an action log.

## Stack

- **Frontend**: React + Vite + Leaflet (`frontend/`)
- **Backend**: FastAPI + scikit-learn Random Forest (`backend/`)
- **Database**: MongoDB (falls back automatically to in-memory storage if
  no MongoDB is configured/reachable — the app still runs end-to-end without it)
- **SMS**: Fast2SMS (falls back automatically to a mock/console log if no
  API key is configured)

## Prerequisites

You need to install these before running the project:

1. **Python 3.10+** — already available on this machine.
2. **Node.js 18+** — not currently installed. Download from
   [nodejs.org](https://nodejs.org/) (LTS version), then verify with:
   ```bash
   node --version
   npm --version
   ```
3. **MongoDB** (optional) — either:
   - Install [MongoDB Community Server](https://www.mongodb.com/try/download/community) locally, or
   - Create a free [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register) cluster and copy its connection string.
   - Or skip this entirely — the backend automatically uses in-memory storage if `MONGODB_URI` is unset or unreachable. Good enough for development and demos; data resets on restart.
4. **Fast2SMS API key** (optional) — sign up at [fast2sms.com](https://www.fast2sms.com/), get an API key from the dashboard. Without it, SMS sends are mocked (logged to the backend console) so the whole alert flow still works for a demo.

## Backend setup

```bash
cd backend
python -m venv venv
./venv/Scripts/activate      # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
cp .env.example .env         # then edit .env with your Mongo/Fast2SMS creds if you have them
python -m app.ml.train_model # trains and saves the Random Forest model (also runs automatically on first server start)
uvicorn app.main:app --reload
```

Backend runs at `http://127.0.0.1:8000`. Check `http://127.0.0.1:8000/api/health`
to confirm it's up and see which storage mode it picked (`mongo` or `memory`).
Interactive API docs are at `http://127.0.0.1:8000/docs`.

## Frontend setup

```bash
cd frontend
npm install
cp .env.example .env   # defaults to http://127.0.0.1:8000, edit if your backend runs elsewhere
npm run dev
```

Frontend runs at `http://localhost:5173`. Open it in a browser and allow
location access to see the auto-detect-zone flow.

## Demo flow for judges

1. Open the citizen map (`/`) — it detects your location and shows the
   nearest zone's current (Low) risk.
2. Subscribe a phone number for that zone.
3. Switch to the admin dashboard (`/admin`) and click **"Simulate Heavy
   Rain"** on that zone — this pushes synthetic rainfall/river-level data
   through the same prediction pipeline a real IMD/CWC feed would use.
4. Watch the zone flip to **High** risk, an SMS auto-fire to the subscribed
   number (mocked in the console if no Fast2SMS key is set), and an entry
   appear in the action log.
5. Go back to the citizen map, submit a "blocked drain" report with a photo
   for a zone — note how it feeds into that zone's `citizen_report_count`
   and `active_drain_count`, which the model uses on the next prediction.

## How the ML model works

`backend/app/ml/train_model.py` generates a synthetic training set from the
9 input features (rainfall, river level, river rise rate, elevation, slope,
distance to river, drainage density, active drain count, citizen report
count), using a weighted rule-of-thumb formula plus noise to assign
Low/Medium/High labels, then fits a `RandomForestClassifier` on it. This
stands in for the real historical flood dataset called out in the "Future
Scope" (live IMD/CWC/CGWB integration). If the trained model file is ever
missing, `backend/app/ml/predict.py` falls back to the same rule-of-thumb
formula directly — this is the cold-start fallback for zones/situations the
ML model can't confidently handle.

## Project structure

```
backend/
  app/
    main.py            FastAPI app, CORS, startup (trains model, seeds risk state)
    storage.py          MongoDB / in-memory storage abstraction
    ml/
      train_model.py    synthetic data generation + Random Forest training
      predict.py         loads the model, predicts risk, rule-based fallback
    routes/
      zones.py           zone list/detail/nearest-zone (geolocation)
      predict.py          risk re-evaluation + demo "simulate" endpoint
      alerts.py           phone opt-in, manual SMS send
      reports.py          citizen reports (with photo upload)
      admin.py            dashboard overview + action log
    services/
      sms.py              Fast2SMS wrapper (mocks if no API key)
      risk_engine.py       combines zone + live conditions -> prediction -> alert trigger
    data/zones.json        29 synthetic ward-level zones across the 6 cities

frontend/
  src/
    pages/Home.jsx        citizen map + geolocation + opt-in + reporting
    pages/Admin.jsx        municipal dashboard
    components/            map, zone panel, forms, admin widgets
    api.js                  backend API client
```
