# URL Shortener Web Application

A full-stack URL Shortener application built using FastAPI and React.js.

---

## Features

- User Signup and Login (JWT Authentication)
- Create Short URLs
- Custom Short Codes
- URL Analytics
- Click Counter
- QR Code Generation
- URL Expiry Management
- Search URLs
- Update and Delete URLs
- Dashboard Statistics
- Responsive User Interface

---

## Tech Stack

### Frontend
- React.js
- CSS
- Axios

### Backend
- FastAPI
- SQLAlchemy
- SQLite
- JWT Authentication

---

## Project Screenshots

### Dashboard

![Dashboard](screenshots/dashboard.png)

---

## Installation

### Backend Setup

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Setup

```bash
npm install
npm start
```

---

## API Endpoints

### Authentication

```text
POST /signup
POST /login
```

### URL Operations

```text
POST /shorten
GET /all
GET /analytics/{short_code}
PUT /update/{short_code}
DELETE /delete/{short_code}
GET /qr/{short_code}
GET /stats
GET /top
GET /expired
```

---

## Project Structure

```text
backend/
│
├── main.py
├── urls.db
├── qrcodes/

frontend/
│
├── src/
│   ├── pages/
│   ├── services/
│   └── components/
```

---

## Future Enhancements

- Email Notifications
- Pagination
- Dark Mode
- Cloud Database Integration

---


## Live Demo

Frontend:
https://your-vercel-url.vercel.app

Backend API Docs:
https://url-shortener-api-bk8f.onrender.com/docs

## GitHub Repository

https://github.com/yourusername/URL-Shortener

## Author

Yasa Bharathsai

M.Tech CSE, NIT Rourkela