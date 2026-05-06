import { useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { ArrowRight, BarChart3, Building2, CalendarDays, Car, ChefHat, Download, MessageCircle, ShieldCheck, Sparkles, TrainFront, TrendingUp, Users } from 'lucide-react';
import { createLead, downloadLeadsCsv, fetchAnalytics, fetchCatalog, fetchLeads, getApiBaseUrl, trackEvent, updateLeadStatus } from './api';
import type { Analytics, Catalog, Lead, LeadInput, Offer } from './types';
import './styles.css';

const defaultCatalog: Catalog = {
  whatsapp_phone: '393701234567',
  brands: [],
  channels: [],
  offers: []
};

const offerIcon: Record<string, ReactNode> = {
  arrival_pack: <Sparkles size={22} />,
  cruise_day: <TrainFront size={22} />,
  gourmet_escape: <ChefHat size={22} />,
  corporate_group: <Building2 size={22} />,
  private_tour: <Users size={22} />
};

const statusLabels = ['new', 'contacted', 'proposal_sent', 'won', 'lost'];

function euro(value: number): string {
  return new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(value || 0);
}

function utmFromUrl(): Record<string, string> {
  const params = new URLSearchParams(window.location.search);
  const out: Record<string, string> = {};
  for (const key of ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term']) {
    const value = params.get(key);
    if (value) out[key] = value;
  }
  return out;
}

function pickDefaultOffer(catalog: Catalog): string {
  return catalog.offers[0]?.id || 'arrival_pack';
}

function Header() {
  return (
    <header className="topbar">
      <a href="#home" className="brand-mark" aria-label="Puglia Profit Engine home">
        <span className="brand-dot">P</span>
        <span>
          <strong>Puglia Profit Engine</strong>
          <small>Tourism revenue hub</small>
        </span>
      </a>
      <nav>
        <a href="#packages">Pacchetti</a>
        <a href="#engine">Motore</a>
        <a href="#lead">Lead</a>
        <a href="#admin">Admin</a>
      </nav>
    </header>
  );
}

function Hero({ catalog, selectedOffer, setSelectedOffer }: { catalog: Catalog; selectedOffer: string; setSelectedOffer: (id: string) => void }) {
  const selected = catalog.offers.find((offer) => offer.id === selectedOffer) || catalog.offers[0];
  return (
    <section id="home" className="hero section-pad">
      <div className="hero-copy">
        <p className="eyebrow">Sistema operativo commerciale per Puglia premium</p>
        <h1>Trasforma ristorante, tour e Petra NCC in un unico funnel ad alto margine.</h1>
        <p className="hero-text">
          Una piattaforma pronta per vendere pacchetti combinati: Petra NCC, Trenino della Felicità, esperienza food premium e offerte B2B. Il valore non è il singolo biglietto: è il bundle.
        </p>
        <div className="hero-actions">
          <a className="btn primary" href="#lead" onClick={() => trackEvent('cta_hero_lead')}>Genera richiesta <ArrowRight size={18} /></a>
          <a className="btn ghost" href="#admin">Apri CRM</a>
        </div>
        <div className="trust-row">
          <span><ShieldCheck size={16} /> Lead scoring</span>
          <span><MessageCircle size={16} /> WhatsApp ready</span>
          <span><BarChart3 size={16} /> Pipeline value</span>
        </div>
      </div>
      <div className="hero-card glass">
        <div className="card-topline">
          <span>Offerta consigliata</span>
          <strong>{selected?.tag || 'bundle'}</strong>
        </div>
        <h2>{selected?.title || 'Bari Arrival Pack'}</h2>
        <p>{selected?.conversion_angle}</p>
        <div className="offer-price">da {euro(selected?.price_from || 149)}</div>
        <div className="mini-list">
          {(selected?.components || []).map((component) => <span key={component}>{component}</span>)}
        </div>
        <select value={selectedOffer} onChange={(event) => setSelectedOffer(event.target.value)} aria-label="Seleziona pacchetto">
          {catalog.offers.map((offer) => <option key={offer.id} value={offer.id}>{offer.title}</option>)}
        </select>
      </div>
    </section>
  );
}

function BrandStrip({ catalog }: { catalog: Catalog }) {
  const icons: Record<string, ReactNode> = {
    cucromia: <ChefHat />,
    trenino: <TrainFront />,
    petra_ncc: <Car />
  };
  return (
    <section className="brand-strip section-pad">
      {catalog.brands.map((brand) => (
        <article className="brand-card" key={brand.id}>
          <div className="round-icon">{icons[brand.id] || <Sparkles />}</div>
          <h3>{brand.name}</h3>
          <p>{brand.category} · {brand.city}</p>
          <small>{brand.primary_goal}</small>
          {brand.website && <a className="brand-link" href={brand.website} target="_blank" rel="noreferrer">Apri sito ufficiale</a>}
        </article>
      ))}
    </section>
  );
}

function Packages({ catalog, selectedOffer, setSelectedOffer }: { catalog: Catalog; selectedOffer: string; setSelectedOffer: (id: string) => void }) {
  return (
    <section id="packages" className="section-pad section-block">
      <div className="section-head">
        <p className="eyebrow">Pacchetti vendibili subito</p>
        <h2>Prodotti ad alto valore percepito, non servizi isolati.</h2>
        <p>Ogni card è costruita per aumentare scontrino medio e probabilità di cross-sell.</p>
      </div>
      <div className="cards-grid">
        {catalog.offers.map((offer) => (
          <article className={`offer-card ${selectedOffer === offer.id ? 'active' : ''}`} key={offer.id} onClick={() => { setSelectedOffer(offer.id); trackEvent('offer_selected', { offer_id: offer.id, value: offer.price_from }); }}>
            <div className="offer-head">
              <div className="round-icon">{offerIcon[offer.id] || <Sparkles size={22} />}</div>
              <span>{offer.tag}</span>
            </div>
            <h3>{offer.title}</h3>
            <p>{offer.conversion_angle}</p>
            <strong>da {euro(offer.price_from)}</strong>
            <ul>
              {offer.components.map((component) => <li key={component}>{component}</li>)}
            </ul>
            <button className="btn small" type="button">Usa nel modulo</button>
          </article>
        ))}
      </div>
    </section>
  );
}

function Engine({ catalog }: { catalog: Catalog }) {
  return (
    <section id="engine" className="section-pad engine-grid">
      <div className="section-head left">
        <p className="eyebrow">Come aumenta i guadagni</p>
        <h2>Il sistema spinge il cliente dal servizio base al pacchetto completo.</h2>
        <p>
          La logica commerciale è semplice: chi arriva in Puglia ha bisogno di Petra NCC, esperienza, tempo risparmiato e momenti memorabili. Il sito vende l'intera sequenza.
        </p>
      </div>
      <div className="engine-list">
        <div className="engine-item"><TrendingUp /><strong>Lead scoring automatico</strong><span>Priorità immediata ai clienti con budget, data e gruppo.</span></div>
        <div className="engine-item"><MessageCircle /><strong>Risposta WhatsApp pronta</strong><span>Riduce attrito tra richiesta, preventivo e conferma.</span></div>
        <div className="engine-item"><CalendarDays /><strong>Pacchetti stagionali</strong><span>Crociere, weekend, eventi aziendali, famiglie, hotel.</span></div>
        <div className="engine-item"><Download /><strong>CRM esportabile</strong><span>CSV per follow-up, agenzie, concierge, retargeting.</span></div>
      </div>
      <div className="channel-panel glass">
        <h3>Canali da attivare</h3>
        <div className="chips">
          {catalog.channels.map((channel) => <span key={channel}>{channel}</span>)}
        </div>
      </div>
    </section>
  );
}

function LeadForm({ catalog, selectedOffer, setSelectedOffer }: { catalog: Catalog; selectedOffer: string; setSelectedOffer: (id: string) => void }) {
  const [form, setForm] = useState<LeadInput>({
    full_name: '',
    email: '',
    phone: '',
    channel: 'site',
    source: 'landing',
    locale: 'it',
    customer_type: 'turista',
    arrival_date: '',
    guests: 2,
    budget: 250,
    intent: 'bundle',
    selected_offer: selectedOffer,
    message: '',
    utm: utmFromUrl(),
    payload: { page: window.location.pathname }
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ lead: Lead; whatsapp_url: string; payment_link?: string } | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    setForm((old) => ({ ...old, selected_offer: selectedOffer }));
  }, [selectedOffer]);

  const selected = catalog.offers.find((offer) => offer.id === selectedOffer);
  const estimated = useMemo(() => {
    const guests = Number(form.guests || 1);
    const base = selected?.price_from || 149;
    return Math.max(Number(form.budget || 0), base) * Math.max(1, Math.min(guests, 30) / 2);
  }, [form.guests, form.budget, selected]);

  async function submitLead(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError('');
    try {
      const response = await createLead(form);
      setResult({ lead: response.lead, whatsapp_url: response.next_actions.whatsapp_url, payment_link: response.next_actions.payment_link });
      trackEvent('lead_form_submitted', { offer_id: response.lead.recommended_offer, value: response.lead.expected_value });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Errore invio richiesta');
    } finally {
      setLoading(false);
    }
  }

  return (
    <section id="lead" className="section-pad lead-section">
      <div className="lead-copy">
        <p className="eyebrow">Conversione immediata</p>
        <h2>Modulo preventivo con scoring e next action automatica.</h2>
        <p>Ogni richiesta entra nel CRM, riceve un valore atteso e produce un link WhatsApp già compilato. Collegando Stripe Payment Links, il pacchetto può diventare pagabile subito.</p>
        <div className="value-box">
          <span>Valore stimato richiesta</span>
          <strong>{euro(estimated)}</strong>
          <small>Calcolato da pacchetto, budget e numero persone.</small>
        </div>
      </div>
      <form className="lead-form glass" onSubmit={submitLead}>
        <div className="form-row">
          <label>Nome e cognome<input value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} required placeholder="Mario Rossi" /></label>
          <label>Telefono / WhatsApp<input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} required placeholder="+39..." /></label>
        </div>
        <div className="form-row">
          <label>Email<input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="cliente@email.com" /></label>
          <label>Tipo cliente<select value={form.customer_type} onChange={(e) => setForm({ ...form, customer_type: e.target.value })}>
            <option value="turista">Turista</option>
            <option value="crocierista">Crocierista</option>
            <option value="famiglia">Famiglia</option>
            <option value="hotel">Hotel / B&B</option>
            <option value="azienda">Azienda</option>
            <option value="agenzia">Agenzia viaggi</option>
            <option value="wedding">Wedding planner</option>
          </select></label>
        </div>
        <div className="form-row">
          <label>Pacchetto<select value={selectedOffer} onChange={(e) => { setSelectedOffer(e.target.value); setForm({ ...form, selected_offer: e.target.value }); }}>
            {catalog.offers.map((offer) => <option key={offer.id} value={offer.id}>{offer.title}</option>)}
          </select></label>
          <label>Data<input type="date" value={form.arrival_date} onChange={(e) => setForm({ ...form, arrival_date: e.target.value })} /></label>
        </div>
        <div className="form-row">
          <label>Persone<input type="number" min={1} max={250} value={form.guests} onChange={(e) => setForm({ ...form, guests: Number(e.target.value) })} /></label>
          <label>Budget indicativo<input type="number" min={0} value={form.budget || 0} onChange={(e) => setForm({ ...form, budget: Number(e.target.value) })} /></label>
        </div>
        <label>Messaggio<textarea value={form.message} onChange={(e) => setForm({ ...form, message: e.target.value })} placeholder="Es. arriviamo al porto alle 10, vogliamo tour breve e cena tipica..." /></label>
        {error && <div className="error-box">{error}</div>}
        {result && (
          <div className="success-box">
            <strong>Lead #{result.lead.id} creato · score {result.lead.lead_score}/100 · valore {euro(result.lead.expected_value)}</strong>
            <div className="success-actions">
              <a className="btn primary" href={result.whatsapp_url} target="_blank" rel="noreferrer">Apri WhatsApp</a>
              {result.payment_link ? <a className="btn ghost" href={result.payment_link} target="_blank" rel="noreferrer">Pagamento Stripe</a> : <span className="muted">Aggiungi Payment Link Stripe nelle env per incassare subito.</span>}
            </div>
          </div>
        )}
        <button className="btn primary full" disabled={loading} type="submit">{loading ? 'Invio...' : 'Crea lead e proposta'} <ArrowRight size={18} /></button>
      </form>
    </section>
  );
}

function Admin() {
  const [token, setToken] = useState(import.meta.env.VITE_ADMIN_TOKEN || '');
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function load() {
    setLoading(true);
    setError('');
    try {
      const [a, l] = await Promise.all([fetchAnalytics(token), fetchLeads(token)]);
      setAnalytics(a);
      setLeads(l);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Errore caricamento admin');
    } finally {
      setLoading(false);
    }
  }

  async function changeStatus(leadId: number, status: string) {
    await updateLeadStatus(token, leadId, status);
    await load();
  }

  return (
    <section id="admin" className="section-pad admin-section">
      <div className="section-head left">
        <p className="eyebrow">Area operativa</p>
        <h2>CRM minimale per seguire lead, valore e conversioni.</h2>
        <p>Backend attivo su <code>{getApiBaseUrl()}</code>. Imposta <code>ADMIN_TOKEN</code> su Render e lo stesso valore su <code>VITE_ADMIN_TOKEN</code> in Vercel solo se vuoi precompilarlo.</p>
      </div>
      <div className="admin-login glass">
        <input value={token} onChange={(e) => setToken(e.target.value)} placeholder="ADMIN_TOKEN" type="password" />
        <button className="btn primary" onClick={load} disabled={loading}>{loading ? 'Carico...' : 'Carica dashboard'}</button>
        <button className="btn ghost" onClick={() => downloadLeadsCsv(token)}>Export CSV</button>
      </div>
      {error && <div className="error-box">{error}</div>}
      {analytics && (
        <div className="metrics-grid">
          <div className="metric"><span>Lead</span><strong>{analytics.total_leads}</strong></div>
          <div className="metric"><span>Pipeline</span><strong>{euro(analytics.pipeline_expected_value)}</strong></div>
          <div className="metric"><span>Score medio</span><strong>{analytics.avg_lead_score}/100</strong></div>
          <div className="metric"><span>Eventi</span><strong>{analytics.events}</strong></div>
        </div>
      )}
      {analytics && (
        <div className="admin-grid">
          <div className="glass panel">
            <h3>Valore per offerta</h3>
            {analytics.by_offer.length === 0 ? <p className="muted">Nessun lead ancora.</p> : analytics.by_offer.map((row) => (
              <div className="bar-row" key={row.offer}>
                <span>{row.offer}</span>
                <strong>{euro(row.expected_value)}</strong>
              </div>
            ))}
          </div>
          <div className="glass panel">
            <h3>Playbook operativo</h3>
            <ol>
              {analytics.playbook.map((item) => <li key={item}>{item}</li>)}
            </ol>
          </div>
        </div>
      )}
      <div className="lead-table glass">
        <div className="table-head"><strong>Ultimi lead</strong><span>{leads.length} record</span></div>
        <div className="table-scroll">
          <table>
            <thead><tr><th>Data</th><th>Cliente</th><th>Offerta</th><th>Persone</th><th>Score</th><th>Valore</th><th>Stato</th></tr></thead>
            <tbody>
              {leads.map((lead) => (
                <tr key={lead.id}>
                  <td>{new Date(lead.created_at).toLocaleString('it-IT')}</td>
                  <td><strong>{lead.full_name}</strong><br /><small>{lead.phone}</small></td>
                  <td>{lead.recommended_offer}</td>
                  <td>{lead.guests}</td>
                  <td>{lead.lead_score}</td>
                  <td>{euro(lead.expected_value)}</td>
                  <td><select value={lead.status} onChange={(e) => changeStatus(lead.id, e.target.value)}>{statusLabels.map((s) => <option key={s} value={s}>{s}</option>)}</select></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="footer section-pad">
      <div>
        <strong>Puglia Profit Engine</strong>
        <p>Funnel, CRM e pacchetti cross-sell per turismo pugliese premium.</p>
      </div>
      <div className="footer-links">
        <a href="#home">Home</a>
        <a href="#packages">Pacchetti</a>
        <a href="#admin">Admin</a>
      </div>
    </footer>
  );
}

export default function App() {
  const [catalog, setCatalog] = useState<Catalog>(defaultCatalog);
  const [selectedOffer, setSelectedOffer] = useState('arrival_pack');

  useEffect(() => {
    fetchCatalog()
      .then((data) => {
        setCatalog(data);
        setSelectedOffer(pickDefaultOffer(data));
        trackEvent('page_loaded', { offer_id: pickDefaultOffer(data) });
      })
      .catch(() => {
        setCatalog({
          ...defaultCatalog,
          offers: [
            { id: 'arrival_pack', title: 'Bari Arrival Pack', tag: 'bundle', price_from: 149, margin_focus: 'alta', duration: '4-6 ore', components: ['Petra NCC', 'tour', 'cena'], best_for: ['turisti'], conversion_angle: 'Tutto organizzato in un unico acquisto.', stripe_env: '' }
          ]
        });
      });
  }, []);

  return (
    <>
      <Header />
      <main>
        <Hero catalog={catalog} selectedOffer={selectedOffer} setSelectedOffer={setSelectedOffer} />
        <BrandStrip catalog={catalog} />
        <Packages catalog={catalog} selectedOffer={selectedOffer} setSelectedOffer={setSelectedOffer} />
        <Engine catalog={catalog} />
        <LeadForm catalog={catalog} selectedOffer={selectedOffer} setSelectedOffer={setSelectedOffer} />
        <Admin />
      </main>
      <Footer />
    </>
  );
}
