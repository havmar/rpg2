#!/usr/bin/env python3
"""Publish a turn: project the save and write the batch that sends it to the page.

    python publish.py [--prose FILE] [--moves PATH] [--state FILE]
                      [--state-version N] [--versions FILE] [--status STATUS]
                      [--check-in TEXT] [--all] [--out DIR]
    python publish.py --sent [--url URL] [--out DIR]

The keeper's turn of THE PLAYER'S PAGE (page-plan.md; dream's publish.py,
adapted). After playing the turn with ``session.py``, run this: it loads the
save under ``RPG2_HOME`` (``session.load()``), projects it with
``page.player_view`` (nothing the player may not know is ever written), and
writes into ``web/out/`` (under ``RPG2_HOME``; ``--out`` for another):

* ``game/<name>.json`` for every singleton that changed since the last publish
  (every one with ``--all``, or when there is no last publish to compare with);
* ``chronicle/tNNNN.json``, the new chronicle entry, when there is ``--prose``;
* ``fights/fNNNN.json`` for every fight queued since the last publish, when
  there is ``--prose``: the entry lists them, and ``game/state``'s
  ``lastFight`` names the newest;
* ``batch.json``, the ``writes`` of one ``ArtifactData`` batch: a ``set`` for
  each of those files, and a ``delete`` for every move read, each pinned with
  ``if_version`` where a version was read.

Every session fight is kept for the page on its own: ``session.print_combat``
calls ``page.keep_fight``, which queues the fight's player log, in blocks, in
``ui/queue/`` (as long-lived as the save; ``new`` empties it). The turn's
publish numbers the queue after ``lastFight`` and sends it; a paused fight's
second half is its own document, whose ``continues`` names the first half.
``--sent`` empties the queue of what was sent. A numbered fight keeps its id in
the queue, so if the batch landed and ``--sent`` never ran, the next publish
(with ``--state``) sees ``lastFight`` past it and drops it instead of sending
it twice. Without ``--prose`` the queue waits for the turn.

Send the batch (``ArtifactData action=batch writes=<batch.json>``), and once it
has landed, run ``python publish.py --sent``: the projection just sent becomes
the one the next publish compares with, and the turn is appended to
``ui/transcript.md`` (its heading, a ``>`` line per move answered, the prose),
so the transcript stays the record of what the player received. Until then a
publish can be run again as often as needed; it writes the same thing.

The store refuses a ``set`` over a document it holds unless the write names the
version it replaces, so every ``game/`` write is pinned. The versions come from
the page's record, ``ui/page.json`` (committed by ``sheet``): the page's
``url`` and the version of every ``game/`` document as the last sent batch
left it. Only ``publish.py`` writes those documents, so ``--sent`` knows what
each became. ``--sent --url URL`` records the page's link, once, after its
first batch. A version read from the store (``--state``, ``--versions``) wins
over the record; a refused pin means the record is behind (a batch landed
without ``--sent``): list ``game`` and pass what it says as ``--versions``.
One page is one game: ``new`` drops the record, and without one the last
publish is not compared with -- the first publish of a game writes everything.

The inputs, all JSON the keeper writes from what it read:

* ``--prose FILE``: the DM's text for this turn (``ui/scene.md`` in page
  play). A paragraph that is exactly ``[fight]`` is where the turn's next
  fight's card goes. Without it the publish changes the singletons alone
  (``--status dm_thinking``, say).
* ``--moves PATH``: the ``moves`` read from the store, as a list of documents,
  an object of documents by id, or a directory of ``mNNNN.json`` files. Each
  document is its fields plus ``id`` (the doc id, else ``m`` and its seq) and
  ``version`` as read. Every move is deleted; the ones past the last ``lastSeq``
  are the turn's answered moves, and ``lastSeq`` rises to the highest seq read.
  A move is data: ``page.clean_move`` keeps its known fields only, and
  ``python page.py moves`` says what each asks of the DM.
* ``--state FILE``: ``game/state`` as read, with its ``version`` beside its
  fields (or ``--state-version N``). It gives the last ``lastSeq``, the last
  chronicle entry and the last fight, and pins the new state. Without it they
  are read off the last publish, and the state is written unpinned.
* ``--versions FILE``: ``{"game/party": 3, ...}``, the version of any other
  document as read, to pin its write.
* ``--status``: ``awaiting_player`` (the default), ``dm_thinking`` or ``ended``.
* ``--check-in TEXT``: when the DM next looks, for the page's status line
  (``the DM looks <TEXT>``). The DM never looks on its own: the player calls
  each turn from Claude Code, and that is the default.

``web/out/`` is not committed: the save is the game, and this is a copy of what
the page may see.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

import page
import session
from page import (CHECK_IN, STATUSES, clean_move, fight_doc, fight_id,
                  fight_markers, move_words, queued_fights, read_json,
                  read_moves)

DOC_MAX = 256 * 1024         # the store's cap on one document
BATCH_MAX = 50               # the most writes one batch takes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--prose", type=Path)
    parser.add_argument("--moves", type=Path)
    parser.add_argument("--state", type=Path)
    parser.add_argument("--state-version", type=int)
    parser.add_argument("--versions", type=Path)
    parser.add_argument("--status", default="awaiting_player", choices=STATUSES)
    parser.add_argument("--check-in", default=CHECK_IN)
    parser.add_argument("--all", action="store_true",
                        help="write every singleton, changed or not")
    parser.add_argument("--out", type=Path,
                        help="where to write (default: web/out under RPG2_HOME)")
    parser.add_argument("--sent", action="store_true",
                        help="the batch has landed: keep this projection as the last")
    parser.add_argument("--url", help="with --sent: the page the batch landed on")
    args = parser.parse_args()
    out = (args.out or page.default_out()).resolve()
    if args.sent:
        sent(out, args.url)
        return
    if args.url:
        parser.error("--url goes with --sent, once the batch has landed on that page")
    publish(args, out)


# ---------------------------------------------------------------- the publish
def publish(args, out: Path) -> None:
    state = session.load()
    last = out / "last"
    page_file = page.record_path()
    record = read_page(page_file)
    # one page is one game: with no record (a new game), the last publish
    # belongs to another page and is neither compared with nor read from
    compare = page_file.exists()

    # the handshake, from game/state as read, or else from the last publish
    if args.state:
        before = read_json(args.state)
    else:
        before = read_json(last / "game" / "state.json") if compare else None
    before = before if isinstance(before, dict) else {}
    state_version = args.state_version or (before.get("version") if args.state else None)
    last_seq = int(before.get("lastSeq") or 0)
    latest = before.get("latest") or None
    last_fight = before.get("lastFight") or None
    versions = dict(record["versions"])              # as the last sent batch left them
    if args.versions:
        versions.update({k: int(v) for k, v in read_json(args.versions).items()})
    if state_version:
        versions["game/state"] = int(state_version)

    # the moves: every one read is deleted, the new ones are answered
    moves = read_moves(args.moves) if args.moves else []
    answered = [m for m in moves if (m.get("seq") or 0) > last_seq]
    seqs = [m["seq"] for m in moves if isinstance(m.get("seq"), int)]
    new_seq = max([last_seq] + seqs)
    for move in moves:
        if clean_move(move) is None:
            print(f"  move {move['id']} is not a move; deleted unanswered",
                  file=sys.stderr)

    # the fights kept since the last publish go out with the turn's prose;
    # one numbered by a publish whose batch landed (lastFight is past it) is
    # already on the page, and leaves the queue
    queue = page.queue_dir()
    queued = []
    for file, doc in queued_fights(queue):
        if doc.get("id") and last_fight and doc["id"] <= last_fight:
            file.unlink()
            print(f"  {doc['id']} is already on the page; cleared from the queue",
                  file=sys.stderr)
        else:
            queued.append((file, doc))
    fights: list[dict[str, Any]] = []
    if queued and args.prose:
        number = int(last_fight[1:]) if last_fight else 0
        previous = last_fight
        for file, doc in queued:
            number += 1
            fid = fight_id(number)
            continues = previous if doc.get("continuing") else None
            numbered = dict(doc, id=fid, continues=continues)
            file.write_text(json.dumps(numbered, indent=2, ensure_ascii=False) + "\n",
                            encoding="utf-8")
            fights.append(fight_doc(numbered, fid, continues))
            previous = fid
        last_fight = fights[-1]["id"]
    elif queued:
        print(f"  {len(queued)} fight{'s wait' if len(queued) != 1 else ' waits'} "
              f"in {queue} for the turn's --prose", file=sys.stderr)
    # the pause belongs to the newest fight on the page; while a fight still
    # waits in the queue, the page does not have it to point at
    pause_fight = last_fight if state.get("pending") and not (queued and not fights) \
        else None

    # the chronicle entry, when there is prose
    entry = None
    transcript = None
    if args.prose:
        turn = int(latest[1:]) + 1 if latest else 1
        prose = args.prose.read_text(encoding="utf-8")
        entry = page.chronicle_entry(turn, prose, answered, state=state,
                                     fights=[f["id"] for f in fights])
        latest = entry["id"]
        markers = len(fight_markers(entry["prose"]))
        if markers > len(fights):
            print(f"  the prose marks {markers} fight{'s' if markers != 1 else ''} "
                  f"and the turn has {len(fights)}: the spare [fight] "
                  f"paragraph{'s show' if markers - len(fights) != 1 else ' shows'} "
                  f"as written", file=sys.stderr)
        transcript = transcript_turn(entry, fights)

    view = page.player_view(state, status=args.status, last_seq=new_seq,
                            latest=latest, check_in=args.check_in,
                            last_fight=last_fight, pause_fight=pause_fight)

    # clear the last run's files, keep the last publish
    for stale in ("game", "chronicle", "fights", "pending", "batch.json"):
        path = out / stale
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()

    writes: list[dict[str, Any]] = []
    for path in page.SINGLETONS:
        doc = view[path]
        write_json(out / "pending" / f"{path}.json", doc)
        if not args.all and compare and read_json(last / f"{path}.json") == doc:
            continue
        writes.append(set_write(path, write_json(out / f"{path}.json", doc),
                                versions.get(path)))
    for fight in fights:
        path = f"fights/{fight['id']}"
        writes.append(set_write(path, write_json(out / f"{path}.json", fight), None))
    if fights:
        write_json(out / "pending" / "queue.json",
                   [str(file) for file, _ in queued[:len(fights)]])
    if entry is not None:
        path = f"chronicle/{entry['id']}"
        writes.append(set_write(path, write_json(out / f"{path}.json", entry), None))
    for move in moves:
        write = {"op": "delete", "collection": "moves", "doc_id": move["id"]}
        if move.get("version"):
            write["if_version"] = int(move["version"])
        writes.append(write)

    if not writes:
        print("Nothing has changed: no batch to send.")
        return
    if len(writes) > BATCH_MAX:
        sys.exit(f"{len(writes)} writes is more than one batch takes ({BATCH_MAX}); "
                 f"send fewer moves' deletions at a time")
    batch = write_json(out / "batch.json", writes)
    if transcript is not None:
        (out / "pending" / "transcript.md").write_text(transcript, encoding="utf-8")
    # what each game/ document becomes once the batch lands, for --sent
    write_json(out / "pending" / "record.json", {
        "page": str(page_file),
        "transcript": str(session.UI_DIR / "transcript.md"),
        "versions": {f"game/{w['doc_id']}": w.get("if_version", 0) + 1
                     for w in writes if w["op"] == "set" and w["collection"] == "game"}})

    state_doc = view["game/state"]
    print(f"Published day {state_doc['day']} at {state_doc['where']}: lastSeq {new_seq}"
          + (f", {entry['id']} answering {len(entry['answered'])} "
             f"move{'s' if len(entry['answered']) != 1 else ''}" if entry else "")
          + (f" with {len(fights)} fight{'s' if len(fights) != 1 else ''}"
             if fights else "")
          + ".")
    for write in writes:
        pin = f" (if_version {write['if_version']})" if "if_version" in write else ""
        print(f"  {write['op']:<6} {write['collection']}/{write['doc_id']}{pin}")
    unpinned = [f"{w['collection']}/{w['doc_id']}" for w in writes
                if w["op"] == "set" and w["collection"] == "game"
                and "if_version" not in w]
    if unpinned:
        print(f"  not pinned, no version is known: {', '.join(unpinned)}. The store "
              f"refuses these if it holds them already: list game and pass --versions.")
    if record["url"]:
        print(f"Send {batch} as one ArtifactData batch to {record['url']}, then run "
              f"python publish.py --sent.")
    else:
        print(f"Send {batch} as one ArtifactData batch to the page, then run "
              f"python publish.py --sent --url <the page's url>.")


def transcript_turn(entry: dict[str, Any], fights: list[dict[str, Any]]) -> str:
    """The turn as ui/transcript.md keeps it (dm.md's scene-page shape): the
    heading, a ``>`` line per move answered, then the prose, each
    ``[fight]`` paragraph naming the fight it stood for; fights the prose
    did not place follow it."""
    lines = entry["prose"].split("\n")
    names = [f"[fight {f['id']}: {f['title'] or 'a fight'}, {f['outcome']}]"
             for f in fights]
    for n, i in enumerate(fight_markers(entry["prose"])[:len(names)]):
        lines[i] = names[n]
    prose = "\n".join(lines)
    placed = min(len(fight_markers(entry["prose"])), len(names))
    for name in names[placed:]:
        prose += f"\n\n{name}"
    said = "".join(f"> {move_words(m)}\n" for m in entry["answered"])
    return (f"## turn {entry['turn']} (day {entry['day']})\n\n"
            + (said + "\n" if said else "") + prose + "\n")


def sent(out: Path, url: str | None = None) -> None:
    """The batch landed: what was sent is what the next publish compares with.

    The page's record takes the versions the batch left, and ``url`` when
    given; the turn joins the transcript; the sent fights leave the queue.
    """
    pending, last = out / "pending", out / "last"
    if not pending.is_dir():
        sys.exit(f"nothing pending in {out}: publish first")
    record = read_json(pending / "record.json")
    if isinstance(record, dict) and record.get("page"):
        page_file = Path(record["page"])
        kept = read_page(page_file)
        kept["versions"].update(record.get("versions") or {})
        kept["url"] = url or kept["url"]
        write_json(page_file, kept)
        (pending / "record.json").unlink()
    elif url:
        sys.exit(f"no record of the page in {pending}: publish again first")
    turn = pending / "transcript.md"
    if turn.exists() and isinstance(record, dict) and record.get("transcript"):
        target = Path(record["transcript"])
        before = target.read_text(encoding="utf-8") if target.exists() else ""
        gap = "" if not before or before.endswith("\n\n") else (
            "\n" if before.endswith("\n") else "\n\n")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(before + gap + turn.read_text(encoding="utf-8"),
                          encoding="utf-8")
        turn.unlink()
    sent_fights = read_json(pending / "queue.json") or []
    for file in sent_fights:
        Path(file).unlink(missing_ok=True)
    (pending / "queue.json").unlink(missing_ok=True)
    if last.exists():
        shutil.rmtree(last)
    pending.rename(last)
    print(f"Kept as the last publish: {last}."
          + (f" {len(sent_fights)} sent fight{'s' if len(sent_fights) != 1 else ''} "
             f"cleared from the queue." if sent_fights else ""))


# ---------------------------------------------------------------- files
def set_write(path: str, file: Path, version: int | None) -> dict[str, Any]:
    collection, doc_id = path.split("/")
    write = {"op": "set", "collection": collection, "doc_id": doc_id,
             "file_path": str(file)}
    if version:
        write["if_version"] = int(version)
    return write


def write_json(path: Path, doc) -> Path:
    text = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
    if isinstance(doc, dict) and len(text.encode()) > DOC_MAX:
        sys.exit(f"{path} is {len(text.encode())} bytes, over the store's "
                 f"{DOC_MAX}-byte cap")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def read_page(path: Path) -> dict[str, Any]:
    """The page's record: its url and each game/ document's version, as sent."""
    raw = read_json(path)
    raw = raw if isinstance(raw, dict) else {}
    versions = raw.get("versions")
    versions = versions if isinstance(versions, dict) else {}
    return {"url": raw.get("url") if isinstance(raw.get("url"), str) else None,
            "versions": {k: int(v) for k, v in versions.items()
                         if isinstance(v, int) and v > 0}}


if __name__ == "__main__":
    main()
