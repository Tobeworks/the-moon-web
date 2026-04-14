/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = new Collection({
    name: "promos",
    type: "base",
    fields: [
      { name: "token",           type: "text",  required: true },
      { name: "release_slug",    type: "text",  required: true },
      { name: "recipient_name",  type: "text",  required: true },
      { name: "recipient_email", type: "email", required: false },
      { name: "notes",           type: "text",  required: false },
      { name: "expires_at",      type: "date",  required: false },
    ],
    indexes: [
      "CREATE UNIQUE INDEX idx_promos_token ON promos (token)"
    ],
    listRule:   "",
    viewRule:   "",
    createRule: null,
    updateRule: null,
    deleteRule: null,
  });
  app.save(collection);
}, (app) => {
  const collection = app.findCollectionByNameOrId("promos");
  app.delete(collection);
});
