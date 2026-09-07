/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  // Skip if already exists
  try { app.findCollectionByNameOrId("split_sheet_releases"); return; } catch (_) {}

  const releases = new Collection({
    name: "split_sheet_releases",
    type: "base",
    fields: [
      { name: "catalog",                type: "text", required: true },  // e.g. "TMR-015", refs the-moon-os/data/releases.json — not duplicated here
      { name: "label_project",          type: "text", required: true },  // e.g. "Logic Moon", "The Moon Records"
      { name: "distribution_platform",  type: "text", required: false }, // free text, e.g. "DistroKid" — no such entity exists yet
      { name: "public_slug",            type: "text", required: true },
      { name: "status",                 type: "text", required: false }, // "draft" | "fully_signed" — plain text like campaigns.status
    ],
    indexes: [
      "CREATE UNIQUE INDEX idx_split_sheet_releases_slug ON split_sheet_releases (public_slug)",
    ],
    // Unauthenticated fetch() from Astro routes is the only way this codebase talks to
    // PocketBase (no superuser token anywhere) — "" here mirrors promos, not a public API.
    listRule:   "",
    viewRule:   "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
  });
  app.save(releases);

  const splits = new Collection({
    name: "splits",
    type: "base",
    fields: [
      {
        name: "release",
        type: "relation",
        required: true,
        collectionId: releases.id,
        cascadeDelete: true,
        maxSelect: 1,
      },
      { name: "artist_name",      type: "text",   required: true },
      { name: "artist_email",     type: "email",  required: false }, // missing -> no auto mail, admin sends the link manually
      { name: "percentage",       type: "number", required: true },
      { name: "role",             type: "text",   required: false }, // e.g. "Songwriting", "Production"
      { name: "signing_token",    type: "text",   required: true },
      { name: "signed_name",      type: "text",   required: false }, // set once, on signing
      { name: "signed_at",        type: "date",   required: false },
      { name: "ip_address",       type: "text",   required: false },
      { name: "document_hash",    type: "text",   required: false },
      { name: "token_expires_at", type: "date",   required: false }, // optional, unset = no expiry
    ],
    indexes: [
      "CREATE UNIQUE INDEX idx_splits_signing_token ON splits (signing_token)",
    ],
    listRule:   "",
    viewRule:   "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
  });
  app.save(splits);
}, (app) => {
  try {
    const splits = app.findCollectionByNameOrId("splits");
    app.delete(splits);
  } catch (_) {}
  try {
    const releases = app.findCollectionByNameOrId("split_sheet_releases");
    app.delete(releases);
  } catch (_) {}
});
