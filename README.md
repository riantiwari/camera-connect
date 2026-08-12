# PhotoWhips / Camera Connect MVP

A Flask MVP connecting car owners and photographers.

## Included
- Public landing site
- Car discovery + search
- Car detail pages and shoot requests
- Photographer directory and profiles
- Photographer portfolios
- Owner garages and car uploads
- Photography job board and applications
- Role-based dashboards
- Reviews + Bayesian-style PhotoWhips reputation score
- Movie shoots, style shoots, pricing and contact pages
- Blog
- Admin dashboard + blog publishing + listing moderation
- Responsive mobile UI
- SQLite local database and event tracking

## Local setup
```bash
git clone https://github.com/riantiwari/camera-connect.git
cd camera-connect
git checkout agent/full-mvp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app app seed
python app.py
```

Open http://127.0.0.1:5000

## Demo accounts
All seeded accounts use password `demo123`.

- Admin: `admin@demo.com`
- Photographer: `maya@demo.com`
- Photographer: `leo@demo.com`
- Owner: `jake@demo.com`

## Test on your phone
Run:
```bash
python app.py
```

The app listens on `0.0.0.0:5000`. With your phone and Mac on the same Wi-Fi, find your Mac's local IP in System Settings → Wi-Fi → Details and open `http://YOUR_MAC_IP:5000` on your phone.

## Deployment
The project includes Gunicorn in `requirements.txt`. Set a strong `SECRET_KEY` environment variable in production. The SQLite database is intended for MVP/local demos; move to PostgreSQL before serious production use.
