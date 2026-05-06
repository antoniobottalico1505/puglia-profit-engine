export type Brand = {
  id: string;
  name: string;
  category: string;
  city: string;
  primary_goal: string;
  upsells: string[];
  website?: string;
};

export type Offer = {
  id: string;
  title: string;
  tag: string;
  price_from: number;
  margin_focus: string;
  duration: string;
  components: string[];
  best_for: string[];
  conversion_angle: string;
  stripe_env: string;
  payment_link?: string;
};

export type Catalog = {
  brands: Brand[];
  offers: Offer[];
  channels: string[];
  whatsapp_phone: string;
};

export type LeadInput = {
  full_name: string;
  email?: string;
  phone: string;
  channel: string;
  source?: string;
  locale: string;
  customer_type: string;
  arrival_date?: string;
  guests: number;
  budget?: number;
  intent: string;
  selected_offer?: string;
  message?: string;
  utm?: Record<string, unknown>;
  payload?: Record<string, unknown>;
};

export type Lead = LeadInput & {
  id: number;
  created_at: string;
  status: string;
  lead_score: number;
  expected_value: number;
  recommended_offer: string;
};

export type Analytics = {
  total_leads: number;
  pipeline_expected_value: number;
  avg_lead_score: number;
  events: number;
  by_offer: Array<{ offer: string; leads: number; expected_value: number; avg_score: number }>;
  by_status: Array<{ status: string; leads: number }>;
  playbook: string[];
};
