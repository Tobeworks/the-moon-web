/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = new Collection({
    name: "linktree_items",
    type: "base",
    fields: [
      {
        name: "type",
        type: "select",
        required: true,
        maxSelect: 1,
        values: ["release", "link"],
      },
      { name: "position",        type: "number", required: true },
      { name: "release_catalog", type: "text",   required: false }, // set when type=release, refs the-moon-os/data/releases.json, not duplicated here
      { name: "label",           type: "text",   required: false }, // set when type=link
      { name: "url",             type: "text",   required: false }, // set when type=link
    ],
    // PocketBase is cluster-internal only — Astro's /api/admin/* routes are the
    // real gate. "" mirrors contracts/split_sheet_releases, not a public API.
    listRule:   "",
    viewRule:   "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
  });
  app.save(collection);
}, (app) => {
  const collection = app.findCollectionByNameOrId("linktree_items");
  app.delete(collection);
});
