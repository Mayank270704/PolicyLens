"""Task 3 — lightweight local annotation interface.

A single-file Tkinter app (stdlib only -- no new dependencies, no cloud
APIs, fine for a CPU-only 8 GB laptop). Shows one comment at a time with
its policy context/section, lets the annotator pick a stance OR an
exclusion code (mutually exclusive), a confidence level, and free-text
notes, then saves to the batch CSV atomically.

It never pre-fills, predicts, or suggests a label -- every field starts
exactly as it was loaded from disk.

Usage:
    python scripts/annotation/gui.py                         # main batch
    python scripts/annotation/gui.py --batch data/annotations/new_experiment/repeat_pass_batch.csv
"""
from __future__ import annotations

import argparse
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from scripts.annotation import schema, state
else:
    from . import schema, state

FILTER_ALL = "All"
FILTER_PENDING = "Pending"
FILTER_COMPLETED = "Completed"
FILTER_EXCLUDED = "Excluded"
FILTER_OPTIONS = (FILTER_ALL, FILTER_PENDING, FILTER_COMPLETED, FILTER_EXCLUDED)


def row_status(row: dict) -> str:
    label = (row.get("annotator_label") or "").strip()
    excl = (row.get("exclusion_code") or "").strip()
    if excl:
        return FILTER_EXCLUDED
    if label:
        return FILTER_COMPLETED
    return FILTER_PENDING


class AnnotationApp:
    def __init__(self, root: tk.Tk, batch_path: Path, backup_path: Path | None):
        self.root = root
        self.batch_path = Path(batch_path)
        self.backup_path = Path(backup_path) if backup_path else self._default_backup_path()

        created = state.ensure_backup(self.batch_path, self.backup_path)
        if created:
            print(f"Created backup of original blank batch: {self.backup_path}")

        self.fieldnames, self.rows = schema.read_rows_with_fieldnames(self.batch_path)
        if not self.rows:
            raise RuntimeError(f"No rows found in {self.batch_path}")

        self.filtered_indices: list[int] = list(range(len(self.rows)))
        self.pos_in_filtered = 0
        self.dirty = False

        self.root.title(f"PolicyLens Annotation -- {self.batch_path.name}")
        self.root.geometry("980x760")

        self._build_widgets()

        start_index = min(state.get_last_index(self.batch_path), len(self.rows) - 1)
        self._jump_to_row_index(max(start_index, 0))
        self._refresh_progress_label()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _default_backup_path(self) -> Path:
        return self.batch_path.with_name(self.batch_path.stem + ".original_backup" + self.batch_path.suffix)

    # ---- UI construction -------------------------------------------------

    def _build_widgets(self) -> None:
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill="x")

        self.progress_label = ttk.Label(top, text="", font=("Segoe UI", 10, "bold"))
        self.progress_label.pack(side="left")

        ttk.Label(top, text="   Filter:").pack(side="left")
        self.filter_var = tk.StringVar(value=FILTER_ALL)
        filter_combo = ttk.Combobox(
            top, textvariable=self.filter_var, values=FILTER_OPTIONS, state="readonly", width=12
        )
        filter_combo.pack(side="left", padx=4)
        filter_combo.bind("<<ComboboxSelected>>", lambda e: self._apply_filter())

        meta = ttk.LabelFrame(self.root, text="Context", padding=8)
        meta.pack(fill="x", padx=8, pady=(0, 4))
        self.id_label = ttk.Label(meta, text="", font=("Segoe UI", 9, "bold"))
        self.id_label.pack(anchor="w")
        self.context_label = ttk.Label(meta, text="", wraplength=920, justify="left")
        self.context_label.pack(anchor="w", pady=(2, 0))
        self.section_label = ttk.Label(meta, text="", wraplength=920, justify="left", foreground="#444")
        self.section_label.pack(anchor="w", pady=(2, 0))

        text_frame = ttk.LabelFrame(self.root, text="Comment text", padding=8)
        text_frame.pack(fill="both", expand=False, padx=8, pady=4)
        self.comment_text = tk.Text(text_frame, height=8, wrap="word")
        self.comment_text.pack(fill="both", expand=True)
        self.comment_text.configure(state="disabled")

        choices = ttk.Frame(self.root, padding=8)
        choices.pack(fill="x", padx=8)

        stance_frame = ttk.LabelFrame(choices, text="Stance label", padding=8)
        stance_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.stance_var = tk.StringVar(value="")
        for label in schema.STANCE_LABELS:
            ttk.Radiobutton(
                stance_frame, text=label, value=label, variable=self.stance_var,
                command=self._on_stance_selected,
            ).pack(anchor="w")

        excl_frame = ttk.LabelFrame(choices, text="Exclusion code (instead of a stance)", padding=8)
        excl_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 8))
        self.exclusion_var = tk.StringVar(value="")
        for code in schema.EXCLUSION_CODES:
            ttk.Radiobutton(
                excl_frame, text=code, value=code, variable=self.exclusion_var,
                command=self._on_exclusion_selected,
            ).pack(anchor="w")

        conf_frame = ttk.LabelFrame(choices, text="Confidence", padding=8)
        conf_frame.grid(row=0, column=2, sticky="nsew")
        self.confidence_var = tk.StringVar(value="")
        for value, text in schema.CONFIDENCE_LABELS.items():
            ttk.Radiobutton(
                conf_frame, text=f"{text} ({value})", value=value, variable=self.confidence_var,
            ).pack(anchor="w")

        choices.grid_columnconfigure(0, weight=1)
        choices.grid_columnconfigure(1, weight=1)
        choices.grid_columnconfigure(2, weight=1)

        notes_frame = ttk.LabelFrame(self.root, text="Annotation notes", padding=8)
        notes_frame.pack(fill="both", expand=True, padx=8, pady=4)
        self.notes_text = tk.Text(notes_frame, height=4, wrap="word")
        self.notes_text.pack(fill="both", expand=True)

        nav = ttk.Frame(self.root, padding=8)
        nav.pack(fill="x")
        ttk.Button(nav, text="<< Previous", command=self._go_previous).pack(side="left")
        ttk.Button(nav, text="Next >>", command=self._go_next).pack(side="left", padx=6)
        ttk.Button(nav, text="Save", command=lambda: self._save_current(advance=False)).pack(side="left", padx=20)
        ttk.Button(nav, text="Save && Next", command=lambda: self._save_current(advance=True)).pack(side="left")
        ttk.Button(nav, text="Clear annotation", command=self._clear_current_fields).pack(side="left", padx=20)
        ttk.Label(nav, text="  (stance and exclusion are mutually exclusive)", foreground="#777").pack(side="left", padx=10)

        for var in (self.stance_var, self.exclusion_var, self.confidence_var):
            var.trace_add("write", lambda *_: self._mark_dirty())
        self.notes_text.bind("<<Modified>>", self._on_notes_modified)

    # ---- stance/exclusion mutual exclusivity -----------------------------

    def _on_stance_selected(self) -> None:
        if self.stance_var.get():
            self.exclusion_var.set("")

    def _on_exclusion_selected(self) -> None:
        if self.exclusion_var.get():
            self.stance_var.set("")

    def _on_notes_modified(self, _event) -> None:
        self.comment_notes_modified_flag = True
        self._mark_dirty()
        self.notes_text.edit_modified(False)

    def _mark_dirty(self) -> None:
        self.dirty = True

    # ---- filtering & navigation -------------------------------------------

    def _build_filtered_indices(self, choice: str) -> list[int]:
        if choice == FILTER_ALL:
            return list(range(len(self.rows)))
        return [i for i, r in enumerate(self.rows) if row_status(r) == choice]

    def _apply_filter(self) -> None:
        if not self._confirm_discard_if_dirty():
            self.filter_var.set(self._current_filter_name_before_change)
            return
        choice = self.filter_var.get()
        self.filtered_indices = self._build_filtered_indices(choice)
        if not self.filtered_indices:
            messagebox.showinfo("No items", f"No rows match filter '{choice}'.")
            self.filtered_indices = list(range(len(self.rows)))
            self.filter_var.set(FILTER_ALL)
        self.pos_in_filtered = 0
        self._load_row(self.filtered_indices[0])

    def _refresh_filtered_indices_after_save(self, saved_row_index: int) -> None:
        """A save can change which filter bucket the current row belongs to
        (e.g. Pending -> Completed). Rebuild the active filter's index list
        so Previous/Next reflect the new state immediately, instead of
        navigating a stale list that still contains items that no longer
        match the selected filter."""
        choice = self.filter_var.get()
        new_indices = self._build_filtered_indices(choice)
        if not new_indices:
            messagebox.showinfo(
                "Filter complete", f"No more items match filter '{choice}'. Switching to 'All'."
            )
            self.filter_var.set(FILTER_ALL)
            new_indices = self._build_filtered_indices(FILTER_ALL)
        if saved_row_index in new_indices:
            self.pos_in_filtered = new_indices.index(saved_row_index)
        else:
            self.pos_in_filtered = min(self.pos_in_filtered, len(new_indices) - 1)
        self.filtered_indices = new_indices

    @property
    def _current_filter_name_before_change(self) -> str:
        return getattr(self, "_last_filter", FILTER_ALL)

    def _jump_to_row_index(self, row_index: int) -> None:
        self.filtered_indices = list(range(len(self.rows)))
        if row_index in self.filtered_indices:
            self.pos_in_filtered = self.filtered_indices.index(row_index)
        self._load_row(row_index)

    def _go_previous(self) -> None:
        if not self._confirm_discard_if_dirty():
            return
        if self.pos_in_filtered > 0:
            self.pos_in_filtered -= 1
            self._load_row(self.filtered_indices[self.pos_in_filtered])

    def _go_next(self) -> None:
        if not self._confirm_discard_if_dirty():
            return
        if self.pos_in_filtered < len(self.filtered_indices) - 1:
            self.pos_in_filtered += 1
            self._load_row(self.filtered_indices[self.pos_in_filtered])
        else:
            messagebox.showinfo("End of list", "This is the last item in the current filter.")

    def _confirm_discard_if_dirty(self) -> bool:
        """Returns True if it's OK to navigate away (either not dirty, or
        the user explicitly saved/discarded)."""
        if not self.dirty:
            return True
        choice = messagebox.askyesnocancel(
            "Unsaved changes",
            "This item has unsaved changes. Save before moving on?\n\n"
            "Yes = save, No = discard changes, Cancel = stay here.",
        )
        if choice is None:
            return False
        if choice is True:
            return self._save_current(advance=False, from_guard=True)
        self.dirty = False
        return True

    # ---- loading / saving a row -------------------------------------------

    def _load_row(self, row_index: int) -> None:
        self._last_filter = self.filter_var.get()
        row = self.rows[row_index]
        self.current_row_index = row_index
        self.comment_notes_modified_flag = False

        self.id_label.config(text=f"{row.get('comment_id')}  "
                                   f"[{row.get('source_dataset')} | {row.get('language')} | "
                                   f"{row.get('word_count')} words]")
        self.context_label.config(text=f"Policy context: {row.get('policy_context', '')}")
        self.section_label.config(text=f"Policy section: {row.get('policy_section', '')}")

        self.comment_text.configure(state="normal")
        self.comment_text.delete("1.0", "end")
        self.comment_text.insert("1.0", row.get("comment_text", ""))
        self.comment_text.configure(state="disabled")

        self.stance_var.set(row.get("annotator_label", "") or "")
        self.exclusion_var.set(row.get("exclusion_code", "") or "")
        self.confidence_var.set(row.get("annotation_confidence", "") or "")

        self.notes_text.delete("1.0", "end")
        self.notes_text.insert("1.0", row.get("annotation_notes", "") or "")
        self.notes_text.edit_modified(False)

        self.dirty = False
        state.set_last_index(self.batch_path, row_index)
        self._refresh_progress_label()

    def _refresh_progress_label(self) -> None:
        total = len(self.rows)
        done = sum(1 for r in self.rows if row_status(r) != FILTER_PENDING)
        pct = round(done / total * 100, 1) if total else 0.0
        pos_in_filter = self.pos_in_filtered + 1
        filter_total = len(self.filtered_indices)
        self.progress_label.config(
            text=f"Item {pos_in_filter}/{filter_total} (filter: {self.filter_var.get()})   |   "
                 f"Overall: {done}/{total} done ({pct}%)"
        )

    def _save_current(self, advance: bool, from_guard: bool = False) -> bool:
        row = self.rows[self.current_row_index]
        cid = row.get("comment_id", "<unknown>")

        new_label = self.stance_var.get().strip()
        new_excl = self.exclusion_var.get().strip()
        new_conf = self.confidence_var.get().strip()
        new_notes = self.notes_text.get("1.0", "end").strip()

        if new_label and new_excl:
            messagebox.showerror(
                "Invalid state", "A comment cannot have both a stance label and an exclusion code. "
                                 "Choosing one automatically clears the other -- please re-check."
            )
            return False

        if new_label and not new_conf:
            if not messagebox.askyesno(
                "No confidence set",
                "No confidence level is set for this stance label. Save anyway?",
            ):
                return False

        if new_label == "Unclear" and not new_notes:
            messagebox.showerror(
                "Notes required",
                "annotation_notes is required for every Unclear label "
                "(STANCE_ANNOTATION_GUIDELINES.md section 3, step 9). Please add a short "
                "justification before saving.",
            )
            return False

        old_label = (row.get("annotator_label") or "").strip()
        old_excl = (row.get("exclusion_code") or "").strip()
        is_overwrite = bool(old_label or old_excl) and (
            old_label != new_label or old_excl != new_excl
        )
        if is_overwrite:
            if not messagebox.askyesno(
                "Overwrite existing annotation?",
                f"{cid} already has an annotation (label='{old_label or '-'}', "
                f"exclusion='{old_excl or '-'}'). Overwrite it?\n\n"
                "This will be recorded in the audit log.",
            ):
                return False
            state.append_audit_entry(
                self.batch_path, cid, old_label, old_excl, new_label, new_excl
            )

        row["annotator_label"] = new_label
        row["exclusion_code"] = new_excl
        row["annotation_confidence"] = new_conf
        row["annotation_notes"] = new_notes

        schema.write_rows_atomic(self.batch_path, self.rows, self.fieldnames)
        self.dirty = False
        state.append_timing_event(self.batch_path, cid, action="overwrite" if is_overwrite else "saved")
        just_completed = state.mark_complete_if_needed(self.batch_path, self.rows)
        if just_completed:
            messagebox.showinfo(
                "Batch complete",
                f"All {len(self.rows)} rows in {self.batch_path.name} now have a label or "
                "exclusion code. Completion timestamp recorded for the repeat-annotation gate.",
            )

        self._refresh_filtered_indices_after_save(self.current_row_index)
        self._refresh_progress_label()

        if advance and not from_guard:
            if self.pos_in_filtered < len(self.filtered_indices) - 1:
                self.pos_in_filtered += 1
                self._load_row(self.filtered_indices[self.pos_in_filtered])
        return True

    def _clear_current_fields(self) -> None:
        """Reset the current item's stance/exclusion/confidence/notes back
        to blank (pending) in the UI. Nothing is written to disk until the
        annotator explicitly clicks Save -- this only clears the in-memory
        form fields, and a Save after clearing an already-saved item still
        goes through the normal overwrite confirmation + audit log."""
        if not any([self.stance_var.get(), self.exclusion_var.get(),
                    self.confidence_var.get(), self.notes_text.get("1.0", "end").strip()]):
            return
        if not messagebox.askyesno(
            "Clear annotation",
            "Clear the stance/exclusion/confidence/notes fields for this item? "
            "You will still need to click Save for this to take effect.",
        ):
            return
        self.stance_var.set("")
        self.exclusion_var.set("")
        self.confidence_var.set("")
        self.notes_text.delete("1.0", "end")
        self._mark_dirty()

    def _on_close(self) -> None:
        if self._confirm_discard_if_dirty():
            self.root.destroy()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Local annotation interface.")
    parser.add_argument("--batch", type=Path, default=schema.MAIN_BATCH_PATH)
    parser.add_argument("--backup", type=Path, default=None)
    args = parser.parse_args(argv)

    if not args.batch.exists():
        print(f"Batch file not found: {args.batch}")
        return 1

    root = tk.Tk()
    try:
        AnnotationApp(root, args.batch, args.backup)
    except RuntimeError as e:
        print(f"Error: {e}")
        return 1
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
