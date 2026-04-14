/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const promos = app.findCollectionByNameOrId("promos");

  const collection = new Collection({
    name: "download_events",
    type: "base",
    fields: [
      {
        name: "promo",
        type: "relation",
        required: true,
        collectionId: promos.id,
        cascadeDelete: false,
        maxSelect: 1,
      },
      {
        name: "quality",
        type: "select",
        required: true,
        maxSelect: 1,
        values: ["128", "320"],
      },
      { name: "user_agent", type: "text", required: false },
      { name: "ip",         type: "text", required: false },
    ],
    listRule:   null,
    viewRule:   null,
    createRule: "",
    updateRule: null,
    deleteRule: null,
  });
  app.save(collection);
}, (app) => {
  const collection = app.findCollectionByNameOrId("download_events");
  app.delete(collection);
});
