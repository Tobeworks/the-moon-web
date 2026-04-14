/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = new Collection({
    name: "newsletter_subscribers",
    type: "base",
    fields: [
      { name: "email",                         type: "email", required: true  },
      { name: "name",                          type: "text",  required: false },
      { name: "confirmed",                     type: "bool",  required: false },
      { name: "confirmation_token",            type: "text",  required: false },
      { name: "confirmation_token_expires_at", type: "date",  required: false },
      { name: "unsubscribe_token",             type: "text",  required: false },
      { name: "confirmed_at",                  type: "date",  required: false },
    ],
    indexes: [
      "CREATE UNIQUE INDEX idx_newsletter_email              ON newsletter_subscribers (email)",
      "CREATE        INDEX idx_newsletter_confirmation_token ON newsletter_subscribers (confirmation_token)",
      "CREATE        INDEX idx_newsletter_unsubscribe_token  ON newsletter_subscribers (unsubscribe_token)",
    ],
    listRule:   "",
    viewRule:   "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
  });
  app.save(collection);
}, (app) => {
  const collection = app.findCollectionByNameOrId("newsletter_subscribers");
  app.delete(collection);
});
