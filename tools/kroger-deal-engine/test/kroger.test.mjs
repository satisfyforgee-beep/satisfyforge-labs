import test from "node:test";
import assert from "node:assert/strict";
import { KrogerClient, normalizeLocation, normalizeProduct } from "../kroger.mjs";

function response(status, data) {
  return { ok: status >= 200 && status < 300, status, async json() { return data; } };
}

function mockFetch(routes) {
  const calls = [];
  const fetchImpl = async (url, options = {}) => {
    const href = String(url);
    calls.push({ href, options });
    for (const route of routes) {
      if (route.match(href, options)) return response(route.status || 200, route.data);
    }
    return response(404, { error: "not mocked" });
  };
  fetchImpl.calls = calls;
  return fetchImpl;
}

test("normalizes location without leaking unnecessary fields", () => {
  assert.deepEqual(normalizeLocation({
    locationId: "01400458",
    name: "Middletown Kroger",
    chain: "KROGER",
    phone: "555-0100",
    address: { addressLine1: "1 Main St", city: "Middletown", state: "OH", zipCode: "45044" },
    geolocation: { latitude: 39.5, longitude: -84.4 },
    ignored: "secret-ish noise"
  }), {
    locationId: "01400458",
    name: "Middletown Kroger",
    chain: "KROGER",
    phone: "555-0100",
    address: "1 Main St, Middletown, OH, 45044",
    latitude: 39.5,
    longitude: -84.4
  });
});

test("uses promo price when it beats regular price", () => {
  const p = normalizeProduct({
    productId: "p1",
    upc: "111",
    description: "Milk",
    brand: "Kroger",
    items: [{ size: "1 gal", price: { regular: 3.99, promo: 2.99 } }]
  });
  assert.equal(p.effectivePrice, 2.99);
  assert.equal(p.onPromo, true);
});

test("authenticates with client credentials and caches token", async () => {
  const fetchImpl = mockFetch([
    { match: u => u.includes("/connect/oauth2/token"), data: { access_token: "TOKEN", expires_in: 1800 } },
    { match: u => u.includes("/locations?"), data: { data: [] } }
  ]);
  const client = new KrogerClient({ clientId: "id", clientSecret: "secret", fetchImpl });
  await client.locationsNearZip("45044");
  await client.locationsNearZip("45044");
  const tokenCalls = fetchImpl.calls.filter(x => x.href.includes("/connect/oauth2/token"));
  assert.equal(tokenCalls.length, 1);
  assert.match(tokenCalls[0].options.headers.Authorization, /^Basic /);
  assert.equal(String(tokenCalls[0].options.body), "grant_type=client_credentials&scope=product.compact");
});

test("builds location and product filters safely", async () => {
  const fetchImpl = mockFetch([
    { match: u => u.includes("/connect/oauth2/token"), data: { access_token: "TOKEN", expires_in: 1800 } },
    { match: u => u.includes("/locations?"), data: { data: [] } },
    { match: u => u.includes("/products?"), data: { data: [] } }
  ]);
  const client = new KrogerClient({ clientId: "id", clientSecret: "secret", fetchImpl });
  await client.locationsNearZip("45044", 7);
  await client.searchProducts({ locationId: "123", term: "whole milk & eggs", limit: 5 });
  const locationUrl = new URL(fetchImpl.calls.find(x => x.href.includes("/locations?")).href);
  const productUrl = new URL(fetchImpl.calls.find(x => x.href.includes("/products?")).href);
  assert.equal(locationUrl.searchParams.get("filter.zipCode.near"), "45044");
  assert.equal(locationUrl.searchParams.get("filter.limit"), "7");
  assert.equal(productUrl.searchParams.get("filter.locationId"), "123");
  assert.equal(productUrl.searchParams.get("filter.term"), "whole milk & eggs");
  assert.equal(productUrl.searchParams.get("filter.limit"), "5");
});

test("basket picks lowest currently priced match and totals quantities", async () => {
  const fetchImpl = mockFetch([
    { match: u => u.includes("/connect/oauth2/token"), data: { access_token: "TOKEN", expires_in: 1800 } },
    {
      match: u => u.includes("/products?") && decodeURIComponent(u).includes("filter.term=milk"),
      data: { data: [
        { productId: "a", description: "Premium milk", items: [{ price: { regular: 4.29 } }] },
        { productId: "b", description: "Kroger milk", items: [{ price: { regular: 3.49, promo: 2.99 } }] }
      ] }
    },
    {
      match: u => u.includes("/products?") && decodeURIComponent(u).includes("filter.term=eggs"),
      data: { data: [{ productId: "e", description: "Eggs", items: [{ price: { regular: 2.49 } }] }] }
    }
  ]);
  const client = new KrogerClient({ clientId: "id", clientSecret: "secret", fetchImpl });
  const result = await client.compareBasket({ locationId: "123", items: [{ term: "milk", quantity: 2 }, "eggs"] });
  assert.equal(result.rows[0].pick.productId, "b");
  assert.equal(result.rows[0].lineTotal, 5.98);
  assert.equal(result.rows[1].lineTotal, 2.49);
  assert.equal(result.estimatedTotal, 8.47);
});

test("rejects missing credentials and empty baskets", async () => {
  assert.throws(() => new KrogerClient({ clientId: "", clientSecret: "x", fetchImpl: async () => {} }), /KROGER_CLIENT_ID_REQUIRED/);
  const client = new KrogerClient({ clientId: "id", clientSecret: "secret", fetchImpl: async () => response(200, {}) });
  await assert.rejects(() => client.compareBasket({ locationId: "123", items: [] }), /BASKET_ITEMS_REQUIRED/);
});
