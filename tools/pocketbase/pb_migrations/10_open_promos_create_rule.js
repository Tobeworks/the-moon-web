/// <reference path="../pb_data/types.d.ts" />

// Allow server-side creation of promo records (Astro API routes are the auth layer).
// PocketBase is not exposed externally, so opening createRule is safe.
migrate(
  (app) => {
    const collection = app.findCollectionByNameOrId('promos');
    collection.createRule = '';
    app.save(collection);
  },
  (app) => {
    const collection = app.findCollectionByNameOrId('promos');
    collection.createRule = null;
    app.save(collection);
  }
);
