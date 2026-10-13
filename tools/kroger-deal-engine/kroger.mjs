const API_BASE = "https://api.kroger.com/v1";
const TOKEN_URL = `${API_BASE}/connect/oauth2/token`;

function required(value, name) {
  if (!value || !String(value).trim()) throw new Error(`${name}_REQUIRED`);
  return String(value).trim();
}

function money(value) {
  const n = Number(value);
  return Number.isFinite(n) ? Math.round(n * 100) / 100 : null;
}

export function normalizeProduct(product = {}) {
  const item = Array.isArray(product.items) ? product.items[0] : null;
  const price = item?.price || product.price || {};
  const regular = money(price.regular);
  const promo = money(price.promo);
  const effective = promo ?? regular;
  const size = item?.size || product.packageSize || null;
  const upc = product.upc || item?.upc || null;
  const description = product.description || product.brand || "Unknown product";

  return {
    productId: product.productId || null,
    upc,
    description,
    brand: product.brand || null,
    size,
    aisle: Array.isArray(product.aisleLocations)
      ? product.aisleLocations.map(x => x.description || x.number || x.bayNumber).filter(Boolean).join(", ") || null
      : null,
    regularPrice: regular,
    promoPrice: promo,
    effectivePrice: effective,
    onPromo: promo !== null && (regular === null || promo < regular)
  };
}

export function normalizeLocation(location = {}) {
  const address = location.address || {};
  return {
    locationId: location.locationId || null,
    name: location.name || "Kroger location",
    chain: location.chain || null,
    phone: location.phone || null,
    address: [address.addressLine1, address.city, address.state, address.zipCode].filter(Boolean).join(", "),
    latitude: location.geolocation?.latitude ?? null,
    longitude: location.geolocation?.longitude ?? null
  };
}

export class KrogerClient {
  constructor({ clientId, clientSecret, scope = "product.compact", fetchImpl = globalThis.fetch } = {}) {
    this.clientId = required(clientId, "KROGER_CLIENT_ID");
    this.clientSecret = required(clientSecret, "KROGER_CLIENT_SECRET");
    this.scope = scope;
    this.fetch = fetchImpl;
    this.token = null;
    this.tokenExpiresAt = 0;
  }

  async getToken() {
    if (this.token && Date.now() < this.tokenExpiresAt - 30_000) return this.token;

    const auth = Buffer.from(`${this.clientId}:${this.clientSecret}`).toString("base64");
    const body = new URLSearchParams({ grant_type: "client_credentials", scope: this.scope });
    const response = await this.fetch(TOKEN_URL, {
      method: "POST",
      headers: {
        Authorization: `Basic ${auth}`,
        "Content-Type": "application/x-www-form-urlencoded"
      },
      body
    });

    if (!response.ok) throw new Error(`KROGER_TOKEN_HTTP_${response.status}`);
    const payload = await response.json();
    if (!payload.access_token) throw new Error("KROGER_TOKEN_MISSING");

    this.token = payload.access_token;
    this.tokenExpiresAt = Date.now() + Number(payload.expires_in || 1800) * 1000;
    return this.token;
  }

  async request(path, params = {}) {
    const token = await this.getToken();
    const url = new URL(`${API_BASE}${path}`);
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null && value !== "") url.searchParams.set(key, String(value));
    }

    const response = await this.fetch(url, { headers: { Authorization: `Bearer ${token}`, Accept: "application/json" } });
    if (!response.ok) throw new Error(`KROGER_API_HTTP_${response.status}`);
    return response.json();
  }

  async locationsNearZip(zipCode, limit = 10) {
    required(zipCode, "ZIP_CODE");
    const payload = await this.request("/locations", {
      "filter.zipCode.near": zipCode,
      "filter.limit": Math.max(1, Math.min(Number(limit) || 10, 200))
    });
    return (payload.data || []).map(normalizeLocation);
  }

  async searchProducts({ term, locationId, limit = 10 }) {
    required(term, "PRODUCT_TERM");
    required(locationId, "LOCATION_ID");
    const payload = await this.request("/products", {
      "filter.term": term,
      "filter.locationId": locationId,
      "filter.limit": Math.max(1, Math.min(Number(limit) || 10, 50))
    });
    return (payload.data || []).map(normalizeProduct);
  }

  async compareBasket({ locationId, items }) {
    required(locationId, "LOCATION_ID");
    if (!Array.isArray(items) || items.length === 0) throw new Error("BASKET_ITEMS_REQUIRED");

    const rows = [];
    let total = 0;
    for (const raw of items) {
      const term = typeof raw === "string" ? raw : raw.term;
      const quantity = Math.max(1, Number(typeof raw === "string" ? 1 : raw.quantity) || 1);
      const matches = await this.searchProducts({ term, locationId, limit: 10 });
      const priced = matches.filter(x => x.effectivePrice !== null).sort((a, b) => a.effectivePrice - b.effectivePrice);
      const pick = priced[0] || matches[0] || null;
      const lineTotal = pick?.effectivePrice !== null && pick?.effectivePrice !== undefined
        ? Math.round(pick.effectivePrice * quantity * 100) / 100
        : null;
      if (lineTotal !== null) total += lineTotal;
      rows.push({ term, quantity, pick, lineTotal, alternatives: priced.slice(1, 4) });
    }

    return { locationId, rows, estimatedTotal: Math.round(total * 100) / 100 };
  }
}

export function createClientFromEnv(env = process.env, fetchImpl = globalThis.fetch) {
  return new KrogerClient({
    clientId: env.KROGER_CLIENT_ID,
    clientSecret: env.KROGER_CLIENT_SECRET,
    scope: env.KROGER_SCOPE || "product.compact",
    fetchImpl
  });
}
