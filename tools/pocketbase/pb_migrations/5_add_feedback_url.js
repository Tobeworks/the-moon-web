/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = app.findCollectionByNameOrId("feedback");
  const field = new Field({ name: "url", type: "url", required: false });
  collection.fields.add(field);
  app.save(collection);
}, (app) => {
  const collection = app.findCollectionByNameOrId("feedback");
  collection.fields.removeByName("url");
  app.save(collection);
});
