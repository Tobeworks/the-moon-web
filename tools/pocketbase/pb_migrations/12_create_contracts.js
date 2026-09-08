/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  // Skip if already exists
  try { app.findCollectionByNameOrId("contract_templates"); return; } catch (_) {}

  const templates = new Collection({
    name: "contract_templates",
    type: "base",
    fields: [
      { name: "name",      type: "text", required: true },  // e.g. "Standard Release Agreement"
      { name: "body_md",   type: "text", required: true },  // Markdown with {{placeholders}}
      { name: "is_active", type: "bool", required: false }, // informational only, not enforced as "only one active"
    ],
    // Unauthenticated fetch() from Astro routes is the only way this codebase talks to
    // PocketBase (no superuser token anywhere) — "" mirrors split_sheet_releases, not a public API.
    listRule:   "",
    viewRule:   "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
  });
  app.save(templates);

  const contracts = new Collection({
    name: "contracts",
    type: "base",
    fields: [
      {
        name: "template",
        type: "relation",
        required: true,
        collectionId: templates.id,
        cascadeDelete: false, // deleting a template must not take existing contracts with it
        maxSelect: 1,
      },
      { name: "catalog",          type: "text",  required: true },  // refs the-moon-os/data/releases.json — not duplicated here
      { name: "artist_name",      type: "text",  required: true },
      { name: "artist_email",     type: "email", required: false }, // missing -> no auto mail, admin sends the link manually
      { name: "rendered_body",    type: "text",  required: true },  // full text at creation time — the legal snapshot, independent of later template edits
      { name: "signing_token",    type: "text",  required: true },
      { name: "signed_name",      type: "text",  required: false }, // set once, on signing
      { name: "signed_at",        type: "date",  required: false },
      { name: "ip_address",       type: "text",  required: false },
      { name: "document_hash",    type: "text",  required: false }, // SHA-256 over rendered_body
      { name: "token_expires_at", type: "date",  required: false }, // optional, unset = no expiry
    ],
    indexes: [
      "CREATE UNIQUE INDEX idx_contracts_signing_token ON contracts (signing_token)",
    ],
    listRule:   "",
    viewRule:   "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
  });
  app.save(contracts);
}, (app) => {
  try {
    const contracts = app.findCollectionByNameOrId("contracts");
    app.delete(contracts);
  } catch (_) {}
  try {
    const templates = app.findCollectionByNameOrId("contract_templates");
    app.delete(templates);
  } catch (_) {}
});
