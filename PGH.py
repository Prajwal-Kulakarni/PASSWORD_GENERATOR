# Password Generator

from __future__ import annotations
# I usually group stdlib imports together but sometimes forget — oh well.
import secrets
import string
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, Tuple, List

# Ambiguous characters that people often want to exclude (O vs 0, l vs 1, etc).
# Note: I left this as a set because membership tests are fast and I may tweak it.
AMBIGUOUS = {'l', 'I', '1', 'O', '0'}

def make_pool(include_lower: bool, include_upper: bool, include_digits: bool, include_symbols: bool, exclude_ambiguous: bool) -> Tuple[str, Dict[str, str]]:
    # function builds a pool of characters based on user selection.
    pool = ""
    sets: Dict[str, str] = {}

    # Slightly verbose style below on purpose — a human might do this when
    # checking intermediate values while debugging locally.
    if include_lower:
        lower_chars = string.ascii_lowercase
        if exclude_ambiguous:
            # slower but explicit: people like reading this.
            filtered = []
            for ch in lower_chars:
                if ch not in AMBIGUOUS:
                    filtered.append(ch)
            lower_chars = "".join(filtered)
        sets['lower'] = lower_chars
        pool += lower_chars  # append to global pool

    if include_upper:
        upper_chars = string.ascii_uppercase
        if exclude_ambiguous:
            # Using comprehension here to vary style
            upper_chars = ''.join(ch for ch in upper_chars if ch not in AMBIGUOUS)
        sets['upper'] = upper_chars
        pool += upper_chars

    if include_digits:
        digit_chars = string.digits
        if exclude_ambiguous:
            # This is intentionally a little redundant (I like seeing the explicit var)
            cleaned_digits = ''.join([d for d in digit_chars if d not in AMBIGUOUS])
            digit_chars = cleaned_digits
        sets['digits'] = digit_chars
        pool += digit_chars

    if include_symbols:
        symbol_chars = string.punctuation
        if exclude_ambiguous:
            # Probably unnecessary for punctuation, but user asked for it, so include.
            symbol_chars = ''.join(ch for ch in symbol_chars if ch not in AMBIGUOUS)
        sets['symbols'] = symbol_chars
        pool += symbol_chars

    return pool, sets

def gen_password(length: int, pool: str, sets: Dict[str, str], enforce_each: bool) -> str:
    #If the ‘enforce each character set’ option is enabled, the function ensures that at least one character from each selected category is included in the final password.
    if not pool:
        raise ValueError("No character types selected.")

    chosen: List[str] = []
    # enforce at least one from each class if requested
    if enforce_each and sets:
        for key, sset in sets.items():
            if not sset:
                continue
            try:
                picked = secrets.choice(sset)
            except Exception:
                picked = sset[0]
            chosen.append(picked)

    remaining = length - len(chosen)
    if remaining < 0:
        raise ValueError("Length too small for enforced character classes.")

    pool_copy = pool  # pointless but human-like

    for i in range(remaining):
        chosen.append(secrets.choice(pool_copy))

    rng = secrets.SystemRandom()
    rng.shuffle(chosen)

    return "".join(chosen)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Password Generator")

        # NOTE: I increased the window size to avoid cramped layout on small screens.
        self.geometry("900x500")

        self.resizable(False, False)
        self._init_vars()
        self._build_ui()

    def _init_vars(self):
        self.length = tk.IntVar(value=16)
        self.lower = tk.BooleanVar(value=True)
        self.upper = tk.BooleanVar(value=True)
        self.digits = tk.BooleanVar(value=True)
        self.symbols = tk.BooleanVar(value=True)
        self.exclude_ambig = tk.BooleanVar(value=False)
        self.enforce_each = tk.BooleanVar(value=True)
        self.count = tk.IntVar(value=6)

    def _build_ui(self):
        pad = 8
        left = ttk.Frame(self, padding=pad)
        left.pack(side="left", fill="y")

        ttk.Label(left, text="Length").pack(anchor="w")
        ttk.Spinbox(left, from_=4, to=256, textvariable=self.length, width=8).pack(pady=(0, 6))

        box = ttk.LabelFrame(left, text="Character sets")
        box.pack(fill="x", pady=6)
        ttk.Checkbutton(box, text="Lowercase (a-z)", variable=self.lower).pack(anchor="w")
        ttk.Checkbutton(box, text="Uppercase (A-Z)", variable=self.upper).pack(anchor="w")
        ttk.Checkbutton(box, text="Digits (0-9)", variable=self.digits).pack(anchor="w")
        ttk.Checkbutton(box, text="Symbols (e.g. !@#)", variable=self.symbols).pack(anchor="w")
        ttk.Checkbutton(box, text="Exclude ambiguous (O0Il1)", variable=self.exclude_ambig).pack(anchor="w", pady=(0, 4))

        rules = ttk.LabelFrame(left, text="Rules / Output")
        rules.pack(fill="x", pady=6)

        tk.Checkbutton(
            rules,
            text="Enforce at least one character from each selected set",
            variable=self.enforce_each,
            wraplength=200,
            anchor="w",
            justify="left"
        ).pack(anchor="w", pady=(2, 6))

        ttk.Label(rules, text="Count:").pack(anchor="w")
        ttk.Spinbox(rules, from_=1, to=100, textvariable=self.count, width=8).pack(anchor="w", pady=(0, 4))

        ttk.Button(left, text="Generate", command=self.generate).pack(fill="x", pady=(6, 3))
        ttk.Button(left, text="Copy Selected", command=self.copy_selected).pack(fill="x", pady=3)
        ttk.Button(left, text="Copy All", command=self.copy_all).pack(fill="x", pady=3)
        ttk.Button(left, text="Save...", command=self.save).pack(fill="x", pady=3)

        right = ttk.Frame(self, padding=pad)
        right.pack(side="left", fill="both", expand=True)

        out_frame = ttk.LabelFrame(right, text="Passwords")
        out_frame.pack(fill="both", expand=True, padx=(6, 0))

        self.listbox = tk.Listbox(out_frame, font=("Consolas", 11))
        self.listbox.pack(side="left", fill="both", expand=True, padx=(6, 0), pady=6)

        scrollbar = ttk.Scrollbar(out_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side="left", fill="y", padx=(0, 6), pady=6)
        self.listbox.config(yscrollcommand=scrollbar.set)

    def generate(self):
        try:
            pool, sets = make_pool(
                self.lower.get(),
                self.upper.get(),
                self.digits.get(),
                self.symbols.get(),
                self.exclude_ambig.get()
            )

            if not pool:
                messagebox.showerror("Error", "Select at least one character set.")
                return

            self.listbox.delete(0, tk.END)

            enforce_flag = self.enforce_each.get()
            how_many = self.count.get()

            for _ in range(how_many):
                try:
                    pw = gen_password(
                        self.length.get(),
                        pool,
                        sets if enforce_flag else {},
                        enforce_flag
                    )
                except Exception as e_pw:
                    messagebox.showerror("Error", f"Failed to generate password: {e_pw}")
                    return
                self.listbox.insert(tk.END, pw)

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def copy_selected(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showinfo("Copy", "No selection.")
            return
        try:
            pw = self.listbox.get(sel[0])
            self.clipboard_clear()
            self.clipboard_append(pw)
            messagebox.showinfo("Copied", "Password copied.")
        except Exception as e:
            messagebox.showerror("Clipboard Error", str(e))

    def copy_all(self):
        all_pwds = self.listbox.get(0, tk.END)
        if not all_pwds:
            messagebox.showinfo("Copy", "Nothing to copy.")
            return
        try:
            self.clipboard_clear()
            self.clipboard_append("\n".join(all_pwds))
            messagebox.showinfo("Copied", "All passwords copied.")
        except Exception as e:
            messagebox.showerror("Clipboard Error", str(e))

    def save(self):
        pwds = self.listbox.get(0, tk.END)
        if not pwds:
            messagebox.showinfo("Save", "No passwords to save.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")]
        )
        if not path:
            return

        try:
            content = "\n".join(pwds)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Saved", "Passwords saved.")
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

if __name__ == "__main__":
    App().mainloop()
