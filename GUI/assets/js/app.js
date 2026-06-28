const App = (function () {
  const ui = {
    view: "overview",
    subject: "emma",
    advisor: "walker",
    bubble: null,
    policy: [["cancer_specialist"], ["legal_advisor"]],
    reg: { sHandle: "", sName: "", sBio: "", aHandle: "", aName: "", aBio: "", aAttrs: [] },
  };

  const TABS = [
    ["overview", "Overview", "▦"],
    ["subject", "Subject", "🙋"],
    ["advisor", "Advisor", "🩺"],
    ["registrar", "Registrar", "🗂"],
    ["tracer", "Tracer", "🔎"],
    ["ledger", "Ledger", "▤"],
    ["logs", "Logs", "⏱"],
  ];

  const PRESETS = [
    ["Cancer + legal", [["cancer_specialist"], ["legal_advisor"]]],
    ["Mental-health support", [["mental_health_specialist"], ["peer_survivor"]]],
    ["Doctor + finance", [["medical_doctor"], ["financial_specialist"]]],
    ["Senior specialist", [["cancer_specialist", "medical_doctor", "mental_health_specialist"], ["experience_gt_5y", "experience_gt_10y"]]],
  ];

  const S = () => OSB.state();
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  function hue(s) {
    let h = 0;
    for (const c of String(s)) h = (h * 31 + c.charCodeAt(0)) % 360;
    return h;
  }
  function initials(name) {
    const w = String(name).replace(/dr\.?/i, "").trim().split(/\s+/);
    return ((w[0] || "?")[0] + (w.length > 1 ? w[w.length - 1][0] : "")).toUpperCase();
  }
  function avatar(u) {
    return `<span class="av" style="background:hsl(${hue(u.handle)} 52% 47%)">${esc(initials(u.name))}</span>`;
  }
  function person(u, sub) {
    return `<div class="person">${avatar(u)}<div class="nm">${esc(u.name)}<small>${esc(sub || u.bio || u.handle)}</small></div></div>`;
  }
  function attrChips(attrs) {
    return `<div class="chips">${attrs.map((a) => `<span class="chip read">${esc(OSB.label(a))}</span>`).join("")}</div>`;
  }
  function dpk(key) {
    return `<span class="dpk-pill">⚷ ${esc(key.slice(0, 14))}…</span>`;
  }
  function subjects() {
    return S().order.map((h) => S().users[h]).filter((u) => u.role === "subject");
  }
  function advisors() {
    return S().order.map((h) => S().users[h]).filter((u) => u.role === "advisor");
  }
  function ownedBubbles(handle) {
    return Object.values(S().bubbles).filter((b) => b.owner === handle);
  }

  function toast(msg, kind) {
    const wrap = document.getElementById("toasts");
    const el = document.createElement("div");
    el.className = "toast " + (kind || "");
    el.innerHTML = `<span>${kind === "err" ? "⚠" : "✓"}</span><span>${esc(msg)}</span>`;
    wrap.appendChild(el);
    setTimeout(() => el.remove(), 3200);
  }
  function act(fn, okMsg) {
    try {
      fn();
      if (okMsg) toast(okMsg, "ok");
    } catch (e) {
      toast(e.message, "err");
    }
    render();
  }
  function download(name, text) {
    const blob = new Blob([text], { type: "text/plain" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = name;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  function render() {
    renderTabs();
    renderActor();
    const m = document.getElementById("main");
    const views = { overview: renderOverview, subject: renderSubject, advisor: renderAdvisor, registrar: renderRegistrar, tracer: renderTracer, ledger: renderLedger, logs: renderLogs };
    m.innerHTML = (views[ui.view] || renderOverview)();
    m.scrollTop = 0;
  }

  function renderTabs() {
    document.getElementById("tabs").innerHTML = TABS.map(
      ([id, label, ic]) => `<button class="tab ${ui.view === id ? "active" : ""}" data-act="nav" data-view="${id}"><span>${ic}</span>${label}</button>`
    ).join("");
  }

  function renderActor() {
    const area = document.getElementById("actor-area");
    if (ui.view === "subject") {
      const opts = subjects().map((u) => `<option value="${u.handle}" ${u.handle === ui.subject ? "selected" : ""}>${esc(u.name)} (${u.handle})</option>`).join("");
      area.innerHTML = opts ? `<div class="actor-picker"><label>Viewing as</label><select id="actor-select" data-role="subject">${opts}</select></div>` : "";
    } else if (ui.view === "advisor") {
      const opts = advisors().map((u) => `<option value="${u.handle}" ${u.handle === ui.advisor ? "selected" : ""}>${esc(u.name)} (${u.handle})</option>`).join("");
      area.innerHTML = opts ? `<div class="actor-picker"><label>Viewing as</label><select id="actor-select" data-role="advisor">${opts}</select></div>` : "";
    } else {
      area.innerHTML = "";
    }
  }

  function head(title, sub) {
    return `<div class="page-head"><div><h1>${title}</h1><p>${sub}</p></div></div>`;
  }
  function empty(ic, text) {
    return `<div class="empty"><div class="ic">${ic}</div><p>${text}</p></div>`;
  }

  function renderOverview() {
    const st = S();
    const nMsg = Object.values(st.bubbles).reduce((s, b) => s + b.messages.length, 0);
    const open = Object.values(st.bubbles).filter((b) => !b.closed).length;
    const stat = (k, v, ic) => `<div class="stat"><span class="ic">${ic}</span><div class="k">${k}</div><div class="v">${v}</div></div>`;
    const recent = st.ledger.slice(-6).reverse();
    return (
      head("System overview", "A live, self-contained simulation of the Online Support Bubble protocol. Switch roles from the tabs above.") +
      `<div class="grid cols-4">
        ${stat("Registered users", st.order.length, "👥")}
        ${stat("Advisors", advisors().length, "🩺")}
        ${stat("Open bubbles", open, "🫧")}
        ${stat("Messages sent", nMsg, "✉️")}
      </div>
      <div style="height:18px"></div>
      <div class="grid side">
        <div class="card"><div class="hd"><h3>How a bubble works</h3></div><div class="bd">
          <div class="flow"><div class="node">🙋 Subject</div><span class="arrow">→</span><div class="node">policy Ψ</div><span class="arrow">→</span><div class="node">🩺 Advisors</div></div>
          <div style="height:12px"></div>
          <div class="flow"><div class="node">🗂 Registrar</div><span class="arrow">+</span><div class="node">🔎 Tracer</div><span class="arrow">→</span><div class="node">accountable tracing</div></div>
          <div style="height:14px"></div>
          <div class="callout teal"><span>🔒</span><span>Every membership uses a fresh, unlinkable key. The ledger never sees a real name; only the Registrar and Tracer <b>together</b> can de-anonymise a member.</span></div>
          <div style="height:14px"></div>
          <button class="btn primary" data-act="rundemo">▶ Run a demo scenario</button>
        </div></div>
        <div>
          <div class="card"><div class="hd"><h3>Recent ledger activity</h3><span class="sub">${st.ledger.length} entries</span></div><div class="bd tight">
            ${recent.length ? `<table><tbody>${recent.map((e) => `<tr><td class="mono">#${e.hl}</td><td><span class="tag ${e.kind === "group" ? "" : "teal"}">${e.kind}</span></td><td>${esc(e.detail)}${e.closed ? ' <span class="tag rose">closed</span>' : ""}</td></tr>`).join("")}</tbody></table>` : empty("▤", "No ledger activity yet.")}
          </div></div>
          <div style="height:18px"></div>
          <div class="card"><div class="hd"><h3>Advisor attributes</h3><span class="sub">${OSB.ATTRIBUTES.length}</span></div><div class="bd">${attrChips(OSB.ATTRIBUTES)}</div></div>
        </div>
      </div>`
    );
  }

  function policyBuilder() {
    const all = OSB.ATTRIBUTES;
    const presets = PRESETS.map(([name], i) => `<span class="preset" data-act="preset" data-i="${i}">${esc(name)}</span>`).join("");
    const clauses = ui.policy
      .map((clause, ci) => {
        const chips = all.map((a) => `<span class="chip ${clause.includes(a) ? "on" : ""}" data-act="chip" data-clause="${ci}" data-attr="${a}">${esc(OSB.label(a))}</span>`).join("");
        const del = ui.policy.length > 1 ? `<button class="btn tiny ghost" data-act="clause-del" data-clause="${ci}">remove</button>` : "";
        return `<div class="clause"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:9px"><b style="font-size:.82rem;color:var(--muted)">Requirement ${ci + 1} &mdash; any one of:</b>${del}</div><div class="chips">${chips}</div></div>`;
      })
      .join('<div class="or-and">AND</div>');
    return `<div class="presets">${presets}</div>${clauses}
      <div style="display:flex;gap:10px;margin-top:14px;flex-wrap:wrap">
        <button class="btn ghost" data-act="clause-add">+ Add requirement</button>
        <button class="btn primary" data-act="create-bubble">Create support bubble</button>
      </div>`;
  }

  function pickSubject() {
    let u = S().users[ui.subject];
    if (!u || u.role !== "subject") {
      const s = subjects()[0];
      if (!s) return null;
      ui.subject = s.handle;
      u = s;
    }
    return u;
  }

  function renderSubject() {
    const u = pickSubject();
    if (!u) return head("Subject dashboard", "") + empty("🙋", "No subjects yet. Onboard one from the Registrar tab.");
    const bubbles = ownedBubbles(u.handle);
    const open = ui.bubble && S().bubbles[ui.bubble] && S().bubbles[ui.bubble].owner === u.handle ? S().bubbles[ui.bubble] : null;
    return (
      head("Subject dashboard", `Acting as <b>${esc(u.name)}</b> &mdash; choose advisors by attribute, form a private bubble, and message them.`) +
      `<div class="grid side">
        <div class="card"><div class="hd"><h3>Create a support bubble</h3></div><div class="bd">
          <p class="muted-note" style="margin-bottom:14px">Pick the kind of advisor you need, or start from a preset. The bubble forms only if every requirement can be met by an available advisor.</p>
          ${policyBuilder()}
          <div style="height:10px"></div>
          <div class="callout"><span>ℹ️</span><span>Authorisation tokens left: <b>${u.tokens}</b>. Each new bubble spends one.</span></div>
        </div></div>
        <div>
          <div class="card"><div class="hd"><h3>Your bubbles</h3><span class="sub">${bubbles.length} total</span></div><div class="bd tight">
            ${bubbles.length ? bubbles.map((b) => bubbleRow(b)).join("") : empty("🫧", "No bubbles yet &mdash; create one on the left.")}
          </div></div>
          ${open ? `<div style="height:18px"></div>${bubbleDetail(open, u.handle, true)}` : ""}
        </div>
      </div>`
    );
  }

  function bubbleRow(b) {
    const names = b.members.map((m) => esc(S().users[m.handle].name.split(" ").slice(-1)[0])).join(", ");
    const active = ui.bubble === b.id;
    return `<div class="list-row" style="${active ? "border-color:var(--primary)" : ""}"><div class="grow"><b>${b.id}</b> ${b.closed ? '<span class="tag rose">closed</span>' : '<span class="tag teal">open</span>'}<div style="color:var(--muted);font-size:.82rem;margin-top:3px">members: ${names}</div></div><button class="btn soft tiny" data-act="open-bubble" data-bubble="${b.id}">${active ? "Viewing" : "Open"}</button></div>`;
  }

  function bubbleDetail(b, owner, asSubject) {
    return `<div class="card"><div class="hd"><h3>Bubble ${b.id}</h3><span class="sub">${b.members.length} member(s)${b.closed ? " · closed" : ""}</span></div><div class="bd">
      <div class="grid cols-2">
        <div>
          <b style="font-size:.82rem;color:var(--muted)">MEMBERS &amp; INVITES</b>
          <div style="margin-top:10px">${memberList(b, owner, asSubject)}</div>
        </div>
        <div>
          <b style="font-size:.82rem;color:var(--muted)">MESSAGES</b>
          ${messaging(b, owner)}
        </div>
      </div>
      <div class="callout teal" style="margin-top:14px"><span>⚷</span><span>Each member's key above is derived only for this bubble &mdash; the same person carries a different, unlinkable key in every bubble.</span></div>
      ${asSubject && !b.closed ? `<div style="display:flex;gap:10px;margin-top:14px"><button class="btn danger tiny" data-act="close-bubble" data-bubble="${b.id}">Close bubble</button></div>` : ""}
    </div></div>`;
  }

  function memberList(b, owner, asSubject) {
    const joined = b.members.map((m) => m.handle);
    const sub = S().users[owner];
    const subDpk = (b.members.find((m) => m.handle === owner) || {}).dpk || "";
    const subRow = `<div class="list-row">${person(sub)}<div class="grow">${subDpk ? dpk(subDpk) : ""}</div><span class="tag">owner</span></div>`;
    const rows = b.offers.map((o) => {
      const u = S().users[o.handle];
      const isIn = joined.includes(o.handle);
      const ctrl = asSubject && !b.closed
        ? `<button class="btn ghost tiny" data-act="remove-adv" data-bubble="${b.id}" data-advisor="${o.handle}">remove</button> <button class="btn ghost tiny" data-act="replace-adv" data-bubble="${b.id}" data-advisor="${o.handle}">replace</button>`
        : "";
      return `<div class="list-row">${person(u)}<div class="grow">${dpk(o.dapk)}</div>${isIn ? '<span class="tag teal"><span class="dot"></span>joined</span>' : '<span class="tag amber">invited</span>'} ${ctrl}</div>`;
    });
    return subRow + rows.join("");
  }

  function messaging(b, who) {
    const thread = b.messages.length
      ? `<div class="thread">${b.messages.map((m) => `<div class="msg ${m.from === who ? "me" : "them"}"><div class="from">${esc(S().users[m.from].name.split(" ").slice(-1)[0])}</div>${esc(m.text)}</div>`).join("")}</div>`
      : empty("✉️", "No messages yet.");
    const composer = !b.closed
      ? `<div class="composer"><input type="text" id="composer" placeholder="Write an encrypted message…" data-bubble="${b.id}" /><button class="btn primary" data-act="send" data-bubble="${b.id}" data-from="${who}">Send</button></div>`
      : "";
    return `<div style="margin-top:10px">${thread}${composer}</div>`;
  }

  function renderAdvisor() {
    let u = S().users[ui.advisor];
    if (!u || u.role !== "advisor") {
      const a = advisors()[0];
      if (!a) return head("Advisor dashboard", "") + empty("🩺", "No advisors yet. Onboard one from the Registrar tab.");
      ui.advisor = a.handle;
      u = a;
    }
    const banned = OSB.isBanned(u.handle);
    const all = Object.values(S().bubbles);
    const invites = all.filter((b) => b.offers.some((o) => o.handle === u.handle));
    const memberships = all.filter((b) => b.members.some((m) => m.handle === u.handle));
    const open = ui.bubble && S().bubbles[ui.bubble] && S().bubbles[ui.bubble].members.some((m) => m.handle === u.handle) ? S().bubbles[ui.bubble] : null;
    return (
      head("Advisor dashboard", `Acting as <b>${esc(u.name)}</b> &mdash; review invitations, join bubbles, and advise.`) +
      `<div class="grid side">
        <div>
          <div class="card"><div class="hd"><h3>Your profile</h3>${banned ? '<span class="tag rose">banned</span>' : ""}</div><div class="bd">
            ${person(u, u.bio)}
            <div style="height:14px"></div>${attrChips(u.attrs)}
            <div style="height:16px"></div>
            <div class="list-row"><div class="grow"><b>Availability</b><div class="muted-note">Unavailable advisors are skipped during selection.</div></div>
            <button class="btn ${u.available ? "soft" : "ghost"} tiny" data-act="toggle-avail" data-advisor="${u.handle}">${u.available ? "● Available" : "○ Unavailable"}</button></div>
            <div style="height:14px"></div>
            <div class="callout"><span>🔑</span><span>Tokens left: <b>${u.tokens}</b> &mdash; one is spent each time you join a bubble.</span></div>
          </div></div>
          ${memberships.length ? `<div style="height:18px"></div><div class="card"><div class="hd"><h3>Your unlinkable identities</h3></div><div class="bd">
            <p class="muted-note" style="margin-bottom:10px">You are the same advisor, yet each bubble sees a different derived key. No one can link these.</p>
            ${memberships.map((b) => `<div class="list-row"><div class="grow"><b>${b.id}</b></div>${dpk((b.members.find((m) => m.handle === u.handle) || {}).dpk || "")}</div>`).join("")}
          </div></div>` : ""}
        </div>
        <div>
          <div class="card"><div class="hd"><h3>Invitations</h3><span class="sub">${invites.length}</span></div><div class="bd tight">
            ${invites.length ? invites.map((b) => inviteRow(b, u.handle)).join("") : empty("📭", "No invitations yet. Open a bubble as a Subject and invite this advisor.")}
          </div></div>
          ${open ? `<div style="height:18px"></div><div class="card"><div class="hd"><h3>Bubble ${open.id}</h3><span class="sub">${open.members.length} members</span></div><div class="bd">${messaging(open, u.handle)}</div></div>` : ""}
        </div>
      </div>`
    );
  }

  function inviteRow(b, handle) {
    const joined = b.members.some((m) => m.handle === handle);
    const owner = S().users[b.owner];
    return `<div class="list-row"><div class="grow"><b>${b.id}</b> ${b.closed ? '<span class="tag rose">closed</span>' : ""}<div style="color:var(--muted);font-size:.82rem;margin-top:3px">from ${esc(owner.name)}</div></div>${
      joined ? `<button class="btn soft tiny" data-act="open-bubble" data-bubble="${b.id}">Open</button>` : b.closed ? "" : `<button class="btn primary tiny" data-act="join" data-bubble="${b.id}" data-advisor="${handle}">Join</button>`
    }</div>`;
  }

  function registerForms() {
    const r = ui.reg;
    const chips = OSB.ATTRIBUTES.map((a) => `<span class="chip ${r.aAttrs.includes(a) ? "on" : ""}" data-act="reg-chip" data-attr="${a}">${esc(OSB.label(a))}</span>`).join("");
    return `<div class="grid cols-2">
      <div class="card"><div class="hd"><h3>Onboard a subject</h3><span class="sub">a help-seeker</span></div><div class="bd">
        <div class="field"><label>Full name</label><input type="text" data-reg="sName" value="${esc(r.sName)}" placeholder="e.g. John Rivers" /></div>
        <div class="field"><label>Handle (optional)</label><input type="text" data-reg="sHandle" value="${esc(r.sHandle)}" placeholder="auto-generated from name" /></div>
        <div class="field"><label>Note (optional)</label><input type="text" data-reg="sBio" value="${esc(r.sBio)}" placeholder="e.g. seeking advice on a diagnosis" /></div>
        <button class="btn primary" data-act="reg-subject">Register subject</button>
      </div></div>
      <div class="card"><div class="hd"><h3>Onboard an advisor</h3><span class="sub">a qualified helper</span></div><div class="bd">
        <div class="field"><label>Full name</label><input type="text" data-reg="aName" value="${esc(r.aName)}" placeholder="e.g. Dr. Lena Park" /></div>
        <div class="field"><label>Handle (optional)</label><input type="text" data-reg="aHandle" value="${esc(r.aHandle)}" placeholder="auto-generated from name" /></div>
        <div class="field"><label>Specialty / note (optional)</label><input type="text" data-reg="aBio" value="${esc(r.aBio)}" placeholder="e.g. cardiologist, 12 years" /></div>
        <div class="field"><label>Attributes (pick at least one)</label><div class="chips">${chips}</div></div>
        <button class="btn primary" data-act="reg-advisor">Register advisor</button>
      </div></div>
    </div>`;
  }

  function renderRegistrar() {
    const st = S();
    const rows = st.order.map((h) => st.users[h]).map((u) => {
      const banned = OSB.isBanned(u.handle);
      return `<tr style="${banned ? "opacity:.5" : ""}"><td>${person(u)}</td><td><span class="tag ${u.role === "subject" ? "amber" : ""}">${u.role}</span>${banned ? ' <span class="tag rose">banned</span>' : ""}</td><td>${u.attrs.length ? attrChips(u.attrs) : '<span class="mono">—</span>'}</td><td class="mono">${u.cpk}</td><td><button class="btn ${banned ? "soft" : "danger"} tiny" data-act="ban" data-handle="${u.handle}" data-on="${banned ? "0" : "1"}">${banned ? "unban" : "ban"}</button></td></tr>`;
    }).join("");
    const traced = st.traced;
    return (
      head("Registrar dashboard", "Onboards users, maintains the blacklist, and holds the only map from a revocation token to a real identity.") +
      registerForms() +
      `<div style="height:18px"></div>
      <div class="grid side">
        <div class="card"><div class="hd"><h3>Judge a revocation token</h3></div><div class="bd">
          <div class="callout amber"><span>⚖️</span><span>The Tracer produces a revocation token (cpk) from a signature. Only the Registrar can map it to an identity &mdash; the two must cooperate.</span></div>
          <div style="height:14px"></div>
          ${traced.length ? traced.map((t) => `<div class="list-row"><div class="grow"><div class="mono">${t.cpk}</div><div style="color:var(--muted);font-size:.78rem">traced from bubble ${t.bubble}</div></div><button class="btn primary tiny" data-act="judge" data-cpk="${t.cpk}">Identify</button></div>`).join("") : empty("🔏", "No tokens to judge yet. Use the Tracer to trace a member first.")}
        </div></div>
        <div class="card"><div class="hd"><h3>Identity register (uL) &amp; blacklist</h3><span class="sub">${st.order.length} users</span></div><div class="bd tight">
          <table><thead><tr><th>User</th><th>Role</th><th>Attributes</th><th>Revocation token</th><th>Manage</th></tr></thead><tbody>${rows}</tbody></table>
        </div></div>
      </div>`
    );
  }

  function renderTracer() {
    const st = S();
    const memberOptions = [];
    Object.values(st.bubbles).forEach((b) => b.members.forEach((m) => memberOptions.push({ b: b.id, h: m.handle })));
    const opts = memberOptions.length ? memberOptions.map((o) => `<option value="${o.b}|${o.h}">${o.b} &mdash; ${esc(st.users[o.h].name)}</option>`).join("") : `<option value="">no members yet</option>`;
    const last = st.traced[st.traced.length - 1];
    return (
      head("Tracer dashboard", "Holds the group-signature trace key. Can map a misbehaving member to a revocation token &mdash; but not to a real name.") +
      `<div class="grid side">
        <div class="card"><div class="hd"><h3>Trace a member</h3></div><div class="bd">
          <label style="font-size:.82rem;color:var(--muted);font-weight:600">Pick a bubble member</label>
          <div style="display:flex;gap:10px;margin-top:8px"><select id="trace-select" style="flex:1">${opts}</select><button class="btn primary" data-act="trace-pick" ${memberOptions.length ? "" : "disabled"}>Trace</button></div>
          <div style="height:14px"></div>
          <div class="callout teal"><span>🔎</span><span>Tracing reveals a <b>revocation token</b> and revokes the member. To learn <i>who</i> they are, hand the token to the Registrar.</span></div>
          ${last ? `<div style="height:14px"></div><div class="kv"><div class="k">last trace</div><div>bubble ${last.bubble}</div><div class="k">derived key</div><div class="mono">${esc(last.dpk)}</div><div class="k">→ token (cpk)</div><div class="mono">${esc(last.cpk)}</div></div>` : ""}
        </div></div>
        <div class="card"><div class="hd"><h3>Anonymous join registry</h3><span class="sub">${st.registry.length}</span></div><div class="bd tight">
          <table><thead><tr><th>Random r</th><th>Revocation token (cpk)</th><th>Status</th></tr></thead><tbody>
          ${st.registry.map((x) => `<tr><td class="mono">${x.r}</td><td class="mono">${x.cpk}</td><td>${st.revoked.includes(x.cpk) ? '<span class="tag rose">revoked</span>' : '<span class="tag gray">active</span>'}</td></tr>`).join("")}
          </tbody></table>
        </div></div>
      </div>`
    );
  }

  function renderLedger() {
    const st = S();
    return (
      head("Ledger / Server dashboard", "The centralized server that replaces the paper's blockchain. It only ever stores unlinkable keys, never identities.") +
      `<div class="grid cols-3">
        <div class="stat"><span class="ic">▤</span><div class="k">Ledger entries</div><div class="v">${st.ledger.length}</div></div>
        <div class="stat"><span class="ic">🎟</span><div class="k">Tokens issued</div><div class="v">${st.tokens.issued}</div></div>
        <div class="stat"><span class="ic">✅</span><div class="k">Tokens spent</div><div class="v">${st.tokens.spent}</div></div>
      </div>
      <div style="height:18px"></div>
      <div class="card"><div class="hd"><h3>Public ledger</h3><span class="sub">append-only; tokens authorise every write</span></div><div class="bd tight">
        ${st.ledger.length ? `<table><thead><tr><th>hl</th><th>Kind</th><th>Bubble</th><th>Derived key (unlinkable)</th><th>Detail</th></tr></thead><tbody>${st.ledger.map((e) => `<tr><td class="mono">#${e.hl}</td><td><span class="tag ${e.kind === "group" ? "" : "teal"}">${e.kind}</span></td><td class="mono">${e.bubble}</td><td class="mono">${e.dpk}</td><td>${esc(e.detail)}${e.closed ? ' <span class="tag rose">closed</span>' : ""}</td></tr>`).join("")}</tbody></table>` : empty("▤", "The ledger is empty.")}
      </div></div>`
    );
  }

  function renderLogs() {
    return (
      head("Profiler &mdash; time &amp; space logs", "The web app keeps its own logs, separate from the terminal build. They reset on reload or Reset.") +
      `<div class="grid cols-2">
        <div class="card"><div class="hd"><h3>time_log</h3><button class="btn soft tiny" data-act="dl-time">Download</button></div><div class="bd"><pre class="log">${esc(OSB.timeLog())}</pre></div></div>
        <div class="card"><div class="hd"><h3>space_log</h3><button class="btn soft tiny" data-act="dl-space">Download</button></div><div class="bd"><pre class="log">${esc(OSB.spaceLog())}</pre></div></div>
      </div>
      <div style="height:16px"></div>
      <div class="callout"><span>⏱</span><span>Web timings are milliseconds of the in-browser simulation (no pairing crypto), and space is the state-footprint growth per operation &mdash; the terminal build measures real BLS12-381 work instead.</span></div>`
    );
  }

  function readPolicy() {
    return ui.policy.map((c) => c.slice()).filter((c) => c.length);
  }

  function handlers(t) {
    const a = t.getAttribute("data-act");
    if (a === "nav") { ui.view = t.getAttribute("data-view"); ui.bubble = null; return render(); }
    if (a === "reset") return act(() => { OSB.reset(true); ui.bubble = null; ui.subject = "emma"; ui.advisor = "walker"; ui.policy = [["cancer_specialist"], ["legal_advisor"]]; }, "world reset and reseeded");
    if (a === "rundemo") return runDemo();
    if (a === "preset") { ui.policy = PRESETS[+t.getAttribute("data-i")][1].map((c) => c.slice()); return render(); }
    if (a === "chip") {
      const ci = +t.getAttribute("data-clause"), at = t.getAttribute("data-attr");
      const c = ui.policy[ci];
      const i = c.indexOf(at);
      if (i >= 0) c.splice(i, 1); else c.push(at);
      return render();
    }
    if (a === "clause-add") { ui.policy.push([]); return render(); }
    if (a === "clause-del") { ui.policy.splice(+t.getAttribute("data-clause"), 1); return render(); }
    if (a === "create-bubble") return act(() => { ui.bubble = OSB.createBubble(ui.subject, readPolicy()); }, "bubble created");
    if (a === "open-bubble") { ui.bubble = t.getAttribute("data-bubble"); return render(); }
    if (a === "join") return act(() => OSB.join(t.getAttribute("data-bubble"), t.getAttribute("data-advisor")), "joined bubble");
    if (a === "send") {
      const inp = document.getElementById("composer");
      const text = inp ? inp.value : "";
      return act(() => OSB.send(t.getAttribute("data-bubble"), t.getAttribute("data-from"), text));
    }
    if (a === "remove-adv") return act(() => OSB.removeAdvisor(t.getAttribute("data-bubble"), t.getAttribute("data-advisor")), "advisor removed");
    if (a === "replace-adv") return act(() => OSB.replaceAdvisor(t.getAttribute("data-bubble"), t.getAttribute("data-advisor")), "advisor replaced");
    if (a === "close-bubble") return act(() => OSB.close(t.getAttribute("data-bubble")), "bubble closed");
    if (a === "toggle-avail") { const u = S().users[t.getAttribute("data-advisor")]; return act(() => OSB.setAvailability(u.handle, !u.available)); }
    if (a === "reg-subject") return act(() => { OSB.registerSubject(ui.reg.sHandle, ui.reg.sName, ui.reg.sBio); ui.reg.sHandle = ui.reg.sName = ui.reg.sBio = ""; }, "subject onboarded");
    if (a === "reg-advisor") return act(() => { OSB.registerAdvisor(ui.reg.aHandle, ui.reg.aName, ui.reg.aBio, ui.reg.aAttrs.slice()); ui.reg.aHandle = ui.reg.aName = ui.reg.aBio = ""; ui.reg.aAttrs = []; }, "advisor onboarded");
    if (a === "reg-chip") {
      const at = t.getAttribute("data-attr");
      const i = ui.reg.aAttrs.indexOf(at);
      if (i >= 0) ui.reg.aAttrs.splice(i, 1); else ui.reg.aAttrs.push(at);
      return render();
    }
    if (a === "ban") return act(() => OSB.setBanned(t.getAttribute("data-handle"), t.getAttribute("data-on") === "1"));
    if (a === "trace-pick") {
      const sel = document.getElementById("trace-select");
      if (!sel || !sel.value) return toast("no member selected", "err");
      const [b, h] = sel.value.split("|");
      return act(() => { const r = OSB.trace(b, h); toast("traced → token " + r.cpk + " (now revoked)", "ok"); });
    }
    if (a === "judge") {
      const u = OSB.judge(t.getAttribute("data-cpk"));
      return toast(u ? "Registrar identifies: " + u.name + " (" + u.handle + ")" : "no match", u ? "ok" : "err");
    }
    if (a === "dl-time") return download("time_log", OSB.timeLog());
    if (a === "dl-space") return download("space_log", OSB.spaceLog());
  }

  function runDemo() {
    try {
      const id = OSB.createBubble("emma", [["cancer_specialist"], ["legal_advisor"]]);
      const invited = S().bubbles[id].offers.map((o) => o.handle);
      invited.forEach((h) => OSB.join(id, h));
      OSB.send(id, "emma", "I was just diagnosed — what are my options?");
      if (invited[0]) OSB.send(id, invited[0], "Let's review them together, carefully.");
      ui.view = "subject";
      ui.subject = "emma";
      ui.bubble = id;
      toast("demo scenario created in " + id, "ok");
    } catch (e) {
      toast(e.message, "err");
    }
    render();
  }

  function mount() {
    OSB.seed();
    document.addEventListener("click", (e) => {
      const t = e.target.closest("[data-act]");
      if (t) { e.preventDefault(); handlers(t); }
    });
    document.addEventListener("input", (e) => {
      const f = e.target.getAttribute && e.target.getAttribute("data-reg");
      if (f) ui.reg[f] = e.target.value;
    });
    document.addEventListener("change", (e) => {
      if (e.target.id === "actor-select") {
        const role = e.target.getAttribute("data-role");
        if (role === "subject") ui.subject = e.target.value;
        else ui.advisor = e.target.value;
        ui.bubble = null;
        render();
      }
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && e.target.id === "composer") {
        const btn = document.querySelector('[data-act="send"]');
        if (btn) handlers(btn);
      }
    });
    render();
  }

  return { mount };
})();

if (document.readyState === "loading") window.addEventListener("DOMContentLoaded", App.mount);
else App.mount();
