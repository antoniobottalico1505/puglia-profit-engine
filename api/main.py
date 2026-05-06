from __future__ import annotations

import csv
import io
import os
import re
import smtplib
import ssl
from datetime import datetime, timezone
from email.message import EmailMessage
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Text, create_engine, func, select
from sqlalchemy.orm import Session, declarative_base, sessionmaker

APP_NAME = os.getenv("APP_NAME", "Puglia Profit Engine API")
ENV = os.getenv("ENV", "development")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "dev-admin-token-change-me")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
WHATSAPP_PHONE = re.sub(r"\D+", "", os.getenv("WHATSAPP_PHONE", "393701234567"))

raw_database_url = os.getenv("DATABASE_URL", "").strip()
if raw_database_url:
    if raw_database_url.startswith("postgres://"):
        raw_database_url = raw_database_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif raw_database_url.startswith("postgresql://") and "+" not in raw_database_url.split("://", 1)[0]:
        raw_database_url = raw_database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    DATABASE_URL = raw_database_url
else:
    DATABASE_URL = "sqlite:///./puglia_profit_engine.db"

connect_args: Dict[str, Any] = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    full_name = Column(String(160), nullable=False)
    email = Column(String(240), nullable=True)
    phone = Column(String(80), nullable=False)
    channel = Column(String(80), nullable=False, default="site")
    source = Column(String(160), nullable=True)
    locale = Column(String(10), nullable=False, default="it")
    customer_type = Column(String(80), nullable=False, default="turista")
    arrival_date = Column(String(40), nullable=True)
    guests = Column(Integer, nullable=False, default=2)
    budget = Column(Float, nullable=True)
    intent = Column(String(80), nullable=False, default="bundle")
    selected_offer = Column(String(80), nullable=True)
    message = Column(Text, nullable=True)
    status = Column(String(40), nullable=False, default="new")
    lead_score = Column(Float, nullable=False, default=0.0)
    expected_value = Column(Float, nullable=False, default=0.0)
    recommended_offer = Column(String(80), nullable=False, default="arrival_pack")
    utm = Column(JSON, nullable=True)
    payload = Column(JSON, nullable=True)


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    event_type = Column(String(100), nullable=False)
    page = Column(String(220), nullable=True)
    offer_id = Column(String(80), nullable=True)
    value = Column(Float, nullable=False, default=0.0)
    payload = Column(JSON, nullable=True)


class LeadIn(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=160)
    email: Optional[str] = Field(default=None, max_length=240)
    phone: str = Field(..., min_length=5, max_length=80)
    channel: str = Field(default="site", max_length=80)
    source: Optional[str] = Field(default=None, max_length=160)
    locale: str = Field(default="it", max_length=10)
    customer_type: str = Field(default="turista", max_length=80)
    arrival_date: Optional[str] = Field(default=None, max_length=40)
    guests: int = Field(default=2, ge=1, le=250)
    budget: Optional[float] = Field(default=None, ge=0, le=500000)
    intent: str = Field(default="bundle", max_length=80)
    selected_offer: Optional[str] = Field(default=None, max_length=80)
    message: Optional[str] = Field(default=None, max_length=3000)
    utm: Optional[Dict[str, Any]] = None
    payload: Optional[Dict[str, Any]] = None

    @field_validator("phone")
    @classmethod
    def clean_phone(cls, value: str) -> str:
        value = value.strip()
        if len(re.sub(r"\D", "", value)) < 5:
            raise ValueError("phone is too short")
        return value


class LeadOut(BaseModel):
    id: int
    created_at: datetime
    full_name: str
    email: Optional[str]
    phone: str
    channel: str
    source: Optional[str]
    locale: str
    customer_type: str
    arrival_date: Optional[str]
    guests: int
    budget: Optional[float]
    intent: str
    selected_offer: Optional[str]
    message: Optional[str]
    status: str
    lead_score: float
    expected_value: float
    recommended_offer: str
    utm: Optional[Dict[str, Any]]
    payload: Optional[Dict[str, Any]]

    model_config = {"from_attributes": True}


class EventIn(BaseModel):
    event_type: str = Field(..., min_length=2, max_length=100)
    page: Optional[str] = Field(default=None, max_length=220)
    offer_id: Optional[str] = Field(default=None, max_length=80)
    value: float = Field(default=0, ge=0, le=500000)
    payload: Optional[Dict[str, Any]] = None


class StatusIn(BaseModel):
    status: str = Field(..., min_length=2, max_length=40)


CATALOG: Dict[str, Any] = {
    "brands": [
        {
            "id": "cucromia",
            "name": "Crucomia / Cucromia",
            "category": "ristorazione esperienziale",
            "city": "Andria",
            "primary_goal": "aumentare scontrino medio, prenotazioni tavoli, eventi aziendali e cene premium",
            "upsells": ["menu degustazione", "wine pairing", "brunch aziendale", "gift card", "evento privato"],
        },
        {
            "id": "trenino",
            "name": "Il Trenino della Felicità",
            "category": "tour urbano Bari",
            "city": "Bari",
            "primary_goal": "convertire crocieristi e turisti short-stay in tour privati e pacchetti famiglia",
            "upsells": ["tour privato", "foto ricordo", "guida multilingua", "souvenir", "bundle ristorante"],
        },
        {
            "id": "petra_ncc",
            "name": "Petra NCC",
            "category": "noleggio con conducente / transfer premium",
            "city": "Puglia",
            "website": "https://petrancc.it",
            "primary_goal": "riempire tratte aeroporto/porto/hotel e trasformare corse Petra NCC in itinerary package ad alto margine",
            "upsells": ["andata e ritorno", "van gruppo", "giornata autista", "tour Murgia", "transfer evento", "pacchetto hotel/B&B"],
        },
    ],
    "offers": [
        {
            "id": "arrival_pack",
            "title": "Bari Arrival Pack",
            "tag": "più convertibile",
            "price_from": 149,
            "margin_focus": "alta",
            "duration": "4-6 ore",
            "components": ["Petra NCC transfer aeroporto/porto", "giro Bari con trenino", "cena o aperitivo premium"],
            "best_for": ["turisti", "coppie", "famiglie", "crocieristi"],
            "conversion_angle": "Arrivi in Puglia e hai tutto organizzato in un unico acquisto.",
            "stripe_env": "STRIPE_LINK_ARRIVAL_PACK",
        },
        {
            "id": "cruise_day",
            "title": "Cruise Day Bari",
            "tag": "crocieristi",
            "price_from": 79,
            "margin_focus": "volume",
            "duration": "2-4 ore",
            "components": ["Petra NCC pick-up porto", "trenino", "stop fotografici", "opzione pranzo/cena"],
            "best_for": ["crocieristi", "gruppi", "agenzie viaggi"],
            "conversion_angle": "Massimizzi poche ore a Bari senza stress logistico.",
            "stripe_env": "STRIPE_LINK_CRUISE_DAY",
        },
        {
            "id": "gourmet_escape",
            "title": "Murgia Gourmet Escape",
            "tag": "premium",
            "price_from": 189,
            "margin_focus": "molto alta",
            "duration": "mezza giornata",
            "components": ["Petra NCC transfer privato", "Andria/Murgia", "Cucromia menu esperienziale", "rientro"],
            "best_for": ["coppie", "food lovers", "ospiti hotel", "stranieri alto-spendenti"],
            "conversion_angle": "La cena diventa un'esperienza territoriale vendibile a prezzo alto.",
            "stripe_env": "STRIPE_LINK_GOURMET_ESCAPE",
        },
        {
            "id": "corporate_group",
            "title": "Corporate Puglia Day",
            "tag": "B2B",
            "price_from": 990,
            "margin_focus": "molto alta",
            "duration": "1 giorno",
            "components": ["Petra NCC transfer gruppo", "tour privato", "brunch/convention", "cena aziendale"],
            "best_for": ["aziende", "hotel", "MICE", "wedding planner"],
            "conversion_angle": "Un unico fornitore operativo per logistica, experience e ristorazione.",
            "stripe_env": "STRIPE_LINK_CORPORATE_GROUP",
        },
        {
            "id": "private_tour",
            "title": "Private Family Tour",
            "tag": "famiglie",
            "price_from": 119,
            "margin_focus": "media",
            "duration": "2-3 ore",
            "components": ["tour privato", "slot dedicato", "foto", "opzione Petra NCC"],
            "best_for": ["famiglie", "compleanni", "bambini", "turisti italiani"],
            "conversion_angle": "Il tour non è un biglietto, ma un ricordo privato.",
            "stripe_env": "STRIPE_LINK_PRIVATE_TOUR",
        },
    ],
    "channels": [
        "Google Search SEO localizzato",
        "Meta Ads verso WhatsApp",
        "hotel/B&B concierge",
        "porto crociere",
        "aeroporto Bari/Brindisi",
        "agenzie viaggi e wedding planner",
        "Tripadvisor/Google Business retargeting",
    ],
}


def create_db() -> None:
    Base.metadata.create_all(bind=engine)


def db_session() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def parse_origins() -> List[str]:
    raw = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    origins = [x.strip() for x in raw.split(",") if x.strip()]
    if ENV != "production" and "http://localhost:5173" not in origins:
        origins.append("http://localhost:5173")
    return origins


app = FastAPI(title=APP_NAME, version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=parse_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    create_db()


def admin_required(authorization: Optional[str] = Header(None), x_admin_token: Optional[str] = Header(None)) -> None:
    token = x_admin_token or ""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
    if not ADMIN_TOKEN or token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized admin token")


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def choose_offer(payload: LeadIn) -> str:
    text = f"{payload.intent} {payload.customer_type} {payload.message or ''} {payload.source or ''}".lower()
    if payload.selected_offer:
        return payload.selected_offer
    if any(k in text for k in ["azienda", "corporate", "convention", "wedding", "matrimonio", "gruppo", "mice"]):
        return "corporate_group"
    if any(k in text for k in ["crociera", "cruise", "porto"]):
        return "cruise_day"
    if any(k in text for k in ["cena", "gourmet", "ristorante", "andria", "murgia", "wine", "degustazione"]):
        return "gourmet_escape"
    if any(k in text for k in ["famiglia", "bambini", "birthday", "compleanno"]):
        return "private_tour"
    return "arrival_pack"


def offer_price(offer_id: str) -> float:
    for offer in CATALOG["offers"]:
        if offer["id"] == offer_id:
            return float(offer["price_from"])
    return 149.0


def score_lead(payload: LeadIn) -> Dict[str, float | str]:
    offer = choose_offer(payload)
    base = offer_price(offer)
    guests = max(1, payload.guests)
    budget = payload.budget or 0
    expected = max(base, budget) * max(1, min(guests, 30) / 2)

    score = 45.0
    score += min(25.0, guests * 1.8)
    if budget >= 1000:
        score += 18
    elif budget >= 300:
        score += 10
    if payload.arrival_date:
        score += 7
    if payload.email:
        score += 4
    if payload.phone:
        score += 6
    if payload.customer_type.lower() in {"azienda", "corporate", "hotel", "agenzia", "wedding"}:
        score += 16
    if offer in {"corporate_group", "gourmet_escape"}:
        score += 8

    return {
        "recommended_offer": offer,
        "lead_score": round(clamp(score, 0, 100), 2),
        "expected_value": round(expected, 2),
    }


def whatsapp_text(lead: Lead) -> str:
    msg = (
        f"Ciao {lead.full_name}, ho ricevuto la tua richiesta per {lead.recommended_offer}. "
        f"Posso prepararti subito una proposta completa per {lead.guests} persone"
    )
    if lead.arrival_date:
        msg += f" il {lead.arrival_date}"
    msg += "."
    return f"https://wa.me/{WHATSAPP_PHONE}?text={quote_plus(msg)}"


def maybe_send_email(lead: Lead) -> None:
    notify_to = os.getenv("NOTIFY_EMAIL", "").strip()
    smtp_host = os.getenv("SMTP_HOST", "").strip()
    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_pass = os.getenv("SMTP_PASS", "").strip()
    smtp_from = os.getenv("SMTP_FROM", smtp_user).strip()
    if not (notify_to and smtp_host and smtp_user and smtp_pass and smtp_from):
        return

    port = int(os.getenv("SMTP_PORT", "587"))
    msg = EmailMessage()
    msg["Subject"] = f"Nuovo lead {lead.recommended_offer}: {lead.full_name}"
    msg["From"] = smtp_from
    msg["To"] = notify_to
    msg.set_content(
        f"Nuovo lead\n\n"
        f"Nome: {lead.full_name}\nTelefono: {lead.phone}\nEmail: {lead.email or '-'}\n"
        f"Offerta: {lead.recommended_offer}\nPersone: {lead.guests}\nBudget: {lead.budget or '-'}\n"
        f"Score: {lead.lead_score}\nValore atteso: {lead.expected_value}\nMessaggio: {lead.message or '-'}\n"
    )

    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_host, port, timeout=15) as server:
        server.starttls(context=context)
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"ok": True, "app": APP_NAME, "env": ENV, "time": datetime.now(timezone.utc).isoformat()}


@app.get("/api/catalog")
def catalog() -> Dict[str, Any]:
    offers = []
    for offer in CATALOG["offers"]:
        item = dict(offer)
        item["payment_link"] = os.getenv(offer["stripe_env"], "")
        offers.append(item)
    return {**CATALOG, "offers": offers, "whatsapp_phone": WHATSAPP_PHONE}


@app.post("/api/leads")
def create_lead(payload: LeadIn, request: Request, db: Session = Depends(db_session)) -> Dict[str, Any]:
    computed = score_lead(payload)
    lead = Lead(
        full_name=payload.full_name.strip(),
        email=(payload.email or "").strip() or None,
        phone=payload.phone.strip(),
        channel=payload.channel.strip() or "site",
        source=payload.source,
        locale=payload.locale or "it",
        customer_type=payload.customer_type,
        arrival_date=payload.arrival_date,
        guests=payload.guests,
        budget=payload.budget,
        intent=payload.intent,
        selected_offer=payload.selected_offer,
        message=payload.message,
        status="new",
        lead_score=float(computed["lead_score"]),
        expected_value=float(computed["expected_value"]),
        recommended_offer=str(computed["recommended_offer"]),
        utm=payload.utm,
        payload={**(payload.payload or {}), "ip": request.client.host if request.client else None},
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)

    db.add(Event(event_type="lead_created", page="lead_form", offer_id=lead.recommended_offer, value=lead.expected_value, payload={"lead_id": lead.id}))
    db.commit()

    try:
        maybe_send_email(lead)
    except Exception as exc:  # email must never break conversion
        db.add(Event(event_type="email_alert_failed", page="backend", offer_id=lead.recommended_offer, value=0, payload={"lead_id": lead.id, "error": str(exc)[:500]}))
        db.commit()

    payment_link = ""
    for offer in CATALOG["offers"]:
        if offer["id"] == lead.recommended_offer:
            payment_link = os.getenv(offer["stripe_env"], "")
            break

    return {
        "ok": True,
        "lead": LeadOut.model_validate(lead).model_dump(mode="json"),
        "next_actions": {
            "whatsapp_url": whatsapp_text(lead),
            "payment_link": payment_link,
            "recommended_offer": lead.recommended_offer,
        },
    }


@app.post("/api/events")
def create_event(payload: EventIn, db: Session = Depends(db_session)) -> Dict[str, Any]:
    event = Event(event_type=payload.event_type, page=payload.page, offer_id=payload.offer_id, value=payload.value, payload=payload.payload)
    db.add(event)
    db.commit()
    return {"ok": True}


@app.get("/api/admin/leads", dependencies=[Depends(admin_required)])
def list_leads(
    db: Session = Depends(db_session),
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
) -> List[LeadOut]:
    stmt = select(Lead).order_by(Lead.created_at.desc()).limit(limit)
    if status:
        stmt = select(Lead).where(Lead.status == status).order_by(Lead.created_at.desc()).limit(limit)
    rows = db.execute(stmt).scalars().all()
    return [LeadOut.model_validate(row) for row in rows]


@app.patch("/api/admin/leads/{lead_id}", dependencies=[Depends(admin_required)])
def update_lead(lead_id: int, payload: StatusIn, db: Session = Depends(db_session)) -> Dict[str, Any]:
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead.status = payload.status
    db.add(Event(event_type="lead_status_changed", page="admin", offer_id=lead.recommended_offer, value=lead.expected_value, payload={"lead_id": lead.id, "status": payload.status}))
    db.commit()
    db.refresh(lead)
    return {"ok": True, "lead": LeadOut.model_validate(lead)}


@app.get("/api/admin/analytics", dependencies=[Depends(admin_required)])
def analytics(db: Session = Depends(db_session)) -> Dict[str, Any]:
    total_leads = db.scalar(select(func.count(Lead.id))) or 0
    total_expected = db.scalar(select(func.coalesce(func.sum(Lead.expected_value), 0))) or 0
    avg_score = db.scalar(select(func.coalesce(func.avg(Lead.lead_score), 0))) or 0
    events = db.scalar(select(func.count(Event.id))) or 0

    by_offer_rows = db.execute(
        select(Lead.recommended_offer, func.count(Lead.id), func.coalesce(func.sum(Lead.expected_value), 0), func.coalesce(func.avg(Lead.lead_score), 0))
        .group_by(Lead.recommended_offer)
        .order_by(func.coalesce(func.sum(Lead.expected_value), 0).desc())
    ).all()
    by_status_rows = db.execute(select(Lead.status, func.count(Lead.id)).group_by(Lead.status)).all()

    return {
        "total_leads": int(total_leads),
        "pipeline_expected_value": round(float(total_expected), 2),
        "avg_lead_score": round(float(avg_score), 2),
        "events": int(events),
        "by_offer": [
            {"offer": r[0], "leads": int(r[1]), "expected_value": round(float(r[2]), 2), "avg_score": round(float(r[3]), 2)} for r in by_offer_rows
        ],
        "by_status": [{"status": r[0], "leads": int(r[1])} for r in by_status_rows],
        "playbook": [
            "Rispondere entro 5 minuti ai lead con score > 70: sono i più vicini alla conversione.",
            "Proporre sempre bundle Petra NCC + tour + ristorazione prima del singolo servizio.",
            "Spostare gruppi e aziende su Corporate Puglia Day: meno volume, più margine.",
            "Creare UTM separati per hotel, B&B, crociere, aeroporto, Meta Ads e Google Search.",
        ],
    }


@app.get("/api/admin/export/leads.csv", dependencies=[Depends(admin_required)])
def export_leads(db: Session = Depends(db_session)) -> Response:
    rows = db.execute(select(Lead).order_by(Lead.created_at.desc()).limit(5000)).scalars().all()
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["id", "created_at", "name", "email", "phone", "offer", "guests", "budget", "score", "expected_value", "status", "message"])
    for lead in rows:
        writer.writerow([
            lead.id,
            lead.created_at.isoformat() if lead.created_at else "",
            lead.full_name,
            lead.email or "",
            lead.phone,
            lead.recommended_offer,
            lead.guests,
            lead.budget or "",
            lead.lead_score,
            lead.expected_value,
            lead.status,
            (lead.message or "").replace("\n", " "),
        ])
    return Response(content=buffer.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=puglia-profit-leads.csv"})


@app.get("/api/seo/{slug}")
def seo_page(slug: str) -> Dict[str, Any]:
    pages = {
        "bari-crociere": {
            "title": "Tour Bari per crocieristi con trenino, Petra NCC e cena tipica",
            "h1": "Pacchetto Bari per crocieristi: Petra NCC, trenino e gusto pugliese",
            "keywords": ["tour bari crocieristi", "trenino bari vecchia", "petrancc.it", "Petra NCC Bari", "cena tipica puglia"],
        },
        "transfer-andria-cena": {
            "title": "Petra NCC verso Andria con cena esperienziale in Puglia",
            "h1": "Murgia Gourmet Escape: Petra NCC e ristorazione premium",
            "keywords": ["Petra NCC Andria", "petrancc.it", "ristorante andria", "esperienza gastronomica puglia", "ncc puglia"],
        },
        "corporate-puglia": {
            "title": "Eventi aziendali in Puglia con Petra NCC, tour e ristorazione",
            "h1": "Corporate Puglia Day per aziende, convention e gruppi",
            "keywords": ["eventi aziendali puglia", "Petra NCC gruppi Bari", "petrancc.it", "ristorante convention andria", "tour aziendale bari"],
        },
    }
    if slug not in pages:
        raise HTTPException(status_code=404, detail="SEO page not found")
    return pages[slug]
