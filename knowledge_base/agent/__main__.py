"""python3 -m agent propose | check | emit | show"""
import argparse
import json
import sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

from . import BUNDLE_DIR, __version__
from . import engines as eng
from . import taste as taste_mod
from .catalog import load_catalog
from .check import check_ir, report, write_report
from .emit import emit, write_outputs
from .ir import load_ir, to_dict, Event
from .policy import Policy
from .propose import append_gaps, default_events, format_table, propose
from . import handbook as hb
from . import knowledge as kn
from . import query as q


def _index_conn():
    """Read-only index connection with the memory db attached, or None when no index exists."""
    try:
        return q.open_all()
    except hb.HandbookError:
        return None


def _print_json(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=1))


def _load_all():
    return load_catalog(), Policy(), eng.load_engine_profiles(), taste_mod.load_profiles()


def _print_findings(findings):
    for f in findings:
        where = " ".join(x for x in (f.event_id, f.directive_id) if x)
        print("%-7s %-30s %s%s" % (f.level.upper(), f.code, f.message, ("  [" + where + "]") if where else ""))


def cmd_propose(args):
    catalog, policy, _, tastes = _load_all()
    taste_id, matched = None, []
    if args.taste:
        ranked = taste_mod.match(args.taste, tastes)
        taste_id = taste_mod.best(args.taste, tastes)
        matched = ranked[0][2] if ranked else []
        if taste_id is None:
            print("taste: no single profile matches %r (ranked: %s); pass --taste-id to choose" % (args.taste, ranked), file=sys.stderr)
    if args.taste_id:
        taste_id = args.taste_id
    profile = tastes.get(taste_id) if taste_id else None
    if args.events:
        doc = json.loads(Path(args.events).read_text(encoding="utf-8"))
        events = [Event(**e) for e in (doc["events"] if isinstance(doc, dict) else doc)]
    else:
        events, _ = default_events(args.duration)
    hconn = None if args.no_handbook else _index_conn()
    mem = kn.open_memory() if args.follow else None
    proposal = propose(args.request, events, catalog, policy, profile, args.sub_genre, handbook_conn=hconn, handbook_limit=args.handbook_limit, mem=mem, follow_depth=args.follow)
    proposal["matched_tags"] = matched
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(proposal, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    n = 0
    if not args.no_gaps:
        n = append_gaps(Path(args.gaps or (BUNDLE_DIR / "gaps.jsonl")), args.request, proposal["lexical_gaps"], taste_id)
    if args.json:
        print(json.dumps(proposal, ensure_ascii=False, indent=1))
    else:
        print(format_table(proposal))
        if n:
            print("appended %d gap line(s) to %s" % (n, args.gaps or (BUNDLE_DIR / "gaps.jsonl")))
    return 0


def _check(run_dir, key):
    catalog, policy, engines, tastes = _load_all()
    ir = load_ir(Path(run_dir) / "ir.json")
    findings = check_ir(ir, catalog, policy, engines, tastes, key=key, handbook_conn=_index_conn())
    rep = report(findings, key)
    return ir, findings, rep, catalog, policy, engines, tastes


def cmd_check(args):
    ir, findings, rep, _, _, _, _ = _check(args.run_dir, args.key)
    path = write_report(args.run_dir, rep)
    if not getattr(args, "no_usage", False):
        hconn = _index_conn()
        if hconn is not None:
            refs = []
            for a in ir.authored:
                for r in (a.handbook_refs or []):
                    pid = q.resolve_id(hconn, r)
                    if hb.get_passage(hconn, pid) is not None:
                        refs.append((a.event_id, pid))
            if refs:
                mem = kn.open_memory()
                kn.record_cited(mem, Path(args.run_dir).name, refs, {"status": rep["status"], "key": args.key})
                mem.close()
    if args.json:
        print(json.dumps(rep, ensure_ascii=False, indent=1))
    else:
        _print_findings(findings)
        print("%s: %d error(s), %d warning(s), %d note(s); key=%s; report %s" % (rep["status"].upper(), rep["errors"], rep["warnings"], rep["notes"], args.key, path))
    return 0 if rep["status"] == "pass" else 1


def cmd_emit(args):
    ir, findings, rep, catalog, policy, engines, tastes = _check(args.run_dir, "subject")
    write_report(args.run_dir, rep)
    if rep["status"] != "pass":
        _print_findings([f for f in findings if f.level == "error"])
        print("refusing to emit: %d error(s)" % rep["errors"])
        return 1
    engine_id = args.engine or ir.engine_profile_id
    profile = eng.get_profile(engines, engine_id)
    if eng.dispatch_status(profile) == "retired":
        print("refusing to emit for retired target %s" % engine_id)
        return 1
    if ir.engine_profile_id != engine_id:
        ir.engine_profile_id = engine_id
        extra = [f for f in check_ir(ir, catalog, policy, engines, tastes, handbook_conn=_index_conn()) if f.level == "error"]
        if extra:
            _print_findings(extra)
            print("refusing to emit for %s: %d error(s)" % (engine_id, len(extra)))
            return 1
    hconn = _index_conn()
    result = emit(ir, catalog, policy, profile, tastes.get(ir.taste_profile_id) if ir.taste_profile_id else None, avoid_sentence=args.avoid_sentence, handbook_conn=hconn)
    out_dir = write_outputs(Path(args.run_dir) / (args.arm or engine_id), result)
    if not args.no_usage:
        mem = kn.open_memory()
        nodes = [("directive", s.directive_id) for s in ir.active_selections()] + [("passage", r) for a in ir.authored for r in (a.handbook_refs or [])]
        if ir.taste_profile_id:
            nodes.append(("taste", ir.taste_profile_id))
        kn.record_usage(mem, Path(args.run_dir).name, "emitted", nodes, {"engine": engine_id, "arm": args.arm})
        mem.close()
    r = result.receipt
    summary = {"out_dir": str(out_dir), "engine": engine_id, "chars_total": r["chars_total"], "chars_by_event": r["chars_by_event"],
               "coverage": r["coverage"], "negatives": {"route": r["negatives"]["route"], "reason": r["negatives"]["reason"], "chars": r["negatives"]["chars"]},
               "prompt_sha256": r["prompt_sha256"]}
    print(json.dumps(summary, ensure_ascii=False, indent=1) if args.json else
          "emitted %s  chars=%d  coverage=%d/%d  negatives=%s%s  sha256=%s" % (
              out_dir, r["chars_total"], r["coverage"]["covered"], r["coverage"]["total"], r["negatives"]["route"],
              (" (" + r["negatives"]["reason"] + ")") if r["negatives"]["reason"] else "", r["prompt_sha256"][:12]))
    return 0


def cmd_show(args):
    catalog, policy, _, _ = _load_all()
    ir = load_ir(Path(args.run_dir) / "ir.json")
    if args.json:
        print(json.dumps(to_dict(ir), ensure_ascii=False, indent=1))
        return 0
    print("request: %s" % ir.request)
    print("clip: %s fps, %s s, %d frames; engine %s; taste %s" % (ir.clip.editorial_fps, ir.clip.duration_seconds, ir.clip.frame_count, ir.engine_profile_id, ir.taste_profile_id))
    for ev in ir.events_in_order():
        print("== %s %s [%d,%d) %s%s%s" % (ev.event_id, ev.moment_type, ev.start_frame, ev.end_frame, ev.actor_id,
                                          (" -> " + ev.target_id) if ev.target_id else "", (" inherits " + ev.inherit_from) if ev.inherit_from else ""))
        for s in ir.selections:
            if s.event_id != ev.event_id:
                continue
            d = catalog.get(s.directive_id)
            print("   %-36s %-17s %-9s %-18s subj=%-6s %s" % (s.directive_id, d.slot_id, policy.effective_priority(s, d), policy.budget_class(s.directive_id),
                                                           ",".join(policy.subjects_of(s, s.directive_id)), ("SUPPRESSED " + s.suppressed_reason) if s.suppressed_reason else ""))
        for a in ir.authored:
            if a.event_id == ev.event_id:
                print("   authored[%s/%s]: %s" % (a.slot_id, a.clause, a.text[:90]))
    return 0


def cmd_ask(args):
    conn = _need_index()
    catalog, policy, _, tastes = _load_all()
    res = q.ask(conn, args.request, catalog, policy, tastes, args.taste, limit_per=args.limit_per,
                kinds=None if args.all_kinds else q.NON_CODE, max_concepts=args.max_concepts, discover=args.discover)
    if args.knob:
        from . import knobs as kb
        k = kb.load()
        res["knobs"] = []
        for spec in args.knob:
            axis, _, name = spec.partition("=")
            o = kb.option(k, axis, name)
            res["knobs"].append(OrderedDict([("axis", axis), ("option", name), ("prose", o["prose"]), ("from", o.get("from", [])), ("prefers", o.get("prefers", []))]))
    if args.json:
        _print_json(res)
    else:
        print(q.format_ask(res, budget=args.budget or None, show_cite=args.cite))
        for kk in res.get("knobs", []):
            print("== knob %s=%s\n      %s" % (kk["axis"], kk["option"], kk["prose"]))
    return 0


def cmd_bench(args):
    from . import bench as bench_mod
    conn = _need_index()
    try:
        meta, records = bench_mod.load_queries(args.queries or bench_mod.QUERIES_PATH)
    except FileNotFoundError as e:
        print(str(e) + "; write it (first line may be a meta record) and rerun", file=sys.stderr)
        return 2
    result = bench_mod.run_bench(conn, records, limit=args.limit, expand=not args.no_expand, diverse=not args.no_diversify,
                                 rerank=(None if args.rerank == "default" else args.rerank == "on"), label=args.label)
    result["queries_meta"] = meta
    if args.out:
        path = bench_mod.save(result, name=args.out)
        print("saved", path)
    _print_json(result) if args.json else print(bench_mod.format_report(result))
    return 0


def cmd_tune_rerank(args):
    """Greedy: start from all flags off, add one at a time in RERANK_FLAGS order, keep it only if recall@10 does not drop
    (MRR breaks ties). Writes agent/data/rerank.json and docs/bench/<date>-tune.json."""
    from . import bench as bench_mod
    conn = _need_index()
    meta, records = bench_mod.load_queries(args.queries or bench_mod.QUERIES_PATH)
    flags = dict((k, False) for k in q.RERANK_FLAGS)
    base = bench_mod.run_bench(conn, records, limit=args.limit, rerank=dict(flags), label="tune-base")
    best = (base["recall_at_k"], base["mrr"])
    trail = [OrderedDict([("step", "none"), ("recall", base["recall_at_k"]), ("mrr", base["mrr"]), ("kept", True)])]
    for flag in q.RERANK_FLAGS:
        trial = dict(flags)
        trial[flag] = True
        res = bench_mod.run_bench(conn, records, limit=args.limit, rerank=trial, label="tune-" + flag)
        keep = (res["recall_at_k"] > best[0]) or (res["recall_at_k"] == best[0] and res["mrr"] >= best[1])
        trail.append(OrderedDict([("step", flag), ("recall", res["recall_at_k"]), ("mrr", res["mrr"]), ("kept", keep),
                                  ("delta_recall", round(res["recall_at_k"] - best[0], 4)), ("delta_mrr", round(res["mrr"] - best[1], 4))]))
        if keep:
            flags, best = trial, (res["recall_at_k"], res["mrr"])
    out = OrderedDict([("tuned_at", datetime.now(timezone.utc).isoformat()), ("queries_meta", meta), ("queries", len(records)),
                       ("rule", "greedy in RERANK_FLAGS order; keep iff recall@10 does not drop, MRR breaks ties"),
                       ("baseline", {"recall": base["recall_at_k"], "mrr": base["mrr"]}), ("final", {"recall": best[0], "mrr": best[1]}),
                       ("flags", flags), ("trail", trail)])
    q.RERANK_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    bench_mod.save(out, name=args.out or "%s-tune.json" % datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    for t in trail:
        print("%-20s recall %.3f  mrr %.3f  %s" % (t["step"], t["recall"], t["mrr"], "KEPT" if t["kept"] else "dropped"))
    print("flags:", json.dumps(flags))
    return 0


def cmd_mine_mechanisms(args):
    from . import mechanism
    conn = _need_index()
    res = mechanism.mine(conn, min_df=args.min_df, max_share=args.max_share, min_chapters=args.min_chapters, top=args.top)
    path = mechanism.write_review(res, conn, args.out)
    if args.json:
        _print_json(res)
    else:
        print("candidates %d (of %d passages); review document: %s" % (res["candidates"], res["passages"], path))
        for r in res["rows"][:args.show]:
            print("  %-28s df %3d ch %d unit %.2f label %.2f causal %d  score %.2f" % (r["term"], r["df"], r["chapters"], r["unit_share"], r["label_share"], r["causal"], r["score"]))
    return 0


def cmd_label(args):
    conn = _need_index()
    pid = q.resolve_id(conn, args.id)
    if hb.get_passage(conn, pid) is None:
        print("unknown passage: %s" % args.id, file=sys.stderr)
        return 1
    mem = kn.open_memory()
    kn.set_label(mem, pid, args.moment, args.slot, args.reason, args.confidence)
    print("judged %s: moment=%s slot=%s (%.2f) — %s" % (q.short_id(conn, pid), args.moment, args.slot, args.confidence, args.reason))
    return 0


def cmd_labels(args):
    conn = _need_index()
    rows = conn.execute("SELECT node_id, moment_type, slot_id, confidence, reason FROM mem.agent_labels ORDER BY created_at DESC LIMIT ?", (args.limit,)).fetchall()
    for r in rows:
        print("%-10s %-15s %-17s %.2f  %s" % (q.short_id(conn, r[0]), r[1] or "-", r[2] or "-", r[3], r[4]))
    print("%d judged label(s)" % conn.execute("SELECT count(*) FROM mem.agent_labels").fetchone()[0])
    return 0


def cmd_discover(args):
    from . import discover as disc
    conn = _need_index()
    if args.source:
        a_id = q.resolve_id(conn, args.source)
    else:
        hits, _ = q.lookup2(conn, text=args.query, limit=8, min_score=0)
        if not hits:
            print("no seed passage for query %r" % args.query, file=sys.stderr)
            return 1
        substantive = [h for h in hits if (hb.get_passage(conn, h["id"]) or {}).get("chars", 0) >= args.min_chars]
        a_id = (substantive or hits)[0]["id"]   # seed from a substantive hit, not a one-line fragment
    hyps = disc.bridges(conn, a_id, kinds=tuple(args.kinds.split(",")), min_chars=args.min_chars, cross_only=args.cross_only, limit=args.limit)
    recs = disc.hypothesis_records(conn, a_id, hyps)
    n = 0
    if args.enqueue and recs:
        mem = kn.open_memory()
        n = disc.enqueue(mem, a_id, hyps, source="discover")
        mem.close()
    if args.json:
        _print_json({"a": q.short_id(conn, a_id), "hypotheses": recs, "enqueued": n})
        return 0
    a = hb.get_passage(conn, a_id)
    print("A %s: %s" % (q.short_id(conn, a_id), hb.excerpt(a, 110)))
    for r in recs:
        print("  %.2f via %-20s %s C=%s  (A matched %s; C matched %s)" % (r["score"], r["b"], "cross" if r["cross_chapter"] else "same ", r["c"], r["a_matched"], r["c_matched"]))
        print("        " + r["c_line"])
    if not recs:
        print("  (no bridges: A links to no mechanism/technique concept, or no cure passage satisfies the constraints)")
    if args.enqueue:
        print("enqueued %d new hypothesis(es) in review_queue" % n)
    return 0


def cmd_queue(args):
    from . import discover as disc
    conn = _need_index()
    mem = kn.open_memory()
    rows = disc.pending(mem, args.limit)
    for r in rows:
        print("#%-4d %.2f  %s -> %s <- %s   %s" % (r["id"], r["score"], q.short_id(conn, r["a_id"]), r["b_concept"], q.short_id(conn, r["c_id"]), r["evidence"][:70]))
        if args.text:
            print("      A: " + hb.excerpt(hb.get_passage(conn, r["a_id"]), 140))
            print("      C: " + hb.excerpt(hb.get_passage(conn, r["c_id"]), 140))
    counts = dict(mem.execute("SELECT status, count(*) FROM review_queue GROUP BY status").fetchall())
    print("queue:", counts)
    return 0


def cmd_resolve(args):
    from . import discover as disc
    mem = kn.open_memory()
    status = disc.resolve(mem, args.id, args.relation, args.note or "")
    print("#%d %s as %s" % (args.id, status, args.relation))
    return 0


def cmd_causal(args):
    from . import causal
    mem = kn.open_memory()
    if args.op == "add":
        causal.add(mem, args.subject, args.predicate, args.object, args.evidence or "", args.passage, args.confidence)
        print("added %s -%s-> %s" % (args.subject, args.predicate, args.object))
    elif args.op == "seed":
        conn = _need_index()
        h = causal.seed_from_handbook(conn, mem)
        c = causal.seed_from_catalog(conn, mem)
        print("seeded %d from handbook clauses, %d from catalog mechanics; total triples %d" % (h, c, mem.execute("SELECT count(*) FROM causal_triples").fetchone()[0]))
    elif args.op == "list":
        for t in causal.list_triples(mem, args.subject):
            print("%-4d %-34s %-15s %-34s %.2f  %s" % (t["id"], t["subject_concept"], t["predicate"], t["object_concept"], t["confidence"], (t["evidence"] or "")[:60]))
    elif args.op == "closure":
        res = causal.closure(mem, args.subject, depth=args.depth)
        _print_json(res) if args.json else print("\n".join("%d %s  (%s)" % (r["depth"], r["concept"], r["path"]) for r in res) or "(nothing reachable)")
    elif args.op == "compensations":
        _print_json(causal.compensations(mem, args.subject))
    elif args.op == "isomorph":
        res = causal.isomorphs(mem)
        _print_json(res) if args.json else print("\n".join("%s: %s | %s" % (r["pattern"], " > ".join(r["chain_a"]), " > ".join(r["chain_b"])) for r in res) or "(no isomorphic chains yet)")
    return 0


def cmd_verify(args):
    from . import verify as vf
    res = vf.run()
    _print_json(res) if args.json else print(vf.format_report(res))
    return 0 if res["ok"] else 1


def cmd_specimens(args):
    conn = _need_index()
    rows = hb.specimens(conn, args.language, q.fts_query(args.text) if args.text else None, args.heading, args.limit)
    if args.json:
        _print_json([OrderedDict([("sid", q.short_id(conn, r["passage_id"])), ("language", r["language"]), ("chars", r["chars"]), ("heading", r["heading_path"]), ("article", r["article_title"])]) for r in rows])
        return 0
    for r in rows:
        print("%-10s %-5s %5dch  %s  ::  %s" % (q.short_id(conn, r["passage_id"]), r["language"], r["chars"], (r["article_title"] or "")[:38], (r["heading_path"] or "")[:60]))
        if args.show:
            print("      " + r["text"][:args.show].replace("\n", "\n      "))
    print("%d specimen(s); `read passage <sid>` prints one in full" % len(rows))
    return 0


def cmd_knobs(args):
    from . import knobs as kb
    k = kb.load()
    if args.axis and args.option:
        o = kb.option(k, args.axis, args.option)
        print(o["prose"]); print("from:", ", ".join(o.get("from", [])), "| prefers:", ", ".join(o.get("prefers", [])))
        return 0
    for a, v in k["axes"].items():
        print("%-18s %s" % (a, v["label"]))
        for name, o in v["options"].items():
            print("    %-30s %s" % (name, o["prose"][:100]))
    bad = kb.check_prose(k)
    print("prose check:", "OK, no frame/fps numbers" if not bad else "NUMERIC in %s" % bad)
    return 0


def cmd_variants(args):
    from . import knobs as kb
    paths = kb.write_variants(args.run_dir, args.axis, args.base)
    for p in paths:
        print("wrote", p)
    return 0


def cmd_relations(args):
    from . import relations as rel
    mem = kn.open_memory()
    if args.op == "seed":
        print("seeded %d relation(s); total %d" % (rel.seed(mem), mem.execute("SELECT count(*) FROM module_relations").fetchone()[0]))
    elif args.op == "add":
        rel.add(mem, args.source, args.relation, args.target, args.evidence or "", args.passage, args.offset or "", args.confidence)
        print("added %s -%s-> %s" % (args.source, args.relation, args.target))
    elif args.op == "list":
        for r in rel.list_relations(mem, args.source):
            print("%-4d %-34s %-17s %-34s %s" % (r["id"], r["source"], r["relation"], r["target"], (r["evidence"] or "")[:50]))
    elif args.op == "follow":
        seeds = [x.strip() for x in (args.source or "").split(",") if x.strip()]
        for p in rel.follow(mem, seeds, depth=args.depth):
            print("%-34s %-17s via %-28s d%d  %s" % (p["id"], p["relation"], p["via"], p["depth"], (p["offset"] or "")))
    return 0


def cmd_index_handbook(args):
    catalog, policy, _, _ = _load_all()
    db = hb.build_index(args.html, args.db or hb.DEFAULT_DB, catalog=catalog, policy=policy)
    conn = hb.connect(db)
    m = hb.meta(conn)
    print(json.dumps(OrderedDict((k, m.get(k)) for k in ("source_path", "source_sha256", "chapters", "sections", "articles", "passages", "blocks", "edges", "concepts", "concept_passages", "summaries", "built_at")), indent=1))
    print("index:", db)
    return 0


def _need_index():
    conn = _index_conn()
    if conn is None:
        print("no handbook index; run: python3 -m agent index-handbook ~/Downloads/handbook.html", file=sys.stderr)
        sys.exit(2)
    return conn


def cmd_find(args):
    conn = _need_index()
    res = q.find2(conn, args.text, limit=args.limit, kinds=None if args.all_kinds else q.NON_CODE, expand=not args.no_expand, diverse=not args.no_diversify,
                  spread=args.spread, per_concept=args.per_concept)
    if args.json:
        _print_json(res)
        return 0
    for c in res["concepts"]:
        print("concept %s  %s [%s]  aliases used: %s" % (c["id"], c["label"], c["ckind"], ", ".join(c["aliases_used"])))
    for t in res["tags"]:
        print("tag %s" % t["id"])
    print(q.format_hits2(res["passages"], budget=args.budget or None, show_cite=args.cite) if res["passages"] else "(no passages)")
    return 0


def cmd_lookup(args):
    conn = _need_index()
    hits, concepts = q.lookup2(conn, args.moment, args.slot, args.tier, args.text, args.min_score, args.limit, None if args.all_kinds else q.NON_CODE,
                               expand=not args.no_expand, diverse=not args.no_diversify, spread=args.spread, per_concept=args.per_concept)
    if args.json:
        _print_json({"concepts": [(c, [a for a, _, _ in spec]) for c, spec in concepts], "passages": hits})
        return 0
    print(q.format_hits2(hits, budget=args.budget or None, show_cite=args.cite) if hits else "(no passages)")
    return 0


def cmd_read(args):
    conn = _need_index()
    res = q.read(conn, args.kind, q.resolve_id(conn, args.id), args.max_chars)
    if res is None:
        print("not found: %s %s" % (args.kind, args.id), file=sys.stderr)
        return 1
    _print_json(res) if args.json else print(res["text"])
    return 0


def cmd_outline(args):
    conn = _need_index()
    res = q.outline(conn, args.kind, q.resolve_id(conn, args.id) if args.id else None)
    if args.json:
        _print_json(res)
        return 0
    for r in res:
        if isinstance(r, dict) and "line" in r:
            extra = "  [%s %s]" % (r.get("akind") or "", r.get("epistemic") or "") if r.get("kind") == "article" else ("  (%s passages, %s chars)" % (r.get("passages"), r.get("chars")) if r.get("kind") == "block" else "")
            print("%s %s%s\n      %s" % (r.get("kind"), r.get("id"), extra, r.get("line", "")))
        else:
            _print_json(r)
    return 0


def cmd_concept(args):
    conn = _need_index()
    if args.id is None:
        rows = conn.execute("SELECT concept_id, label, kind FROM concepts ORDER BY kind, concept_id").fetchall() + conn.execute("SELECT concept_id, label, kind FROM mem.agent_concepts").fetchall()
        for r in rows:
            print("%-32s %-10s %s" % (r[0], r[2], r[1]))
        return 0
    res = q.concept(conn, args.id, args.limit)
    if res is None:
        print("unknown concept: %s" % args.id, file=sys.stderr)
        return 1
    if args.json:
        _print_json(res)
        return 0
    print("%s  [%s]  %s\n  aliases: %s" % (res["id"], res["kind"], res["label"], ", ".join(res["aliases"])))
    if res["description"]:
        print("  note: %s" % res["description"])
    if res["directives"]:
        print("  directives: " + ", ".join("%s(%s)" % (d["id"], d["relation"]) for d in res["directives"]))
    if res["related"]:
        print("  related: " + ", ".join("%s(%s %s)" % (r["id"], r["relation"], r["weight"]) for r in res["related"]))
    if res["tags"] or res["used_with"] or res["agent_links"]:
        print("  tags: %s  used_with: %s  links: %s" % (res["tags"], res["used_with"], res["agent_links"]))
    print(q.format_hits(res["passages"]))
    return 0


def cmd_near(args):
    conn = _need_index()
    res = q.near(conn, q.resolve_id(conn, args.id))
    if res is None:
        print("unknown passage: %s" % args.id, file=sys.stderr)
        return 1
    _print_json(res)
    return 0


def cmd_walk(args):
    conn = _need_index()
    res = q.walk(conn, args.slot, args.start, args.per_moment, args.min_score)
    if args.json:
        _print_json(res)
        return 0
    for moment, hits in res.items():
        print("== %s" % moment)
        print(q.format_hits(hits) if hits else "   (none)")
    return 0


def cmd_deps(args):
    conn = _need_index()
    res = q.deps(conn, args.directive_id)
    _print_json(res) if args.json else print("\n".join("%s <- %s  %s  %s" % (r["token"], r["satisfier_directive_id"], r.get("passage_id") or "", r.get("line") or "") for r in res) or "(no requires)")
    return 0


def cmd_tag(args):
    mem = kn.open_memory()
    if args.node_kind and args.node_id:
        tag = kn.tag_node(mem, args.node_kind, args.node_id, args.tag, args.weight, args.note or "")
        print("tagged %s %s with %s" % (args.node_kind, args.node_id, tag))
    else:
        tag = kn.add_tag(mem, args.tag, args.note or "", aliases=args.alias or [])
        print("tag %s ready" % tag)
    return 0


def cmd_tagged(args):
    conn = _need_index()
    tag = kn.resolve_tag(conn, args.tag) if False else args.tag.strip().lower().replace(" ", "_")
    rows = [dict(r) for r in conn.execute("SELECT node_kind, node_id, weight, note FROM mem.node_tags WHERE tag = ? ORDER BY weight DESC LIMIT ?", (tag, args.limit))]
    _print_json(rows) if args.json else print("\n".join("%s %s  w=%s  %s" % (r["node_kind"], r["node_id"], r["weight"], r["note"]) for r in rows) or "(nothing tagged %s)" % tag)
    return 0


def cmd_note(args):
    mem = kn.open_memory()
    kn.set_summary(mem, args.node_kind, args.node_id, args.text)
    print("summary set for %s %s" % (args.node_kind, args.node_id))
    return 0


def cmd_link(args):
    mem = kn.open_memory()
    kn.add_link(mem, args.from_kind, args.from_id, args.to_kind, args.to_id, args.relation, args.note or "")
    print("linked %s %s -%s-> %s %s" % (args.from_kind, args.from_id, args.relation, args.to_kind, args.to_id))
    return 0


def cmd_concept_add(args):
    mem = kn.open_memory()
    kn.add_concept(mem, args.id, args.label, args.kind, args.alias or [], args.note or "")
    print("concept %s added to agent memory (rebuild the index to link passages: index-handbook)" % args.id)
    return 0


def cmd_usage(args):
    mem = kn.open_memory()
    if args.node_kind and args.node_id:
        res = {"used_with": kn.used_with(mem, args.node_kind, args.node_id, args.limit)}
    else:
        res = {"top": kn.usage_stats(mem, args.node_kind, args.limit)}
    _print_json(res)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="agent", description="bundle-local prompt agent (v%s): propose rows, check an IR, emit prose" % __version__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("propose", help="candidate rows per event x slot for a request")
    p.add_argument("request")
    p.add_argument("--taste", help="vibe words, e.g. 'heavy, brutal, old school'")
    p.add_argument("--taste-id", help="force a taste profile id")
    p.add_argument("--sub-genre")
    p.add_argument("--duration", type=float, default=3.0, help="seconds; scales the bundle's single-exchange event template")
    p.add_argument("--events", help="JSON file with an events array instead of the template")
    p.add_argument("--out", help="write proposal.json here")
    p.add_argument("--gaps", help="gaps.jsonl path (default: bundle root)")
    p.add_argument("--no-gaps", action="store_true")
    p.add_argument("--no-handbook", action="store_true", help="skip handbook passages per event x slot")
    p.add_argument("--handbook-limit", type=int, default=3)
    p.add_argument("--follow", type=int, default=0, help="pull supporting rows through module relations from each beat's primary actions (depth 1 or 2)")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_propose)
    c = sub.add_parser("check", help="check <run_dir>/ir.json; writes check_report.json")
    c.add_argument("run_dir")
    c.add_argument("--key", choices=("subject", "actor"), default="subject", help="duplicate-slot key: subject (default) or actor (the bundle validator's rule)")
    c.add_argument("--no-usage", action="store_true", help="do not record cited events in agent_memory.db")
    c.add_argument("--json", action="store_true")
    c.set_defaults(func=cmd_check)
    e = sub.add_parser("emit", help="check, then emit prompt/post_plan/receipt into <run_dir>/<arm or engine>/")
    e.add_argument("run_dir")
    e.add_argument("--engine")
    e.add_argument("--arm", help="output folder name (default: the engine id)")
    e.add_argument("--avoid-sentence", action="store_true", help="fold negatives into one Avoid sentence when the engine has no active negative field (unverified)")
    e.add_argument("--no-usage", action="store_true", help="do not record this emit in agent_memory.db")
    e.add_argument("--json", action="store_true")
    e.set_defaults(func=cmd_emit)
    s = sub.add_parser("show", help="print the IR's selections with priority, budget class and subject")
    s.add_argument("run_dir")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_show)
    bn = sub.add_parser("bench", help="recall@k, MRR and retrieval-to-citation over docs/queries.jsonl")
    bn.add_argument("--queries")
    bn.add_argument("--limit", type=int, default=10)
    bn.add_argument("--label", default="bench")
    bn.add_argument("--out", help="file name under docs/bench/ to save the result json")
    bn.add_argument("--no-expand", action="store_true")
    bn.add_argument("--no-diversify", action="store_true")
    bn.add_argument("--rerank", choices=("default", "on", "off"), default="default")
    bn.add_argument("--json", action="store_true")
    bn.set_defaults(func=cmd_bench)
    tr = sub.add_parser("tune-rerank", help="greedy flag selection gated by recall@10; writes agent/data/rerank.json")
    tr.add_argument("--queries")
    tr.add_argument("--limit", type=int, default=10)
    tr.add_argument("--out")
    tr.set_defaults(func=cmd_tune_rerank)
    mm = sub.add_parser("mine-mechanisms", help="mine mechanism-vocabulary candidates with lexical pre-filters; writes docs/mechanism_candidates.md")
    mm.add_argument("--min-df", type=int, default=3)
    mm.add_argument("--max-share", type=float, default=0.01)
    mm.add_argument("--min-chapters", type=int, default=2)
    mm.add_argument("--top", type=int, default=150)
    mm.add_argument("--show", type=int, default=25)
    mm.add_argument("--out")
    mm.add_argument("--json", action="store_true")
    mm.set_defaults(func=cmd_mine_mechanisms)
    lb = sub.add_parser("label", help="record a judged moment/slot label for a passage, with its reason")
    lb.add_argument("id")
    lb.add_argument("--moment")
    lb.add_argument("--slot")
    lb.add_argument("--reason", required=True)
    lb.add_argument("--confidence", type=float, default=0.7)
    lb.set_defaults(func=cmd_label)
    lbs = sub.add_parser("labels", help="list judged labels")
    lbs.add_argument("--limit", type=int, default=50)
    lbs.set_defaults(func=cmd_labels)
    dv = sub.add_parser("discover", help="Swanson A->B<-C hypotheses from a passage or the top hit of a query")
    dv.add_argument("--source", help="seed passage id (short or canonical)")
    dv.add_argument("--query", help="seed from the top find hit")
    dv.add_argument("--kinds", default="mechanism,technique")
    dv.add_argument("--min-chars", type=int, default=80)
    dv.add_argument("--cross-only", action="store_true")
    dv.add_argument("--limit", type=int, default=10)
    dv.add_argument("--enqueue", action="store_true", help="write hypotheses to review_queue (pending)")
    dv.add_argument("--json", action="store_true")
    dv.set_defaults(func=cmd_discover)
    qu = sub.add_parser("queue", help="pending review_queue hypotheses")
    qu.add_argument("--limit", type=int, default=20)
    qu.add_argument("--text", action="store_true", help="show A and C excerpts")
    qu.set_defaults(func=cmd_queue)
    rs = sub.add_parser("resolve", help="resolve a review_queue row; accepted relations become agent_links edges with evidence")
    rs.add_argument("id", type=int)
    rs.add_argument("relation", choices=("analogous_mechanism", "compensates_for", "extends", "refines", "contradicts", "restates", "unrelated"))
    rs.add_argument("--note")
    rs.set_defaults(func=cmd_resolve)
    cz = sub.add_parser("causal", help="causal triples between concepts: add | seed | list | closure | compensations | isomorph")
    cz.add_argument("op", choices=("add", "seed", "list", "closure", "compensations", "isomorph"))
    cz.add_argument("subject", nargs="?")
    cz.add_argument("predicate", nargs="?", choices=(None, "amplifies", "dampens", "triggers", "inhibits", "requires", "breaks", "compensates_for"))
    cz.add_argument("object", nargs="?")
    cz.add_argument("--evidence")
    cz.add_argument("--passage")
    cz.add_argument("--confidence", type=float, default=0.6)
    cz.add_argument("--depth", type=int, default=3)
    cz.add_argument("--json", action="store_true")
    cz.set_defaults(func=cmd_causal)
    vf = sub.add_parser("verify", help="integrity + backfill checks over the index and memory (read-only); exit 1 on any failure")
    vf.add_argument("--json", action="store_true")
    vf.set_defaults(func=cmd_verify)
    sp = sub.add_parser("specimens", help="typed code blocks (yaml/json/xml/text): the handbook's schemas and templates")
    sp.add_argument("--language")
    sp.add_argument("--text")
    sp.add_argument("--heading")
    sp.add_argument("--limit", type=int, default=20)
    sp.add_argument("--show", type=int, default=0, help="print the first N chars of each")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_specimens)
    kb = sub.add_parser("knobs", help="diversity knobs: axes and options, or one option's prose")
    kb.add_argument("axis", nargs="?")
    kb.add_argument("option", nargs="?")
    kb.set_defaults(func=cmd_knobs)
    vr = sub.add_parser("variants", help="write one-change variants of a run's JSON prompt along one knob axis")
    vr.add_argument("run_dir")
    vr.add_argument("--axis", required=True)
    vr.add_argument("--base", default="prompt.json")
    vr.set_defaults(func=cmd_variants)
    rl = sub.add_parser("relations", help="module relations: seed | add | list | follow")
    rl.add_argument("op", choices=("seed", "add", "list", "follow"))
    rl.add_argument("source", nargs="?")
    rl.add_argument("relation", nargs="?")
    rl.add_argument("target", nargs="?")
    rl.add_argument("--evidence")
    rl.add_argument("--passage")
    rl.add_argument("--offset")
    rl.add_argument("--confidence", type=float, default=0.6)
    rl.add_argument("--depth", type=int, default=1)
    rl.set_defaults(func=cmd_relations)
    ih = sub.add_parser("index-handbook", help="build handbook_index.db from handbook.html (rebuilds; agent_memory.db untouched)")
    ih.add_argument("html")
    ih.add_argument("--db")
    ih.set_defaults(func=cmd_index_handbook)
    ak = sub.add_parser("ask", help="one call: request -> moments, slots, concepts, hits per concept, directives, gaps")
    ak.add_argument("request")
    ak.add_argument("--taste", help="vibe words")
    ak.add_argument("--limit-per", type=int, default=3)
    ak.add_argument("--max-concepts", type=int, default=4)
    ak.add_argument("--budget", type=int, default=1500, help="character budget (0 = none)")
    ak.add_argument("--all-kinds", action="store_true")
    ak.add_argument("--discover", type=int, default=0, help="append up to N Swanson bridge hypotheses as a serendipity group")
    ak.add_argument("--knob", action="append", help="axis=option, repeatable; appends the option's verbalised prose")
    ak.add_argument("--cite", action="store_true")
    ak.add_argument("--json", action="store_true")
    ak.set_defaults(func=cmd_ask)
    f = sub.add_parser("find", help="one query over concepts, tags and passages (FTS5)")
    f.add_argument("text")
    f.add_argument("--limit", type=int, default=8)
    f.add_argument("--all-kinds", action="store_true", help="include code blocks")
    f.add_argument("--no-expand", action="store_true", help="do not expand through concept aliases")
    f.add_argument("--no-diversify", action="store_true", help="no per-block / per-article cap")
    f.add_argument("--spread", type=float, default=0.5, help="allocator diversity 0 (relevance) .. 1 (spread)")
    f.add_argument("--per-concept", type=int, default=None, help="allocator: minimum hits per resolved concept")
    f.add_argument("--budget", type=int, default=0, help="character budget for the printed hits (0 = none)")
    f.add_argument("--cite", action="store_true", help="print the full citation under each hit")
    f.add_argument("--json", action="store_true")
    f.set_defaults(func=cmd_find)
    lk = sub.add_parser("lookup", help="passages by moment / slot / tier, optionally with text")
    lk.add_argument("--moment")
    lk.add_argument("--slot")
    lk.add_argument("--tier", type=int)
    lk.add_argument("--text")
    lk.add_argument("--min-score", type=int, default=2)
    lk.add_argument("--limit", type=int, default=8)
    lk.add_argument("--all-kinds", action="store_true")
    lk.add_argument("--no-expand", action="store_true")
    lk.add_argument("--no-diversify", action="store_true")
    lk.add_argument("--spread", type=float, default=0.5, help="allocator diversity 0 (relevance) .. 1 (spread)")
    lk.add_argument("--per-concept", type=int, default=None, help="allocator: minimum hits per resolved concept")
    lk.add_argument("--budget", type=int, default=0)
    lk.add_argument("--cite", action="store_true")
    lk.add_argument("--json", action="store_true")
    lk.set_defaults(func=cmd_lookup)
    rd = sub.add_parser("read", help="expand a passage, block or article")
    rd.add_argument("kind", choices=("passage", "block", "article"))
    rd.add_argument("id")
    rd.add_argument("--max-chars", type=int, default=1500)
    rd.add_argument("--json", action="store_true")
    rd.set_defaults(func=cmd_read)
    ol = sub.add_parser("outline", help="chapters; or the children of a chapter / section / article / block")
    ol.add_argument("kind", nargs="?", choices=("chapter", "section", "article", "block", "passage"))
    ol.add_argument("id", nargs="?")
    ol.add_argument("--json", action="store_true")
    ol.set_defaults(func=cmd_outline)
    co = sub.add_parser("concept", help="list concepts, or one concept with its passages, related concepts and directives")
    co.add_argument("id", nargs="?")
    co.add_argument("--limit", type=int, default=8)
    co.add_argument("--json", action="store_true")
    co.set_defaults(func=cmd_concept)
    nr = sub.add_parser("near", help="a passage's neighbours, block, duplicates, concepts, citations, tags")
    nr.add_argument("id")
    nr.set_defaults(func=cmd_near)
    wk = sub.add_parser("walk", help="passages for one slot along the phase order")
    wk.add_argument("--slot", required=True)
    wk.add_argument("--start", default="anticipation")
    wk.add_argument("--per-moment", type=int, default=3)
    wk.add_argument("--min-score", type=int, default=2)
    wk.add_argument("--json", action="store_true")
    wk.set_defaults(func=cmd_walk)
    dp = sub.add_parser("deps", help="a directive's requires tokens, satisfiers and their passages")
    dp.add_argument("directive_id")
    dp.add_argument("--json", action="store_true")
    dp.set_defaults(func=cmd_deps)
    tg = sub.add_parser("tag", help="create a tag, or tag a node (passage/block/article/concept/directive)")
    tg.add_argument("tag")
    tg.add_argument("node_kind", nargs="?")
    tg.add_argument("node_id", nargs="?")
    tg.add_argument("--weight", type=float, default=1.0)
    tg.add_argument("--note")
    tg.add_argument("--alias", action="append")
    tg.set_defaults(func=cmd_tag)
    tgd = sub.add_parser("tagged", help="nodes carrying a tag")
    tgd.add_argument("tag")
    tgd.add_argument("--limit", type=int, default=20)
    tgd.add_argument("--json", action="store_true")
    tgd.set_defaults(func=cmd_tagged)
    nt = sub.add_parser("note", help="set the agent's one-line summary for a node (overrides the auto summary)")
    nt.add_argument("node_kind")
    nt.add_argument("node_id")
    nt.add_argument("text")
    nt.set_defaults(func=cmd_note)
    ln = sub.add_parser("link", help="record a relation between two nodes in agent memory")
    ln.add_argument("from_kind")
    ln.add_argument("from_id")
    ln.add_argument("relation")
    ln.add_argument("to_kind")
    ln.add_argument("to_id")
    ln.add_argument("--note")
    ln.set_defaults(func=cmd_link)
    ca = sub.add_parser("concept-add", help="add a concept with aliases to agent memory")
    ca.add_argument("id")
    ca.add_argument("label")
    ca.add_argument("--kind", default="concept")
    ca.add_argument("--alias", action="append")
    ca.add_argument("--note")
    ca.set_defaults(func=cmd_concept_add)
    us = sub.add_parser("usage", help="most-used nodes, or what a node was used with")
    us.add_argument("node_kind", nargs="?")
    us.add_argument("node_id", nargs="?")
    us.add_argument("--limit", type=int, default=20)
    us.set_defaults(func=cmd_usage)
    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
