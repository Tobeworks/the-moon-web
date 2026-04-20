/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  // Skip if already exists
  try { app.findCollectionByNameOrId("promo_subscribers"); return; } catch (_) {}

  const collection = new Collection({
    name: "promo_subscribers",
    type: "base",
    fields: [
      { name: "email",             type: "email", required: true },
      { name: "name",              type: "text",  required: false },
      { name: "unsubscribe_token", type: "text",  required: true },
    ],
    indexes: [
      "CREATE UNIQUE INDEX idx_promo_subscribers_email ON promo_subscribers (email)",
      "CREATE INDEX idx_promo_subscribers_token ON promo_subscribers (unsubscribe_token)",
    ],
    listRule:   null,
    viewRule:   null,
    createRule: "",
    updateRule: null,
    deleteRule: null,
  });
  app.save(collection);
}, (app) => {
  try {
    const collection = app.findCollectionByNameOrId("promo_subscribers");
    app.delete(collection);
  } catch (_) {}
});
