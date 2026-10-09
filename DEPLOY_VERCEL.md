# How to Deploy to Vercel

This project is pre-configured and 100% ready for deployment on **Vercel** as a Python Serverless Application.

---

## What Has Been Configured for Vercel

1. **`vercel.json`**:
   - Routes all web traffic to the Serverless Python handler (`api/index.py`).
   - Maps static CSS/JS assets directly to `/static/`.
2. **`api/index.py`**:
   - Exposes the Flask WSGI `app` callable required by Vercel serverless runtime.
3. **`config.py`**:
   - Detects the Vercel serverless environment (`VERCEL=1`).
   - Uses `/tmp/production.db` (the only writeable filesystem location in AWS Lambda / Vercel Serverless) for SQLite database storage and auto-seeds initial demo data.
4. **`.vercelignore`**:
   - Excludes local virtual environments, test caches, and large documents to ensure fast, lightweight deployment builds.
5. **`requirements.txt`**:
   - Clean, lightweight production dependencies (`Flask`, `Flask-SQLAlchemy`, `SQLAlchemy`, `Werkzeug`).

---

## Option 1: Deploy via GitHub (Recommended)

1. **Initialize Git & Push to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "AI-Based Production Planning using CSP"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<your-repo-name>.git
   git push -u origin main
   ```

2. **Import into Vercel**:
   - Go to [vercel.com](https://vercel.com/) and sign in.
   - Click **"Add New..."** &rarr; **"Project"**.
   - Select your GitHub repository.
   - **Framework Preset:** Leave as *Other* (Vercel will automatically read `vercel.json`).
   - **Root Directory:** `./` (default).
   - Click **"Deploy"**.

3. **Done!**
   - Vercel will build the Python environment and provide a public HTTPS URL (e.g., `https://ai-production-planner.vercel.app`).

---

## Option 2: Deploy via Vercel CLI

If you have Node.js and the Vercel CLI installed:

1. **Install Vercel CLI (if not installed)**:
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**:
   ```bash
   vercel login
   ```

3. **Deploy from project directory**:
   ```bash
   vercel
   ```
   - *Set up and deploy?* &rarr; **Y**
   - *Which scope?* &rarr; Select your account
   - *Link to existing project?* &rarr; **N**
   - *Project name:* &rarr; `ai-production-planner` (or press Enter)
   - *In which directory is your code located?* &rarr; `./` (press Enter)
   - *Want to modify settings?* &rarr; **N**

4. **Deploy to Production**:
   ```bash
   vercel --prod
   ```

---

## Security & Authentication on Vercel

When hosted publicly on Vercel, the entire site is protected behind strict authentication:
1. **Protected Landing Page:**
   - Any visitor attempting to open `/`, `/dashboard`, `/planner`, etc. is immediately redirected to `/login`.
   - **Login Only:** Public registration is disabled to prevent unauthorized accounts.
2. **Initial Admin Credentials:**
   - **Username:** `admin`
   - **Password:** `admin123`
3. **Change Credentials in Admin Portal:**
   - Navigate to `/admin` or click **"Admin & Credentials"** from the top-right profile dropdown.
   - Enter your current password and set your new username / password.
   - All passwords are securely encrypted using PBKDF2/SHA-256 password hashing.

---

## Verification After Deployment

Once deployed, visit your Vercel URL and check:
1. **Login Gate:** Visiting `/` redirects to `/login`.
2. **Sign In:** Sign in with `admin` / `admin123`.
3. **Admin Portal:** Visit `/admin` to verify or change admin credentials.
4. **Dashboard:** `/dashboard`
5. **AI Production Planner:** `/planner` (Click **"Generate Production Plan"** to test live CSP solver execution on Vercel).
6. **Schedule & Gantt Timeline:** `/schedule`

