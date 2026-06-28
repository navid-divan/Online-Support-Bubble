# Online Support Bubble — Web edition (GUI)

A complete, self-contained **web application** for the Online Support Bubble system. It runs the
whole protocol as an **in-browser simulation** — there is no backend and nothing is sent anywhere.
It is fully separate from the terminal build in the parent `osb/` directory, including its own
time/space logs.

> This is a UI/UX prototype. For clarity and offline use it simulates the protocol's *behaviour*
> (unlinkable per-bubble keys, attribute-based selection, encrypted messaging, Registrar+Tracer
> tracing). The real BLS12-381 cryptography lives in the terminal build.

## Run it

It is plain HTML/CSS/JavaScript with **no dependencies and no build step**.

- **Simplest:** double-click `index.html` (or open it in any browser).
- **Or serve it** (recommended) from this `GUI/` directory:

  ```bash
  ./serve.sh
  # then open http://localhost:8000
  ```

`index.html` is the formal home page; the **Open the app** button takes you to `app.html`, the
dashboards.

## What's inside

- **`index.html`** — landing page: the services, features, and the five role dashboards, with a
  button into the app.
- **`app.html`** — the dashboard application. The tab bar switches **instantly** between roles:
  - **Overview** — system stats, the bubble flow, an attribute glossary, and a one-click demo.
  - **Subject** — build a bubble from an attribute policy (presets or a custom AND/OR builder),
    message advisors, replace/remove/close, and see each member's per-bubble unlinkable key.
  - **Advisor** — availability, invitations, join, advise, and a "your unlinkable identities" view
    showing a different derived key per bubble. (Pick which advisor via *Viewing as*.)
  - **Registrar** — **onboard new subjects and advisors**, the identity register, the **blacklist
    (ban/unban)**, and judging a revocation token to an identity.
  - **Tracer** — trace a member to an anonymous revocation token; the anonymous join registry.
  - **Ledger / Server** — the append-only store of unlinkable keys; token accounting.
  - **Logs** — the web app's own `time_log` and `space_log`, viewable and downloadable.

You can build the whole world yourself from the **Registrar** tab (register people), then act as
them from the Subject/Advisor tabs — no authentication required in this edition.
- **`assets/js/osb-core.js`** — the simulated engine (state, protocol operations, profiler, seed).
- **`assets/js/app.js`** — the dashboard UI.
- **`assets/css/styles.css`** — the design system.

Sample users are seeded automatically (subject **Emma Clarke**, advisors **Dr. Martin Walker**,
**Dr. Sofia Reyes**, **Sarah Bennett**, **Diane Marsh**, **James Okonkwo**, **Dr. Aisha Khan**,
**Tom Fielding**), so every dashboard has data the moment you open it. No sign-up or sign-in.

## Separate logs

Open the **Logs** tab to see the web edition's `time_log` (milliseconds per operation) and
`space_log` (state-footprint growth per operation), and download them. They are independent of the
terminal build's pairing-based logs and reset on reload or **Reset**.
