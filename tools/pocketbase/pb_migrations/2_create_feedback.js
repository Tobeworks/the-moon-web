/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const promos = app.findCollectionByNameOrId("promos");

  const collection = new Collection({
    name: "feedback",
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
      { name: "name",       type: "text",  required: true },
      { name: "email",      type: "email", required: true },
      { name: "comment",    type: "text",  required: true },
      { name: "user_agent", type: "text",  required: false },
      { name: "ip",         type: "text",  required: false },
    ],
    listRule:   "",
    viewRule:   "",
    createRule: "",
    updateRule: null,
    deleteRule: null,
  });
  app.save(collection);
}, (app) => {
  const collection = app.findCollectionByNameOrId("feedback");
  app.delete(collection);
});
