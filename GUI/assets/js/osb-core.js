const OSB = (function () {
  const ATTRIBUTES = [
    "cancer_specialist",
    "medical_doctor",
    "mental_health_specialist",
    "legal_advisor",
    "financial_specialist",
    "experience_gt_5y",
    "experience_gt_10y",
    "peer_survivor",
  ];

  const LABELS = {
    cancer_specialist: "Cancer specialist",
    medical_doctor: "Medical doctor",
    mental_health_specialist: "Mental-health specialist",
    legal_advisor: "Legal advisor",
    financial_specialist: "Financial specialist",
    experience_gt_5y: "5+ years experience",
    experience_gt_10y: "10+ years experience",
    peer_survivor: "Peer survivor",
  };

  const SAMPLE = {
    subject: ["emma", "Emma Clarke", "recently diagnosed patient"],
    advisors: [
      ["walker", "Dr. Martin Walker", "oncologist, 18 years", ["cancer_specialist", "experience_gt_10y"]],
      ["reyes", "Dr. Sofia Reyes", "general practitioner, 9 years", ["medical_doctor", "experience_gt_5y"]],
      ["bennett", "Sarah Bennett", "solicitor", ["legal_advisor"]],
      ["marsh", "Diane Marsh", "solicitor, 6 years", ["legal_advisor", "experience_gt_5y"]],
      ["okonkwo", "James Okonkwo", "financial adviser", ["financial_specialist", "experience_gt_5y"]],
      ["khan", "Dr. Aisha Khan", "psychiatrist", ["mental_health_specialist", "experience_gt_10y"]],
      ["fielding", "Tom Fielding", "peer survivor & mentor", ["peer_survivor"]],
    ],
  };

  let state = freshState();
  const listeners = [];

  function freshState() {
    return {
      users: {},
      order: [],
      bubbles: {},
      ledger: [],
      tokens: { issued: 0, spent: 0 },
      revoked: [],
      registry: [],
      traced: [],
      banned: {},
      bcount: 0,
      log: [],
      startedAt: Date.now(),
    };
  }

  function rid(n) {
    const bytes = new Uint8Array(n || 9);
    if (typeof window !== "undefined" && window.crypto && window.crypto.getRandomValues) window.crypto.getRandomValues(bytes);
    else for (let i = 0; i < bytes.length; i++) bytes[i] = Math.floor(Math.random() * 256);
    return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
  }

  function slug(name) {
    const base = String(name).toLowerCase().replace(/dr\.?/g, "").replace(/[^a-z0-9]+/g, "").slice(0, 14) || "user";
    if (!state.users[base]) return base;
    let i = 2;
    while (state.users[base + i]) i++;
    return base + i;
  }

  function footprint() {
    try {
      return JSON.stringify({
        users: state.users,
        bubbles: state.bubbles,
        ledger: state.ledger,
        registry: state.registry,
        revoked: state.revoked,
        traced: state.traced,
        banned: state.banned,
      }).length;
    } catch (e) {
      return 0;
    }
  }

  function profile(op, fn) {
    const before = footprint();
    const t0 = performance.now();
    const result = fn();
    const ms = performance.now() - t0;
    state.log.push({ op, ms, bytes: Math.max(0, footprint() - before), at: Date.now() });
    notify();
    return result;
  }

  function notify() {
    listeners.forEach((fn) => fn());
  }

  function fail(message) {
    throw new Error(message);
  }

  function user(handle) {
    const u = state.users[handle];
    if (!u) fail("unknown user '" + handle + "'");
    return u;
  }

  function requireSubject(handle) {
    const u = user(handle);
    if (u.role !== "subject") fail("'" + handle + "' is not a subject");
    return u;
  }

  function requireAdvisor(handle) {
    const u = user(handle);
    if (u.role !== "advisor") fail("'" + handle + "' is not an advisor");
    return u;
  }

  function bubble(id) {
    const b = state.bubbles[id];
    if (!b) fail("unknown bubble '" + id + "'");
    return b;
  }

  function enrol(handle, name, bio, role, attrs) {
    const h = handle && handle.trim() ? handle.trim() : slug(name || role);
    if (state.users[h]) fail("handle '" + h + "' already exists");
    const cpk = rid(6);
    state.users[h] = {
      handle: h,
      name: (name && name.trim()) || h,
      bio: (bio && bio.trim()) || "",
      role,
      attrs: attrs || [],
      available: true,
      cpk,
      spk: rid(9),
      tokens: role === "advisor" ? 32 : 8,
    };
    state.order.push(h);
    state.registry.push({ r: rid(5), cpk });
    state.tokens.issued += role === "advisor" ? 32 : 8;
    return state.users[h];
  }

  function registerSubject(handle, name, bio) {
    return profile("registerSubject", () => enrol(handle, name, bio, "subject", []));
  }

  function registerAdvisor(handle, name, bio, attrs) {
    return profile("registerAdvisor", () => {
      const clean = (attrs || []).map((a) => a.trim()).filter(Boolean);
      const unknown = clean.filter((a) => !ATTRIBUTES.includes(a));
      if (unknown.length) fail("unknown attribute(s): " + unknown.join(", "));
      if (!clean.length) fail("an advisor needs at least one attribute");
      return enrol(handle, name, bio, "advisor", clean);
    });
  }

  function setAvailability(handle, available) {
    return profile("setAvailability", () => {
      requireAdvisor(handle).available = !!available;
    });
  }

  function setBanned(handle, banned) {
    return profile("setBanned", () => {
      user(handle);
      if (banned) state.banned[handle] = true;
      else delete state.banned[handle];
      return banned;
    });
  }

  function isBanned(handle) {
    return !!state.banned[handle];
  }

  function advisorDirectory() {
    return state.order
      .map((h) => state.users[h])
      .filter((u) => u.role === "advisor" && !state.banned[u.handle])
      .map((u) => ({ handle: u.handle, name: u.name, bio: u.bio, attrs: u.attrs, available: u.available }));
  }

  function coverPolicy(clauses, exclude) {
    const pool = advisorDirectory().filter((a) => a.available && !(exclude || []).includes(a.handle));
    const chosen = [];
    const chosenAttrs = new Set();
    for (const clause of clauses) {
      if (clause.some((a) => chosenAttrs.has(a))) continue;
      const pick = pool.find((a) => !chosen.includes(a.handle) && a.attrs.some((x) => clause.includes(x)));
      if (!pick) return null;
      chosen.push(pick.handle);
      pick.attrs.forEach((x) => chosenAttrs.add(x));
    }
    return chosen;
  }

  function getAdvisors(clauses) {
    return profile("getAdvisors", () => coverPolicy(clauses, []));
  }

  function createBubble(owner, clauses) {
    return profile("createBubble", () => {
      const u = requireSubject(owner);
      if (state.banned[owner]) fail("'" + owner + "' is banned");
      if (!clauses.length || clauses.some((c) => !c.length)) fail("policy needs at least one attribute");
      const apkL = coverPolicy(clauses, []);
      if (!apkL) fail("no set of available advisors satisfies that policy");
      if (u.tokens < 1) fail("subject has no authorisation tokens left");
      u.tokens -= 1;
      state.tokens.spent += 1;
      const id = "b" + state.bcount++;
      const shl = state.ledger.length;
      const dspk = rid(10);
      const offers = apkL.map((h) => ({ handle: h, dapk: rid(10) }));
      state.bubbles[id] = {
        id,
        owner,
        clauses,
        offers,
        members: [{ handle: owner, dpk: dspk, role: "subject" }],
        messages: [],
        closed: false,
        shl,
        createdAt: Date.now(),
      };
      state.ledger.push({ hl: shl, kind: "group", bubble: id, dpk: dspk, detail: "support bubble opened, " + offers.length + " advisor slot(s)", closed: false });
      return id;
    });
  }

  function invited(b, handle) {
    return b.offers.find((o) => o.handle === handle) || null;
  }

  function isMember(b, handle) {
    return b.members.some((m) => m.handle === handle);
  }

  function join(id, advisor) {
    return profile("joinGroup", () => {
      const b = bubble(id);
      const u = requireAdvisor(advisor);
      if (state.banned[advisor]) fail("'" + advisor + "' is banned");
      if (b.closed) fail("bubble " + id + " is closed");
      const offer = invited(b, advisor);
      if (!offer) fail("'" + advisor + "' was not invited to " + id);
      if (isMember(b, advisor)) fail("'" + advisor + "' already joined " + id);
      if (u.tokens < 1) fail("advisor has no tokens left");
      u.tokens -= 1;
      state.tokens.spent += 1;
      b.members.push({ handle: advisor, dpk: offer.dapk, role: "advisor" });
      state.ledger.push({ hl: state.ledger.length, kind: "member", bubble: id, dpk: offer.dapk, detail: "advisor joined " + id, closed: false });
      return offer.dapk;
    });
  }

  function send(id, from, text) {
    return profile("sendMessage", () => {
      const b = bubble(id);
      if (b.closed) fail("bubble " + id + " is closed");
      if (!isMember(b, from)) fail("'" + from + "' is not a member of " + id);
      if (!text || !text.trim()) fail("message is empty");
      b.messages.push({ from, text: text.trim(), ts: Date.now() });
      return true;
    });
  }

  function messages(id) {
    return bubble(id).messages;
  }

  function removeAdvisor(id, advisor) {
    return profile("removeAdvisor", () => {
      const b = bubble(id);
      if (b.closed) fail("bubble " + id + " is closed");
      if (!invited(b, advisor) && !isMember(b, advisor)) fail("'" + advisor + "' is not in " + id);
      b.offers = b.offers.filter((o) => o.handle !== advisor);
      b.members = b.members.filter((m) => m.handle !== advisor);
      return b.offers.map((o) => o.handle);
    });
  }

  function replaceAdvisor(id, advisor, clauses) {
    return profile("replaceAdvisor", () => {
      const b = bubble(id);
      if (b.closed) fail("bubble " + id + " is closed");
      if (!invited(b, advisor) && !isMember(b, advisor)) fail("'" + advisor + "' is not in " + id);
      b.offers = b.offers.filter((o) => o.handle !== advisor);
      b.members = b.members.filter((m) => m.handle !== advisor);
      const kept = b.offers.map((o) => o.handle);
      const policy = clauses && clauses.length ? clauses : b.clauses;
      const exclude = kept.concat([advisor]);
      const keptAttrs = new Set();
      kept.forEach((h) => state.users[h].attrs.forEach((a) => keptAttrs.add(a)));
      const additions = [];
      for (const clause of policy) {
        if (clause.some((a) => keptAttrs.has(a))) continue;
        const pool = advisorDirectory().filter((a) => a.available && !exclude.includes(a.handle) && !additions.includes(a.handle));
        const pick = pool.find((a) => a.attrs.some((x) => clause.includes(x)));
        if (!pick) fail("no available advisor can replace " + advisor);
        additions.push(pick.handle);
        state.users[pick.handle].attrs.forEach((a) => keptAttrs.add(a));
      }
      additions.forEach((h) => b.offers.push({ handle: h, dapk: rid(10) }));
      return b.offers.map((o) => o.handle);
    });
  }

  function close(id) {
    return profile("closeGroup", () => {
      const b = bubble(id);
      b.closed = true;
      const entry = state.ledger.find((e) => e.bubble === id && e.kind === "group");
      if (entry) entry.closed = true;
      return true;
    });
  }

  function trace(id, member) {
    return profile("trace", () => {
      const b = bubble(id);
      const m = b.members.find((x) => x.handle === member);
      if (!m) fail("'" + member + "' is not a member of " + id);
      const cpk = state.users[member].cpk;
      if (!state.revoked.includes(cpk)) state.revoked.push(cpk);
      const record = { bubble: id, dpk: m.dpk, cpk, at: Date.now() };
      if (!state.traced.some((t) => t.cpk === cpk && t.bubble === id)) state.traced.push(record);
      return record;
    });
  }

  function judge(cpk) {
    const h = state.order.find((x) => state.users[x].cpk === cpk);
    return h ? state.users[h] : null;
  }

  function seed() {
    registerSubject(SAMPLE.subject[0], SAMPLE.subject[1], SAMPLE.subject[2]);
    SAMPLE.advisors.forEach(([h, n, bio, attrs]) => registerAdvisor(h, n, bio, attrs));
    return state;
  }

  function reset(reseed) {
    state = freshState();
    if (reseed) seed();
    notify();
  }

  function aggregate() {
    const byOp = {};
    for (const e of state.log) {
      const a = (byOp[e.op] = byOp[e.op] || { op: e.op, calls: 0, ms: 0, bytes: 0 });
      a.calls += 1;
      a.ms += e.ms;
      a.bytes += e.bytes;
    }
    return Object.values(byOp).sort((x, y) => y.ms - x.ms);
  }

  function timeLog() {
    const rows = aggregate();
    const total = rows.reduce((s, r) => s + r.ms, 0);
    const when = new Date().toISOString().replace("T", " ").slice(0, 19);
    let out = "OSB-GUI time_log  -  web simulation  -  " + when + "\n";
    out += "wall-clock milliseconds per operation; reset on reload or Reset.\n\n";
    out += pad("total_ms", 12) + pad("avg_ms", 12) + pad("calls", 8) + "  operation\n";
    out += "-".repeat(56) + "\n";
    for (const r of rows) out += pad(r.ms.toFixed(3), 12) + pad((r.ms / r.calls).toFixed(3), 12) + pad(r.calls, 8) + "  " + r.op + "\n";
    out += "\ntotal: " + total.toFixed(3) + " ms across " + rows.length + " operation type(s)\n";
    return out;
  }

  function spaceLog() {
    const rows = aggregate().slice().sort((x, y) => y.bytes - x.bytes);
    const total = rows.reduce((s, r) => s + r.bytes, 0);
    const when = new Date().toISOString().replace("T", " ").slice(0, 19);
    let out = "OSB-GUI space_log  -  web simulation  -  " + when + "\n";
    out += "state-footprint growth in bytes per operation; reset on reload or Reset.\n\n";
    out += pad("total_bytes", 14) + pad("calls", 8) + "  operation\n";
    out += "-".repeat(56) + "\n";
    for (const r of rows) out += pad(r.bytes, 14) + pad(r.calls, 8) + "  " + r.op + "\n";
    out += "\ntotal: " + total + " bytes across " + rows.length + " operation type(s)\n";
    return out;
  }

  function pad(v, n) {
    const s = String(v);
    return s.length >= n ? s : " ".repeat(n - s.length) + s;
  }

  function onChange(fn) {
    listeners.push(fn);
  }

  return {
    ATTRIBUTES,
    LABELS,
    state: () => state,
    registerSubject,
    registerAdvisor,
    setAvailability,
    setBanned,
    isBanned,
    advisorDirectory,
    getAdvisors,
    createBubble,
    join,
    send,
    messages,
    removeAdvisor,
    replaceAdvisor,
    close,
    trace,
    judge,
    seed,
    reset,
    timeLog,
    spaceLog,
    onChange,
    label: (a) => LABELS[a] || a,
  };
})();
