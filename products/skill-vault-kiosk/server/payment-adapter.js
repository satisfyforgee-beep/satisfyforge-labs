// Intentionally disabled production boundary.
// A future approved provider adapter must return a normalized authorization record
// and must never expose or store raw card data inside Skill Vault.
async function authorizePaidSession({authorizationId,idempotencyKey,amountCents}){
  void authorizationId; void idempotencyKey; void amountCents;
  const err=new Error('payment_adapter_not_configured');
  err.code='payment_adapter_not_configured';
  throw err;
}
module.exports={authorizePaidSession};
