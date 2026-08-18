# KyU Campus Connect

**Innovative Technology for a Dynamic World**

Kirinyaga University's official campus communication platform. Connect with classmates, join study groups, access e-books, collaborate in coding workspaces, and stay updated with campus events.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **Real-time Chat** - Instant messaging with Socket.IO
- **Study Groups** - Create and join study groups with video/audio calls
- **E-book Catalog** - Search, preview, and download e-books
- **AI Study Assistant** - Get help from an AI-powered chatbot
- **Coding Workspaces** - Collaborative code editor with multiple language support
- **Campus Events** - Stay updated with university events and news
- **Moments Feed** - Share campus life with photos and posts
- **Calendar Sync** - Sync with Google Calendar, Outlook, and more
- **Cloud Backup** - Backup data to Google Drive, OneDrive, or Dropbox
- **Admin Panel** - User management, analytics, and audit logs
- **Multi-platform** - Web, Android (APK), Windows, Linux (DEB/AppImage), PWA

## Tech Stack

### Backend
- **Framework**: FastAPI + Socket.IO
- **Database**: SQLAlchemy (async) + SQLite/PostgreSQL
- **Auth**: JWT + OAuth (Google, Microsoft, Apple)
- **Real-time**: Socket.IO + WebRTC

### Frontend
- **Framework**: React 18 + React Router
- **Mobile**: Capacitor (Android)
- **Desktop**: Electron
- **State**: Context API

### DevOps
- **Container**: Docker + Docker Compose
- **CI/CD**: GitHub Actions
- **Deploy**: Railway / Oracle Cloud
- **SSL**: Cloudflare / Let's Encrypt

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+

### Installation

```bash
# Clone the repo
git clone https://github.com/Kiplangatisaac/Campus-connect.git
cd Campus-connect

# Setup backend
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
cp ../.env.example .env  # Edit with your values

# Setup frontend
cd ../frontend
npm install

# Start backend (terminal 1)
cd backend
uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# Start frontend (terminal 2)
cd frontend
PORT=3001 npm start
```

### Docker

```bash
docker compose up --build
```

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

## Project Structure

```
Campus-connect/
├── backend/               # FastAPI backend
│   ├── main.py            # App entry point
│   ├── config.py          # Settings
│   ├── database.py        # SQLAlchemy engine
│   ├── auth.py            # Authentication
│   ├── oauth.py           # OAuth providers
│   ├── routes/            # API routers (16 modules)
│   ├── models/            # Database models
│   ├── schemas/           # Pydantic schemas
│   ├── modules/           # OOD modules
│   ├── core/              # Domain/infrastructure
│   └── realtime/          # Socket.IO handlers
├── frontend/              # React frontend
│   ├── src/               # Source code
│   ├── public/            # Static assets
│   ├── android/           # Capacitor Android
│   └── electron/          # Electron desktop
├── deploy/                # Deployment configs
├── db/                    # Database schemas
├── Dockerfile             # Docker build
├── railway.json           # Railway deploy
└── .github/workflows/     # CI/CD
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

```env
DATABASE_URL=sqlite+aiosqlite:///./campus.db
JWT_SECRET_KEY=your-secret-key
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

See `.env.example` for all available options.

## Deployment

### Railway
1. Connect GitHub repo to Railway
2. Railway auto-detects the Dockerfile
3. Set environment variables in Railway dashboard
4. Deploy!

### Oracle Cloud
```bash
# On your server
git clone https://github.com/Kiplangatisaac/Campus-connect.git
cd Campus-connect
docker compose -f docker-compose.prod.yml up -d
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to the branch
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

**Kirinyaga University**
- P.O.Box 143-10300 Kerugoya, Kenya
- +254 709 742000
- info@kyu.ac.ke
- [www.kyu.ac.ke](https://www.kyu.ac.ke)
