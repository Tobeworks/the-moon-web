/// <reference path="../pb_data/types.d.ts" />
// PocketBase runs cluster-internal only — Astro API routes are the security layer.
// These collections need list/view access for server-side operations (subscribe, confirm, unsubscribe).
migrate((app) => {
  for (const name of ['newsletter_subscribers', 'promo_subscribers', 'campaigns']) {
    const col = app.findCollectionByNameOrId(name);
    col.listRule   = "";
    col.viewRule   = "";
    col.updateRule = "";
    col.deleteRule = "";
    app.save(col);
  }
}, (app) => {
  for (const name of ['newsletter_subscribers', 'promo_subscribers', 'campaigns']) {
    const col = app.findCollectionByNameOrId(name);
    col.listRule   = null;
    col.viewRule   = null;
    col.updateRule = null;
    col.deleteRule = null;
    app.save(col);
  }
});
