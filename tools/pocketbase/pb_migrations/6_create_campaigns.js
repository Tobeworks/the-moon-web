/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = new Collection({
    name: "campaigns",
    type: "base",
    fields: [
      { name: "subject",      type: "text",   required: true },
      { name: "body_html",    type: "text",   required: true },
      { name: "body_md",      type: "text",   required: false },
      { name: "body_text",    type: "text",   required: false },
      { name: "status",       type: "text",   required: false },
      { name: "sent_at",      type: "date",   required: false },
      { name: "sent_count",   type: "number", required: false },
      { name: "failed_count", type: "number", required: false },
    ],
    listRule:   "",
    viewRule:   "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
  });
  app.save(collection);
}, (app) => {
  const collection = app.findCollectionByNameOrId("campaigns");
  app.delete(collection);
});
