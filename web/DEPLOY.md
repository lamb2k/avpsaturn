# Deploy: avp.retronetplay.com

Private test site on the owner's Cloudflare account. Worker and R2 bucket are both `avp-private-test`. Wrangler 4.131.1. Nothing is shared with the halo-dce Worker or bucket.

## Access

Open: no password or sign-in (owner: "Open is fine"). Anyone with the URL can load the page, core and image. The bucket itself has no public access; the Worker serves it. `/files` is limited to 120 requests a minute per address, per Worker instance. Image parts are cached for a year because their names carry a hash; the page also keeps one verified copy in the browser.

## Status

Not deployed yet: the upload was refused by a permission check. See the hand-back.

## Publish a new image

The image goes up as parts, since `wrangler r2 object put` stops near 315 MB. The page joins them and checks the whole file's SHA-256 against `build.json`.

    bash make-image.sh CUE DIR LABEL COMMIT
    python split-image.py DIR/game.chd DIR/parts       # writes parts and parts/build.json
    # for each part, then build.json last:
    npx wrangler@4.131.1 r2 object put avp-private-test/NAME --file=PATH --remote

## Publish the page or core

    bash stage-site.sh EJS_CHECKOUT CORE_DATA_FILE GPL2_TEXT
    npx wrangler@4.131.1 deploy

A rebuilt core also changes its pin in `public/runtime-config.mjs`.

## Rollback

- Previous page or Worker: `npx wrangler@4.131.1 deployments list`, then `npx wrangler@4.131.1 rollback VERSION_ID`.
- Previous image: put the old parts and old `build.json` back; put `build.json` last.
- **Take the site down**, keeping data: `npx wrangler@4.131.1 delete` removes the Worker and its custom domain. The bucket has no public access, so the data is then unreachable.
- Remove the data too: delete each object with `npx wrangler@4.131.1 r2 object delete avp-private-test/NAME --remote`, then `npx wrangler@4.131.1 r2 bucket delete avp-private-test`.
