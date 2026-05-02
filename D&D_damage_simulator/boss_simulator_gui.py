import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import re

import requests

from attack_context import AttackContext
from character import Character
from spell_context import SpellContext


class BossSimulatorGUI:

    STAT_CHOICES = ["str", "dex", "con", "int", "wis", "cha"]
    _OPEN5E_URL = "https://api.open5e.com/v1/monsters/"

    def __init__(self, parent_gui):
        self.parent = parent_gui
        self.master = parent_gui.master

        self.characters = parent_gui.characters
        self.spell_mapping = parent_gui.spell_mapping
        self.class_mapping = parent_gui.class_mapping
        self.subclass_mapping = parent_gui.subclass_mapping
        self.modifier_mapping = parent_gui.modifier_mapping
        self.weapon_mapping = parent_gui.weapon_mapping

        self.win = None
        self.mode_var = None
        self.priority_var = None
        self.result_text = None
        self.simulate_btn = None
        self.enemy_rows = []
        self.char_rows = []

        self._monster_cache = []
        self._search_var = None
        self._monster_listbox = None
        self._import_status_var = None

        self._build_ui()

    def show(self):
        if self.win is not None:
            self.win.lift()
            self.win.focus_force()

    def _build_ui(self):
        self.win = tk.Toplevel(self.master)
        self.win.title("Combat Simulator")
        try:
            self.win.state("zoomed")  # works on Windows, some X11 window managers
        except tk.TclError:
            # Fallback: manually set to screen size if 'zoomed' not supported
            self.win.geometry(f"{self.win.winfo_screenwidth()}x{self.win.winfo_screenheight()}+0+0")
        self.win.minsize(950, 600)

        spell_choices = ["None"] + sorted(self.spell_mapping.keys())

        top_area = tk.Frame(self.win)
        top_area.pack(fill="both", expand=True, padx=10, pady=(10, 6))

        top_panes = tk.PanedWindow(top_area, orient=tk.HORIZONTAL, sashrelief="raised", bd=0)
        top_panes.pack(fill="both", expand=True)

        party_frame = tk.LabelFrame(top_panes, text="Party Selector")
        enemy_frame = tk.LabelFrame(top_panes, text="Enemies")

        top_panes.add(party_frame, minsize=675)
        top_panes.add(enemy_frame, minsize=450)

        self._build_character_table(spell_choices, parent=party_frame)
        self._build_enemy_section(parent=enemy_frame)

        self._build_open5e_section(parent=self.win)

        # Roll mode
        options_frame = tk.Frame(self.win)
        options_frame.pack(fill="x", padx=10, pady=(2, 0))

        tk.Label(options_frame, text="Roll Mode:").pack(side="left")
        self.mode_var = tk.StringVar(value="normal")

        for label, val in [
            ("Normal", "normal"),
            ("Advantage", "advantage"),
            ("Disadvantage", "disadvantage"),
        ]:
            tk.Radiobutton(options_frame, text=label, variable=self.mode_var, value=val).pack(side="left")

        # Target priority
        priority_frame = tk.Frame(self.win)
        priority_frame.pack(fill="x", padx=10, pady=(2, 0))

        tk.Label(priority_frame, text="Party Targets:").pack(side="left")
        self.priority_var = tk.StringVar(value="boss_first")

        for label, val in [
            ("Boss First", "boss_first"),
            ("Adds First", "adds_first"),
            ("Random", "random"),
        ]:
            tk.Radiobutton(priority_frame, text=label, variable=self.priority_var, value=val).pack(side="left")

        # Result window
        out_frame = tk.LabelFrame(self.win, text="Result")
        out_frame.pack(fill="both", expand=True, padx=10, pady=(6, 4))

        self.result_text = tk.Text(out_frame, height=12, wrap="word")
        self.result_text.pack(fill="both", expand=True, padx=6, pady=6)

        # Button
        btn_frame = tk.Frame(self.win)
        btn_frame.pack(fill="x", padx=10, pady=(0, 8))

        self.simulate_btn = tk.Button(btn_frame, text="Run Simulation", command=self.simulate)
        self.simulate_btn.pack(pady=2)

    def _build_open5e_section(self, parent):
        frame = tk.LabelFrame(parent, text="Import Monsters")
        frame.pack(fill="x", padx=10, pady=(0, 6))

        search_row = tk.Frame(frame)
        search_row.pack(fill="x", padx=6, pady=(6, 2))

        tk.Label(search_row, text="Search:").pack(side="left")

        self._search_var = tk.StringVar()
        search_entry = tk.Entry(search_row, textvariable=self._search_var, width=28)
        search_entry.pack(side="left", padx=(4, 2))
        search_entry.bind("<Return>", lambda e: self._on_search())

        tk.Button(search_row, text="Search", command=self._on_search).pack(side="left", padx=2)

        self._import_status_var = tk.StringVar(value="")
        tk.Label(search_row, textvariable=self._import_status_var, fg="gray").pack(side="left", padx=8)

        list_row = tk.Frame(frame)
        list_row.pack(fill="x", padx=6, pady=(0, 6))

        scrollbar = tk.Scrollbar(list_row)
        self._monster_listbox = tk.Listbox(list_row, height=10, yscrollcommand=scrollbar.set)
        scrollbar.config(command=self._monster_listbox.yview)

        self._monster_listbox.pack(side="left", fill="x", expand=True)
        scrollbar.pack(side="left", fill="y")

        button_col = tk.Frame(list_row)
        button_col.pack(side="left", padx=8, pady=4)

        tk.Button(
            button_col,
            text="Add to Enemies →",
            command=self._on_import_selected
        ).pack(fill="x", pady=(0, 4))

        tk.Button(
            button_col,
            text="+ Add Custom",
            command=self.add_enemy_row
        ).pack(fill="x")


    def _build_enemy_section(self, parent):
        enemy_outer_frame = parent
        enemy_outer_frame.config(height = 160)
        enemy_outer_frame.pack_propagate(False)

        # Header
        enemy_header_font = ("TkDefaultFont", 9, "bold")
        enemy_header_frame = tk.Frame(enemy_outer_frame)
        enemy_header_frame.pack(side="top", fill="x", padx=4, pady=(6, 0))

        enemy_col_widths = {
            0: 30, 1: 120, 2: 80, 3: 55, 4: 50,
            5: 55, 6: 50, 7: 65, 8: 65, 9: 36,
        }
        for col, minsize in enemy_col_widths.items():
            enemy_header_frame.grid_columnconfigure(col, minsize=minsize)

        headers = ["In", "Name", "Role", "HP", "AC", "To hit", "Atks", "Dmg/Atk", "Init", ""]
        for col, text in enumerate(headers):
            tk.Label(
                enemy_header_frame,
                text=text,
                font=enemy_header_font,
                anchor="w",
            ).grid(row=0, column=col, padx=2, pady=2, sticky="w")

        # Scrollable enemy rows
        enemy_canvas_frame = tk.Frame(enemy_outer_frame)
        enemy_canvas_frame.pack(side="top", fill="both", expand=True, padx=4, pady=(0, 4))

        self.enemy_canvas = tk.Canvas(enemy_canvas_frame, highlightthickness=0)
        enemy_scroll = tk.Scrollbar(enemy_canvas_frame, orient="vertical", command=self.enemy_canvas.yview)
        self.enemy_canvas.configure(yscrollcommand=enemy_scroll.set)

        enemy_scroll.pack(side="right", fill="y")
        self.enemy_canvas.pack(side="left", fill="both", expand=True)

        self.enemy_inner = tk.Frame(self.enemy_canvas)
        self._enemy_window = self.enemy_canvas.create_window((0, 0), window=self.enemy_inner, anchor="nw")

        self.enemy_inner.bind("<Configure>", self._on_enemy_configure)
        self.enemy_canvas.bind("<Configure>", self._on_enemy_canvas_resize)

        self.add_enemy_row(
            name="Boss", role="Boss", hp="200", ac="15", to_hit="3",
            attacks="3", damage="15", init_bonus="2",
        )

    def _on_enemy_configure(self, event):
        self.enemy_canvas.configure(scrollregion=self.enemy_canvas.bbox("all"))

    def _on_enemy_canvas_resize(self, event):
        self.enemy_canvas.itemconfig(self._enemy_window, width=event.width)

    def add_enemy_row(self, name="Enemy", role="Add", hp="50", ac="15",
                      to_hit="2", attacks="1", damage="10", init_bonus="0"):
        row_idx = len(self.enemy_rows)
        row_frame = tk.Frame(self.enemy_inner)
        row_frame.grid(row=row_idx, column=0, columnspan=10, sticky="ew", pady=1)

        enemy_col_widths = {
            0: 30, 1: 120, 2: 80, 3: 55, 4: 50,
            5: 55, 6: 50, 7: 65, 8: 65, 9: 36,
        }
        for col, minsize in enemy_col_widths.items():
            row_frame.grid_columnconfigure(col, minsize=minsize)

        enabled_var  = tk.BooleanVar(value=True)
        name_var     = tk.StringVar(value=name)
        role_var     = tk.StringVar(value=role)
        hp_var       = tk.StringVar(value=hp)
        ac_var       = tk.StringVar(value=ac)
        to_hit_var   = tk.StringVar(value=to_hit)
        attacks_var  = tk.StringVar(value=attacks)
        damage_var   = tk.StringVar(value=damage)
        init_var     = tk.StringVar(value=init_bonus)

        tk.Checkbutton(row_frame, variable=enabled_var).grid(row=0, column=0, padx=2)
        tk.Entry(row_frame, textvariable=name_var, width=14).grid(row=0, column=1, padx=2)
        role_menu = tk.OptionMenu(row_frame, role_var, "Boss", "Add", "Minion")
        role_menu.config(width=5)
        role_menu.grid(row=0, column=2, padx=2)
        tk.Entry(row_frame, textvariable=hp_var,      width=7).grid(row=0, column=3, padx=2)
        tk.Entry(row_frame, textvariable=ac_var,      width=6).grid(row=0, column=4, padx=2)
        tk.Entry(row_frame, textvariable=to_hit_var,  width=6).grid(row=0, column=5, padx=2)
        tk.Entry(row_frame, textvariable=attacks_var, width=6).grid(row=0, column=6, padx=2)
        tk.Entry(row_frame, textvariable=damage_var,  width=8).grid(row=0, column=7, padx=2)
        tk.Entry(row_frame, textvariable=init_var,    width=8).grid(row=0, column=8, padx=2)

        row_data = (
            enabled_var, row_frame, name_var, role_var,
            hp_var, ac_var, to_hit_var, attacks_var, damage_var, init_var,
        )

        def remove_row():
            self.enemy_rows.remove(row_data)
            row_frame.destroy()
            for idx, (_, frame, *_rest) in enumerate(self.enemy_rows):
                frame.grid(row=idx, column=0, columnspan=10, sticky="ew", pady=1)

        tk.Button(row_frame, text="✕", command=remove_row, width=2).grid(row=0, column=9, padx=2)
        self.enemy_rows.append(row_data)

    def _build_character_table(self, spell_choices, parent):
        tk.Label(parent, text="Select party members and configure options:").pack(
            anchor="w", padx=10, pady=(8, 0)
        )

        self.table_outer = tk.Frame(parent, height=160)
        self.table_outer.pack(fill="both", expand=True, padx=10, pady=(0, 6))
        self.table_outer.pack_propagate(False)

        header_font = ("TkDefaultFont", 9, "bold")
        header_frame = tk.Frame(self.table_outer)
        header_frame.pack(side="top", fill="x")

        header_inner = tk.Frame(header_frame)
        header_inner.pack(side="left", fill="x", expand=True)
        tk.Frame(header_frame, width=16).pack(side="right")

        _hcols = [
            ("In", 3, 0, "center"),
            ("Character", 18, 1, "w"),
            ("Spell", 16, 2, "center"),
            ("Dice", 7, 3, "center"),
            ("Stat", 5, 4, "center"),
            ("Mastery", 6, 5, "center"),
            ("2H", 3, 6, "center"),
            ("TWF", 3, 7, "center"),
        ]
        for text, w, col, anchor in _hcols:
            tk.Label(header_inner, text=text, font=header_font, width=w, anchor=anchor).grid(
                row=0, column=col, padx=4, pady=2
            )

        body_frame = tk.Frame(self.table_outer)
        body_frame.pack(side="top", fill="both", expand=True)

        self.table_canvas = tk.Canvas(body_frame, highlightthickness=0)
        table_scroll = tk.Scrollbar(body_frame, orient="vertical", command=self.table_canvas.yview)
        self.table_canvas.configure(yscrollcommand=table_scroll.set)
        table_scroll.pack(side="right", fill="y")
        self.table_canvas.pack(side="left", fill="both", expand=True)

        self.table_inner = tk.Frame(self.table_canvas)
        self._table_window = self.table_canvas.create_window((0, 0), window=self.table_inner, anchor="nw")

        self.table_inner.bind("<Configure>", self._on_table_configure)
        self.table_canvas.bind("<Configure>", self._on_canvas_resize)

        self.table_outer.bind("<Enter>", self._enable_scroll)
        self.table_outer.bind("<Leave>", self._disable_scroll)

        for row_idx, name in enumerate(sorted(self.characters.keys()), start=0):
            char_data = self.characters[name]
            default_main_stat = char_data.get("main_stat", "str")

            selected_var = tk.BooleanVar(value=False)
            spell_var    = tk.StringVar(value="None")
            stat_var     = tk.StringVar(value=default_main_stat)
            mastery_var  = tk.BooleanVar(value=False)
            twohand_var  = tk.BooleanVar(value=False)
            twf_var      = tk.BooleanVar(value=False)

            tk.Checkbutton(self.table_inner, variable=selected_var).grid(row=row_idx, column=0, padx=2)
            tk.Label(self.table_inner, text=name, anchor="w", width=18).grid(
                row=row_idx, column=1, padx=4, sticky="w"
            )
            spell_menu = tk.OptionMenu(self.table_inner, spell_var, *spell_choices)
            spell_menu.config(width=14)
            spell_menu.grid(row=row_idx, column=2, padx=4)
            dice_entry = tk.Entry(self.table_inner, width=7)
            dice_entry.insert(0, "")
            dice_entry.grid(row=row_idx, column=3, padx=4)
            stat_menu = tk.OptionMenu(self.table_inner, stat_var, *self.STAT_CHOICES)
            stat_menu.config(width=4)
            stat_menu.grid(row=row_idx, column=4, padx=4)
            tk.Checkbutton(self.table_inner, variable=mastery_var).grid(row=row_idx, column=5, padx=4)
            tk.Checkbutton(self.table_inner, variable=twohand_var).grid(row=row_idx, column=6, padx=4)
            tk.Checkbutton(self.table_inner, variable=twf_var).grid(row=row_idx, column=7, padx=4)

            self.char_rows.append(
                (name, selected_var, spell_var, dice_entry, stat_var, mastery_var, twohand_var, twf_var)
            )

    # ------------------------------------------------------------------
    # Open5e helpers (all private — only used internally)
    # ------------------------------------------------------------------
    def _on_search(self):
        """Called when the user presses Search or hits Enter in the entry."""
        query = self._search_var.get().strip()
        if not query:
            return
        self._import_status_var.set("Searching…")
        self._monster_listbox.delete(0, "end")
        threading.Thread(target=self._fetch_monsters, args=(query,), daemon=True).start()

    def _fetch_monsters(self, query):
        """Background thread: hit the Open5e API and schedule a UI update."""
        try:
            resp = requests.get(
                self._OPEN5E_URL,
                params={"search": query, "limit": 30},
                timeout=6,
            )
            resp.raise_for_status()
            results = resp.json().get("results", [])
            self.win.after(0, lambda: self._populate_results(results))
        except requests.exceptions.ConnectionError:
            self.win.after(0, lambda: self._import_status_var.set("No internet connection."))
        except requests.exceptions.Timeout:
            self.win.after(0, lambda: self._import_status_var.set("Request timed out."))
        except Exception as exc:
            self.win.after(0, lambda: self._import_status_var.set(f"Error: {exc}"))

    def _populate_results(self, results):
        """Populate the listbox with search results (runs on the main thread)."""
        self._monster_cache = results
        self._monster_listbox.delete(0, "end")
        if not results:
            self._import_status_var.set("No monsters found.")
            return
        self._import_status_var.set(f"{len(results)} result(s) — click one then 'Add to Enemies'")
        for m in results:
            cr = m.get("challenge_rating", "?")
            hp = m.get("hit_points", "?")
            ac_raw = m.get("armor_class", "?")
            ac = ac_raw if isinstance(ac_raw, int) else (
                ac_raw[0]["value"] if isinstance(ac_raw, list) and ac_raw else ac_raw
            )
            self._monster_listbox.insert("end", f"{m['name']}  |  CR {cr}  |  HP {hp}  |  AC {ac}")

    def _on_import_selected(self):
        """Add the selected monster from the listbox to the enemy roster."""
        selection = self._monster_listbox.curselection()
        if not selection:
            self._import_status_var.set("Select a monster from the list first.")
            return
        monster = self._monster_cache[selection[0]]
        to_hit, dmg_avg, num_attacks = self._parse_monster_actions(monster)

        # Determine role heuristic from CR
        cr_raw = monster.get("challenge_rating", 0)
        try:
            cr = float(cr_raw)
        except (TypeError, ValueError):
            cr = 0.0
        role = "Boss" if cr >= 10 else "Add"

        # armor_class can be int or list
        ac_raw = monster.get("armor_class", 10)
        if isinstance(ac_raw, list) and ac_raw:
            ac = ac_raw[0].get("value", 10)
        else:
            ac = int(ac_raw) if ac_raw else 10

        # Initiative bonus from dexterity
        dex = monster.get("dexterity", 10)
        init_bonus = (int(dex) - 10) // 2

        self.add_enemy_row(
            name=monster.get("name", "Monster"),
            role=role,
            hp=str(monster.get("hit_points", 10)),
            ac=str(ac),
            to_hit=str(to_hit),
            attacks=str(num_attacks),
            damage=str(round(dmg_avg, 2)),
            init_bonus=str(init_bonus),
        )
        self._import_status_var.set(f"Added: {monster.get('name', 'Monster')}")

    def _parse_monster_actions(self, monster):
        """
        Parse the monster's actions list to extract to_hit, avg damage,
        and number of attacks. Returns (to_hit: int, dmg_avg: float, num_attacks: int).
        """
        actions = monster.get("actions", []) or []
        best_to_hit = 0
        best_dmg = 0.0
        num_attacks = 1

        for action in actions:
            desc = action.get("desc", "") or ""

            # to hit: "+5 to hit"
            hit_match = re.search(r'\+(\d+)\s+to hit', desc, re.IGNORECASE)
            if not hit_match:
                continue  # skip non-attack actions (e.g. Multiattack description)

            to_hit = int(hit_match.group(1))

            # damage: first parenthesised dice expression e.g. (2d6 + 3)
            dmg_match = re.search(r'\((\d+d\d+(?:\s*[+\-]\s*\d+)?)\)', desc)
            dmg_avg = self._dice_avg(dmg_match.group(1)) if dmg_match else 0.0

            if dmg_avg > best_dmg:
                best_dmg = dmg_avg
                best_to_hit = to_hit

        # Try to parse number of attacks from a "Multiattack" action
        for action in actions:
            name_lower = (action.get("name") or "").lower()
            if "multiattack" in name_lower:
                desc = action.get("desc", "") or ""
                count_match = re.search(r'(\w+)\s+attacks?', desc, re.IGNORECASE)
                word_map = {
                    "one": 1, "two": 2, "three": 3, "four": 4,
                    "five": 5, "six": 6, "1": 1, "2": 2, "3": 3, "4": 4,
                }
                if count_match:
                    num_attacks = word_map.get(count_match.group(1).lower(), 1)
                break

        return best_to_hit, best_dmg, num_attacks

    @staticmethod
    def _dice_avg(expr: str) -> float:
        """
        Return the average value of a dice expression like "2d6+3" or "1d8 - 1".
        Works for any XdY +/- Z format.
        """
        expr = expr.replace(" ", "")
        parts = re.split(r'(?=[+\-])', expr)
        total = 0.0
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if "d" in part.lower():
                sign = -1 if part.startswith("-") else 1
                part = part.lstrip("+-")
                n, die = part.lower().split("d")
                total += sign * int(n) * (int(die) + 1) / 2
            else:
                total += float(part)
        return total

    # ------------------------------------------------------------------
    # Scroll helpers
    # ------------------------------------------------------------------
    def _on_table_configure(self, event):
        self.table_canvas.configure(scrollregion=self.table_canvas.bbox("all"))

    def _on_canvas_resize(self, event):
        self.table_canvas.itemconfig(self._table_window, width=event.width)

    def _scroll(self, delta):
        if delta < 0 and self.table_canvas.yview()[0] <= 0:
            return
        self.table_canvas.yview_scroll(delta, "units")

    def _on_mousewheel(self, event):
        self._scroll(int(-1 * (event.delta / 120)))

    def _on_mousewheel_up(self, event):
        self._scroll(-1)

    def _on_mousewheel_down(self, event):
        self._scroll(1)

    def _enable_scroll(self, event):
        self.win.bind_all("<MouseWheel>", self._on_mousewheel)
        self.win.bind_all("<Button-4>", self._on_mousewheel_up)
        self.win.bind_all("<Button-5>", self._on_mousewheel_down)

    def _disable_scroll(self, event):
        self.win.unbind_all("<MouseWheel>")
        self.win.unbind_all("<Button-4>")
        self.win.unbind_all("<Button-5>")

    # ------------------------------------------------------------------
    # Simulation
    # ------------------------------------------------------------------
    def simulate(self):
        """
        Run a round-by-round encounter:
          • deterministic damage-per-attack (computed via expected_damage)
          • rolled initiative (1d20 + init_bonus)
          • party uses the chosen target-priority strategy
          • enemies pick a random living party member per attack
        """
        from run_file import CustomWeapon, make_custom_modifier
        from encounter_simulator import EncounterSimulator, Combatant

        active_rows = [
            (n, sv, spv, de, stv, mv, thv, twfv)
            for (n, sv, spv, de, stv, mv, thv, twfv) in self.char_rows
            if sv.get()
        ]
        if not active_rows:
            messagebox.showwarning("No characters", "Check at least one party member.", parent=self.win)
            return

        active_enemies = []
        for (enabled_v, _frame, name_v, role_v, hp_v, ac_v, to_hit_v,
             attacks_v, dmg_v, init_v) in self.enemy_rows:
            if enabled_v.get():
                active_enemies.append((
                    name_v.get(), role_v.get(), hp_v.get(), ac_v.get(), to_hit_v.get(),
                    attacks_v.get(), dmg_v.get(), init_v.get(),
                ))
        if not active_enemies:
            messagebox.showwarning("No enemies", "Add at least one enemy.", parent=self.win)
            return

        try:
            enemy_combatants = []
            for raw_name, role, hp_str, ac_str, to_hit_str, atk_str, dmg_str, init_str in active_enemies:
                enemy_combatants.append(Combatant(
                    name=raw_name if raw_name else "Enemy",
                    side="enemy",
                    hp=int(hp_str),
                    ac=int(ac_str),
                    init_bonus=int(init_str) if init_str.strip() else 0,
                    to_hit=int(to_hit_str) if to_hit_str.strip() else 2,
                    num_attacks=int(atk_str) if atk_str.strip() else 1,
                    damage_per_attack=float(dmg_str),
                    role=role,
                ))
        except ValueError:
            messagebox.showerror(
                "Error",
                "Enemy HP, AC, To Hit, Atks, Dmg/Atk and Init bonus must all be valid numbers.",
                parent=self.win,
            )
            return

        mode = self.mode_var.get()
        avg_ac = sum(e.ac for e in enemy_combatants) / len(enemy_combatants)

        party_combatants = []
        warnings = []

        for (name, _sel, spell_var_row, dice_entry_row, stat_var_row,
             mastery_var_row, twohand_var_row, twf_var_row) in active_rows:
            char_data = self.characters.get(name, {})
            char_hp = int(char_data.get("HP", 0))
            char_dex = int(char_data.get("dex", 0))
            char_ac = int(char_data.get("AC", 10))
            char_init_bonus = int(char_data.get("init_bonus", 0))

            char_obj = Character(
                lvl=char_data.get("lvl", 0),
                str_mod=char_data.get("str", 0),
                dex_mod=char_data.get("dex", 0),
                cha_mod=char_data.get("cha", 0),
                wis_mod=char_data.get("wis", 0),
                con_mod=char_data.get("con", 0),
                int_mod=char_data.get("int", 0),
            )
            char_obj.clear_modifiers()
            cls_name = char_data.get("class", "")
            cls_cls = self.class_mapping.get(cls_name)
            if cls_cls:
                char_obj.set_class(cls_cls)
            sub_name = char_data.get("subclass", "")
            sub_cls = self.subclass_mapping.get(sub_name)
            if sub_cls:
                char_obj.set_subclass(sub_cls)
            char_obj.apply_class_features()
            for mod_name in char_data.get("modifiers", []):
                mod_cls = self.modifier_mapping.get(mod_name)
                if mod_cls:
                    char_obj.add_modifier(mod_cls)
            for cm in char_data.get("custom_modifiers", []):
                dyn = make_custom_modifier(cm["name"], cm.get("to_hit", 0), cm.get("damage", 0))
                char_obj.add_modifier(dyn)
            char_obj.default_weapon_name = char_data.get("standard_weapon", "")
            char_obj.default_weapon_bonus = char_data.get("standard_weapon_bonus", 0)

            stat = stat_var_row.get()
            spell_name_row = spell_var_row.get()
            dice_str = dice_entry_row.get().strip()

            total_dpt = 0.0
            num_attacks = 1
            label = ""

            if spell_name_row != "None":
                spell_class = self.spell_mapping.get(spell_name_row)
                if spell_class is None:
                    warnings.append(f"{name}: ⚠ Spell '{spell_name_row}' not found, skipped.")
                    continue
                if not dice_str:
                    warnings.append(f"{name}: ⚠ Spell selected but no dice entered (e.g. 1d10), skipped.")
                    continue
                spell_obj = spell_class(char_obj)
                spell_magic_bonus = char_data.get("standard_weapon_bonus", 0)
                s_ctx = SpellContext(stat=stat, magic_bonus=spell_magic_bonus, dice=dice_str, damage_bonus=0)
                try:
                    result = spell_obj.expected_damage(avg_ac, s_ctx)
                except Exception as e:
                    warnings.append(f"{name}: ⚠ Spell error: {e}")
                    continue
                total_dpt = result.get(mode, 0)
                num_attacks = result.get("num_attacks", 1) or 1
                label = spell_name_row
            else:
                cw = char_data.get("custom_weapon", {})
                if cw and cw.get("name") and cw.get("dice"):
                    from weapon_files.damage_modifiers.weapon_masteries import (
                        WeaponMasteryGraze, WeaponMasteryNick,
                    )
                    _mastery_map = {"Graze": WeaponMasteryGraze, "Nick": WeaponMasteryNick}
                    weapon_obj = CustomWeapon(
                        owner=char_obj,
                        name=cw["name"],
                        weapon_type=cw.get("weapon_type", "Melee"),
                        dice=cw["dice"],
                        magic_bonus=cw.get("magic_bonus", 0),
                        mastery_cls=_mastery_map.get(cw.get("mastery", "None")),
                    )
                    magic_bonus_used = cw.get("magic_bonus", 0)
                else:
                    weapon_obj = char_obj.get_default_weapon(self.weapon_mapping)
                    magic_bonus_used = char_data.get("standard_weapon_bonus", 0)

                if weapon_obj is None:
                    warnings.append(f"{name}: ⚠ No spell, no weapon set — skipped.")
                    continue

                a_ctx = AttackContext(
                    stat=stat,
                    magic_bonus=magic_bonus_used,
                    use_mastery=mastery_var_row.get(),
                    two_handed=twohand_var_row.get(),
                    damage_bonus=0,
                    use_twf=twf_var_row.get(),
                )
                result = weapon_obj.expected_damage(avg_ac, a_ctx)
                total_dpt = result.get(mode, 0)
                num_attacks = result.get("num_attacks", 1) or 1
                _class_gui = getattr(type(weapon_obj), "gui_name", "")
                label = weapon_obj.name if _class_gui == "_custom_" else (_class_gui or weapon_obj.name)

            damage_per_attack = (total_dpt / num_attacks) if num_attacks > 0 else 0.0

            party_combatants.append(Combatant(
                name=name,
                side="party",
                hp=char_hp,
                ac=char_ac,
                to_hit=0,
                init_bonus=char_dex + char_init_bonus,
                num_attacks=num_attacks,
                damage_per_attack=damage_per_attack,
                label=label,
            ))

        if not party_combatants:
            messagebox.showwarning(
                "No usable characters",
                "None of the selected characters could be set up. Check the warnings in the result panel.",
                parent=self.win,
            )
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert(tk.END, "\n".join(warnings))
            return

        sim = EncounterSimulator(
            party=party_combatants,
            enemies=enemy_combatants,
            priority=self.priority_var.get()
        )
        result = sim.run()

        lines = []
        if warnings:
            lines.append("--- Setup Warnings ---")
            lines.extend(warnings)
            lines.append("")

        lines.append(f"Mode: {mode}   |   Target priority: {self.priority_var.get()}")
        lines.append("--- Party ---")
        for c in party_combatants:
            lines.append(
                f"  {c.name} [{c.label}]: HP = {c.hp}, AC = {c.ac}, Initiative = +{c.init_bonus}, "
                f"{c.num_attacks} atk × {c.damage_per_attack:.2f} dmg"
            )
        lines.append("--- Enemies ---")
        for c in enemy_combatants:
            lines.append(
                f"  {c.name} ({c.role}): HP = {c.hp}, AC = {c.ac}, Initiative = +{c.init_bonus}, "
                f"{c.num_attacks} atk × {c.damage_per_attack:.2f} dmg"
            )
        lines.append("")
        lines.extend(result["log"])

        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, "\n".join(lines))


# ----------------------------------------------------------------------
# Backward-compatible function wrapper.
# ----------------------------------------------------------------------
def open_simulator_window(parent_gui):
    """Open the Boss Fight Simulator. Returns the BossSimulatorGUI instance."""
    return BossSimulatorGUI(parent_gui)