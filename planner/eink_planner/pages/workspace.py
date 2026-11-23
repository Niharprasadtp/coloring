"""Brain Dump pages and the Projects & Work hub."""

from __future__ import annotations

from ..geometry import Rect
from ..ink import BOLD, REGULAR
from ..widgets import button, button_width, checklist, lines_box, page_header, section, table
from ..builder import N_BRAIN_DUMP, N_PROJECTS

BRAIN_DUMP_KINDS = ["grid", "dots", "blank", "grid", "dots"]


# --- brain dump ---------------------------------------------------------------------------
def brain_dump(P, spec) -> None:
    ink, m = P.ink, P.m
    i = spec.data["index"]
    buttons = [(str(n), f"bd-{n}", n == i) for n in range(1, N_BRAIN_DUMP + 1)]
    body = page_header(ink, P.content, "Brain Dump", f"Page {i} of {N_BRAIN_DUMP}", buttons=buttons)
    kind = BRAIN_DUMP_KINDS[(i - 1) % len(BRAIN_DUMP_KINDS)]
    if kind == "grid":
        ink.grid(body)
    elif kind == "dots":
        ink.dots(body)


# --- shared --------------------------------------------------------------------------------
def field(ink, r: Rect, label: str) -> None:
    m, t = ink.m, ink.t
    ink.text(r.x, r.top - m.fs_small * 0.75, label.upper(), m.fs_small, BOLD, t.muted,
             tracking=m.fs_small * 0.06)
    ink.line(r.x, r.y, r.right, r.y, t.rule, m.lw_rule)


def _project_header(P, n: int, page: str) -> Rect:
    m = P.m
    names = {"plan": "Plan", "board": "Timeline & Board", "notes": "Meeting Notes"}
    buttons = [("Index", "projects")] + [
        (lbl, f"p{n}-{pg}", pg == page) for pg, lbl in (("plan", "Plan"), ("board", "Board"),
                                                         ("notes", "Notes"))]
    arrows = {} if m.compact else {
        "prev": f"p{n - 1}-{page}" if n > 1 else None,
        "next": f"p{n + 1}-{page}" if n < N_PROJECTS else None}
    return page_header(P.ink, P.content, f"Project {n:02d}", names[page], buttons=buttons, **arrows)


# --- index --------------------------------------------------------------------------------
def project_index(P, spec) -> None:
    ink, m, t = P.ink, P.m, P.t
    body = page_header(ink, P.content, "Projects", f"{N_PROJECTS} project hubs")
    labels = [("Plan", "plan"), ("Board", "board"), ("Notes", "notes")]
    bw = max(button_width(ink, lb) for lb, _ in labels)
    btn_block = 3 * bw + 2 * m.gap
    vgap = m.gap * 1.5
    # Flow into more columns when ten rows would be shorter than a tap target.
    for ncols in (1, 2, 3):
        per = -(-N_PROJECTS // ncols)
        row_h = (body.h - m.mm(5) - (per - 1) * vgap) / per
        if row_h >= m.tap:
            break
    row_h = min(row_h, m.mm(17))
    for c, col in enumerate(body.cols(ncols, m.space * 2)):
        hdr, rows_r = col.take_top(m.mm(5))
        ink.text(rows_r.x, hdr.y + m.mm(1.5), "#", m.fs_small, BOLD, t.muted)
        ink.text(rows_r.x + m.tap + m.mm(3), hdr.y + m.mm(1.5), "PROJECT", m.fs_small, BOLD,
                 t.muted, tracking=m.fs_small * 0.06)
        ink.text(rows_r.right - btn_block, hdr.y + m.mm(1.5), "OPEN", m.fs_small, BOLD, t.muted,
                 tracking=m.fs_small * 0.06)
        for k in range(per):
            i = c * per + k + 1
            if i > N_PROJECTS:
                break
            y = rows_r.top - (k + 1) * row_h - k * vgap
            row = Rect(rows_r.x, y, rows_r.w, row_h)
            num, rest = row.take_left(max(m.tap, min(row_h * 0.9, m.mm(14))), m.mm(3))
            button(ink, num, f"{i:02d}", f"p{i}-plan", fill=t.qt((i - 1) % 4 + 1), size=m.fs_h)
            btns, name = rest.take_right(btn_block, m.mm(3))
            bh = min(m.tap, row.h)
            for j, (lb, pg) in enumerate(labels):
                button(ink, Rect(btns.x + j * (bw + m.gap), row.cy - bh / 2, bw, bh), lb,
                       f"p{i}-{pg}")
            if not m.compact and name.w > m.mm(60):
                nm, due = name.take_right(name.w * 0.28, m.mm(3))
                field(ink, Rect(due.x, row.y + m.mm(1.5), due.w, row.h * 0.6), "Due")
                name = nm
            field(ink, Rect(name.x, row.y + m.mm(1.5), name.w, row.h * 0.6), "Name")


# --- hub pages -------------------------------------------------------------------------------
def project_plan(P, spec) -> None:
    ink, m, t = P.ink, P.m, P.t
    n = spec.data["n"]
    body = _project_header(P, n, "plan")
    sp = m.space * 1.5
    fh = m.mm(8 if m.compact else 9.5)
    milestones = [("Milestone", 4), ("Due", 1.4), ("Done", 1)]
    if P.opts.landscape:
        left, right = body.cols([0.45, 0.55], sp * 1.3)
    else:
        left = right = None
    col = left or body
    name_r, col = col.take_top(fh, sp)
    field(ink, name_r, "Project name")
    meta, col = col.take_top(fh, sp)
    for lb, c in zip(("Start", "Due", "Owner", "Status"), meta.cols(4, m.space)):
        field(ink, c, lb)
    goal, col = col.take_top(m.fs_label * 0.7 + m.mm(1.6) + 3 * m.ruled, sp)
    lines_box(ink, goal, "Goal / outcome")
    if left:
        checklist(ink, col, "Next actions")
        miles, notes = right.rows([0.55, 0.45], sp)
        table(ink, section(ink, miles, "Milestones"), milestones)
        lines_box(ink, notes, "Notes", kind="grid")
    else:
        miles, low = col.rows([0.42, 0.58], sp)
        table(ink, section(ink, miles, "Milestones"), milestones)
        acts, notes = low.cols(2, sp)
        checklist(ink, acts, "Next actions")
        lines_box(ink, notes, "Notes", kind="grid")


def project_board(P, spec) -> None:
    ink, m, t = P.ink, P.m, P.t
    n = spec.data["n"]
    body = _project_header(P, n, "board")
    sp = m.space * 1.5
    tl, kb = body.rows([0.36, 0.64], sp)

    # Timeline: task lanes x weeks.
    tb = section(ink, tl, "Timeline")
    n_cols = 8 if m.compact else 12
    name_w = tb.w * (0.28 if m.compact else 0.22)
    hdr, lanes = tb.take_top(m.mm(5))
    cols = Rect(tb.x + name_w, lanes.y, tb.w - name_w, lanes.h).cols(n_cols)
    ink.text(tb.x, hdr.y + m.mm(1.4), "TASK", m.fs_small, BOLD, t.muted)
    for i, c in enumerate(cols, 1):
        ink.box(Rect(c.x + m.mm(0.3), hdr.y + m.mm(0.3), c.w - m.mm(0.6), hdr.h - m.mm(0.6)),
                stroke=t.grid, width=m.lw_grid, radius=m.radius * 0.5)
        ink.line(c.x, lanes.y, c.x, lanes.top, t.grid, m.lw_grid)
    ink.hlines(lanes, lanes.h / 6, top_line=True)

    # Kanban: three columns of dashed cards.
    kr = section(ink, kb, "Kanban board")
    card_h = m.mm(12 if m.compact else 16)
    for q, (title, col) in enumerate(zip(("To do", "Doing", "Done"), kr.cols(3, m.space)), 1):
        head, rest = col.take_top(m.mm(7 if m.compact else 8), m.mm(2))
        ink.box(head, fill=t.qt(q), radius=m.radius)
        ink.text_in(head, title.upper(), m.fs_label, BOLD, t.soft, tracking=m.fs_label * 0.08)
        k = int((rest.h + m.mm(2)) // (card_h + m.mm(2)))
        for j in range(k):
            card = Rect(rest.x, rest.top - (j + 1) * card_h - j * m.mm(2), rest.w, card_h)
            ink.box(card, stroke=t.rule, width=m.lw_grid, radius=m.radius,
                    dash=[m.mm(0.8), m.mm(0.8)])


def project_notes(P, spec) -> None:
    ink, m, t = P.ink, P.m, P.t
    n = spec.data["n"]
    body = _project_header(P, n, "notes")
    sp = m.space * 1.5
    fh = m.mm(8 if m.compact else 9.5)
    meta, body = body.take_top(fh, sp)
    for lb, c in zip(("Meeting", "Date", "Time"), meta.cols([2, 1, 1], m.space)):
        field(ink, c, lb)
    att, body = body.take_top(fh, sp)
    field(ink, att, "Attendees")
    agenda, body = body.take_top(m.fs_label + 3 * m.ruled * 0.9, sp)
    lines_box(ink, agenda, "Agenda", step=m.ruled * 0.9)
    notes, actions = body.rows([0.58, 0.42], sp)
    lines_box(ink, notes, "Notes")
    if m.compact:
        checklist(ink, actions, "Action items")
    else:
        act, dec = actions.cols([0.62, 0.38], sp)
        table(ink, section(ink, act, "Action items"), [("Task", 4), ("Owner", 1.6), ("Due", 1.2), ("Done", 0.9)])
        lines_box(ink, dec, "Decisions")
