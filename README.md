# Puglia Profit Engine

Cartella full-stack pronta per GitHub, Vercel e Render. Il progetto crea un revenue hub per vendere pacchetti turistici pugliesi ad alto margine combinando:

- ristorazione esperienziale: Crucomia / Cucromia;
- tour urbano: Il Trenino della Felicità;
- noleggio con conducente / transfer premium: Petra NCC (`petrancc.it`).

L'obiettivo operativo è aumentare scontrino medio e conversioni: il cliente non compra un singolo servizio, ma un pacchetto completo con Petra NCC, esperienza e ristorazione.

## Stack

```text
puglia-profit-engine/
├─ api/                  FastAPI + SQLAlchemy + PostgreSQL/SQLite fallback
├─ web/                  React + Vite deployabile su Vercel
├─ scripts/              comandi PowerShell per locale, deploy check e GitHub
├─ docs/                 playbook commerciale
├─ render.yaml           blueprint Render backend + Postgres
├─ vercel.json           configurazione Vercel per frontend
└─ README.md
```

## Funzioni già implementate

- Landing page premium responsive.
- Catalogo brand e pacchetti: Arrival Pack, Cruise Day, Gourmet Escape, Corporate Puglia Day, Private Family Tour.
- Lead form con budget, data, persone, tipo cliente e pacchetto.
- Lead scoring automatico.
- Valore atteso pipeline.
- WhatsApp link precompilato dopo invio richiesta.
- CRM admin con stato lead.
- Export CSV lead.
- Analytics per offerta, status, eventi.
- Event tracking minimale.
- SMTP opzionale per notifiche email immediate.
- Stripe Payment Links opzionali via variabili ambiente.
- PostgreSQL su Render, SQLite in locale se `DATABASE_URL` è vuota.
- SEO endpoint per pagine verticali.

## Avvio locale su Windows PowerShell

Dalla root del progetto:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\local-dev.ps1
```

Oppure manuale:

```powershell
cd api
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Secondo terminale:

```powershell
cd web
npm install
copy .env.example .env
npm run dev
```

Frontend locale: `http://localhost:5173`  
Backend locale: `http://localhost:8000/health`

## Deploy Render

1. Vai su Render.
2. New > Blueprint.
3. Collega il repo GitHub.
4. Render legge `render.yaml`.
5. Imposta almeno queste env sul servizio backend:

```text
ENV=production
ADMIN_TOKEN=<token lungo casuale>
CORS_ORIGINS=https://TUO-PROGETTO.vercel.app,http://localhost:5173
FRONTEND_URL=https://TUO-PROGETTO.vercel.app
WHATSAPP_PHONE=39NUMERO_REALE_PETRA_NCC_O_CENTRALE_COMMERCIALE
```

Opzionali ma consigliate:

```text
NOTIFY_EMAIL=prenotazioni@dominio.it
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=email@gmail.com
SMTP_PASS=app-password-gmail
SMTP_FROM=email@gmail.com
STRIPE_LINK_ARRIVAL_PACK=https://buy.stripe.com/...
STRIPE_LINK_CRUISE_DAY=https://buy.stripe.com/...
STRIPE_LINK_GOURMET_ESCAPE=https://buy.stripe.com/...
STRIPE_LINK_CORPORATE_GROUP=https://buy.stripe.com/...
STRIPE_LINK_PRIVATE_TOUR=https://buy.stripe.com/...
```

## Deploy Vercel

1. Importa lo stesso repo su Vercel.
2. Framework: Vite.
3. Root: lascia root del repository, perché `vercel.json` entra in `web` da solo.
4. Env Vercel:

```text
VITE_API_BASE_URL=https://puglia-profit-engine-api.onrender.com
VITE_ADMIN_TOKEN=<stesso ADMIN_TOKEN se vuoi precompilare l'admin>
VITE_BRAND_OWNER=Antonio
```

Se preferisci non esporre il token nel bundle frontend, lascia vuoto `VITE_ADMIN_TOKEN` e inseriscilo manualmente nel campo admin.

## GitHub

Per creare repo e pushare con GitHub CLI:

```powershell
cd C:\percorso\puglia-profit-engine
winget install GitHub.cli
gh auth login
.\scripts\push-github.ps1
```

Se hai già creato manualmente il repo:

```powershell
cd C:\percorso\puglia-profit-engine
git init
git add .
git commit -m "Create Puglia Profit Engine"
git branch -M main
git remote add origin https://github.com/antoniobottalico1505/puglia-profit-engine.git
git push -u origin main
```

## Strategia pratica per monetizzare

1. Portare traffico su offerte verticali, non su homepage generica.
2. Meta Ads verso WhatsApp per pacchetti rapidi: crocieristi, famiglie, weekend.
3. Google Search su keyword con intenzione alta: Petra NCC Bari, petrancc.it, tour Bari crocieristi, cena tipica Andria, eventi aziendali Puglia.
4. Partnership dirette con hotel/B&B: QR code al banco e link con UTM dedicato.
5. Ogni richiesta singola va trasformata in bundle: Petra NCC + tour + ristorazione.
6. Ogni gruppo sopra 8 persone va spinto su preventivo corporate, non prezzo standard.
7. Lead score sopra 70: risposta entro 5 minuti.

## Nota legale/commerciale

Il software aiuta a vendere, tracciare e organizzare lead. Non garantisce risultati economici automatici: i profitti dipendono da prezzo, capacità operativa, qualità del servizio, ads, stagionalità, recensioni e follow-up commerciale.
