import tkinter as tk
from tkinter import filedialog, messagebox

from attack_context import AttackContext
from character import Character
from run_file import CustomWeapon, make_custom_modifier
from spell_context import SpellContext


class BossSimulatorGUI:
    """
    Class-based Boss Fight Simulator window.

    Opens as a Toplevel attached to the main MinimalDNDGUI instance and
    reads its mappings (characters, spells, classes, weapons, modifiers...)
    to estimate combined party DPT against a configurable enemy roster.
    """

    STAT_CHOICES = ["str", "dex", "con", "int", "wis", "cha"]

    def __init__(self, parent_gui):
        """
        :param parent_gui: An instance of MinimalDNDGUI (or any object that
            exposes ``master``, ``characters``, ``spell_mapping``,
            ``class_mapping``, ``subclass_mapping``, ``modifier_mapping``
            and ``weapon_mapping``).
        """
        self.parent = parent_gui
        self.master = parent_gui.master

        # Convenience aliases for the parent's mappings.
        self.characters = parent_gui.characters
        self.spell_mapping = parent_gui.spell_mapping
        self.class_mapping = parent_gui.class_mapping
        self.subclass_mapping = parent_gui.subclass_mapping
        self.modifier_mapping = parent_gui.modifier_mapping
        self.weapon_mapping = parent_gui.weapon_mapping

        # Will be populated in _build_ui().
        self.win = None
        self.mode_var = None
        self.result_text = None
        self.simulate_btn = None
        self.enemy_rows = []
        self.char_rows = []
        self.enemy_inner = None
        self.enemy_canvas = None
        self._enemy_window = None
        self.table_canvas = None
        self.table_inner = None
        self._table_window = None
        self.table_outer = None

        self._build_ui()

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------
    def show(self):
        """Bring the simulator window to the front (no-op convenience)."""
        if self.win is not None:
            self.win.lift()
            self.win.focus_force()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self):
        self.win = tk.Toplevel(self.master)
        self.win.title("Boss Fight Simulator")
        self.win.geometry("800x700+725+50")

        spell_choices = ["None"] + sorted(self.spell_mapping.keys())

        # ----------------------------------------------------------------
        # Pack bottom widgets FIRST so tkinter reserves their space before
        # the expanding character table claims any remaining room.
        # ----------------------------------------------------------------

        # --- Simulate button (very bottom) ---
        btn_frame = tk.Frame(self.win)
        btn_frame.pack(side="bottom", fill="x", padx=10, pady=4)
        self.simulate_btn = tk.Button(btn_frame, text="Run Simulation", command=self.simulate)
        self.simulate_btn.pack(pady=2)

        # --- Output ---
        out_frame = tk.LabelFrame(self.win, text="Result")
        out_frame.pack(side="bottom", fill="both", expand=False, padx=10, pady=(0, 4))
        self.result_text = tk.Text(out_frame, height=12, wrap="word")
        self.result_text.pack(fill="both", expand=True, padx=6, pady=6)

        # --- Roll mode ---
        options_frame = tk.Frame(self.win)
        options_frame.pack(side="bottom", fill="x", padx=10, pady=(2, 0))
        tk.Label(options_frame, text="Roll Mode:").pack(side="left")
        self.mode_var = tk.StringVar(value="normal")
        for label, val in [("Normal", "normal"), ("Advantage", "advantage"), ("Disadvantage", "disadvantage")]:
            tk.Radiobutton(options_frame, text=label, variable=self.mode_var, value=val).pack(side="left", padx=2)

        # ----------------------------------------------------------------
        # Enemy section
        # ----------------------------------------------------------------
        self._build_enemy_section()

        # ----------------------------------------------------------------
        # Character table
        # ----------------------------------------------------------------
        self._build_character_table(spell_choices)

    def _build_enemy_section(self):
        enemy_outer_frame = tk.LabelFrame(self.win, text="Enemies")
        enemy_outer_frame.pack(side="bottom", fill="both", expand=False, padx=10, pady=6)

        # Header
        enemy_header_font = ("TkDefaultFont", 9, "bold")
        enemy_header_frame = tk.Frame(enemy_outer_frame)
        enemy_header_frame.pack(side="top", fill="x", padx=4, pady=(4, 0))

        _enemy_hcols = [
            ("In", 3, 0, "center"),
            ("Name", 15, 1, "w"),
            ("Role", 8, 2, "center"),
            ("HP", 6, 3, "center"),
            ("AC", 5, 4, "center"),
            ("Damage/Turn", 10, 5, "center"),
            ("", 3, 6, "center"),  # delete button
        ]
        for text, w, col, anchor in _enemy_hcols:
            tk.Label(enemy_header_frame, text=text, font=enemy_header_font, width=w, anchor=anchor).grid(
                row=0, column=col, padx=2, pady=2
            )

        # Scrollable enemy rows
        enemy_canvas_frame = tk.Frame(enemy_outer_frame)
        enemy_canvas_frame.pack(side="top", fill="both", expand=True, padx=4)

        self.enemy_canvas = tk.Canvas(enemy_canvas_frame, highlightthickness=0, height=120)
        enemy_scroll = tk.Scrollbar(enemy_canvas_frame, orient="vertical", command=self.enemy_canvas.yview)
        self.enemy_canvas.configure(yscrollcommand=enemy_scroll.set)
        enemy_scroll.pack(side="right", fill="y")
        self.enemy_canvas.pack(side="left", fill="both", expand=True)

        self.enemy_inner = tk.Frame(self.enemy_canvas)
        self._enemy_window = self.enemy_canvas.create_window((0, 0), window=self.enemy_inner, anchor="nw")

        self.enemy_inner.bind("<Configure>", self._on_enemy_configure)
        self.enemy_canvas.bind("<Configure>", self._on_enemy_canvas_resize)

        # Add enemy button
        add_enemy_btn_frame = tk.Frame(enemy_outer_frame)
        add_enemy_btn_frame.pack(side="bottom", fill="x", padx=4, pady=4)
        tk.Button(add_enemy_btn_frame, text="+ Add Enemy", command=lambda: self.add_enemy_row()).pack(side="left")

        # Pre-populate with one boss
        self.add_enemy_row(name="Boss", role="Boss", hp="200", ac="15", damage="50")

    def _on_enemy_configure(self, event):
        self.enemy_canvas.configure(scrollregion=self.enemy_canvas.bbox("all"))

    def _on_enemy_canvas_resize(self, event):
        self.enemy_canvas.itemconfig(self._enemy_window, width=event.width)

    def add_enemy_row(self, name="Enemy", role="Add", hp="50", ac="15", damage="10"):
        row_idx = len(self.enemy_rows)
        row_frame = tk.Frame(self.enemy_inner)
        row_frame.grid(row=row_idx, column=0, columnspan=7, sticky="ew", pady=1)

        enabled_var = tk.BooleanVar(value=True)
        name_var = tk.StringVar(value=name)
        role_var = tk.StringVar(value=role)
        hp_var = tk.StringVar(value=hp)
        ac_var = tk.StringVar(value=ac)
        damage_var = tk.StringVar(value=damage)

        tk.Checkbutton(row_frame, variable=enabled_var).grid(row=0, column=0, padx=2)

        name_entry = tk.Entry(row_frame, textvariable=name_var, width=15)
        name_entry.grid(row=0, column=1, padx=2)

        role_menu = tk.OptionMenu(row_frame, role_var, "Boss", "Add", "Minion")
        role_menu.config(width=6)
        role_menu.grid(row=0, column=2, padx=2)

        hp_entry = tk.Entry(row_frame, textvariable=hp_var, width=6)
        hp_entry.grid(row=0, column=3, padx=2)

        ac_entry = tk.Entry(row_frame, textvariable=ac_var, width=5)
        ac_entry.grid(row=0, column=4, padx=2)

        damage_entry = tk.Entry(row_frame, textvariable=damage_var, width=10)
        damage_entry.grid(row=0, column=5, padx=2)

        row_data = (enabled_var, row_frame, name_var, role_var, hp_var, ac_var, damage_var)

        def remove_row():
            self.enemy_rows.remove(row_data)
            row_frame.destroy()
            # Re-grid remaining rows
            for idx, (_, frame, *_rest) in enumerate(self.enemy_rows):
                frame.grid(row=idx, column=0, columnspan=7, sticky="ew", pady=1)

        delete_btn = tk.Button(row_frame, text="✕", command=remove_row, width=2)
        delete_btn.grid(row=0, column=6, padx=2)

        self.enemy_rows.append(row_data)

    def _build_character_table(self, spell_choices):
        # --- Character table with per-character controls ---
        tk.Label(self.win, text="Select party members and configure options:").pack(
            anchor="w", padx=10, pady=(10, 0)
        )

        # Outer frame — fixed header row + scrollable body
        self.table_outer = tk.Frame(self.win)
        self.table_outer.pack(fill="both", expand=True, padx=10, pady=(0, 4))

        # --- Fixed header row (outside the canvas, never scrolls) ---
        header_font = ("TkDefaultFont", 9, "bold")
        header_frame = tk.Frame(self.table_outer)
        header_frame.pack(side="top", fill="x")

        # Reserve space for the scrollbar on the right so headers align with rows
        header_inner = tk.Frame(header_frame)
        header_inner.pack(side="left", fill="x", expand=True)
        tk.Frame(header_frame, width=16).pack(side="right")  # scrollbar placeholder

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

        # --- Scrollable body ---
        body_frame = tk.Frame(self.table_outer)
        body_frame.pack(side="top", fill="both", expand=True)

        self.table_canvas = tk.Canvas(body_frame, highlightthickness=0, height=150)
        table_scroll = tk.Scrollbar(body_frame, orient="vertical", command=self.table_canvas.yview)
        self.table_canvas.configure(yscrollcommand=table_scroll.set)
        table_scroll.pack(side="right", fill="y")
        self.table_canvas.pack(side="left", fill="both", expand=True)

        self.table_inner = tk.Frame(self.table_canvas)
        self._table_window = self.table_canvas.create_window((0, 0), window=self.table_inner, anchor="nw")

        self.table_inner.bind("<Configure>", self._on_table_configure)
        self.table_canvas.bind("<Configure>", self._on_canvas_resize)

        # --- Mousewheel scrolling ---
        self.table_outer.bind("<Enter>", self._enable_scroll)
        self.table_outer.bind("<Leave>", self._disable_scroll)

        # One row per character
        for row_idx, name in enumerate(sorted(self.characters.keys()), start=0):
            char_data = self.characters[name]
            default_main_stat = char_data.get("main_stat", "str")

            selected_var = tk.BooleanVar(value=False)
            spell_var = tk.StringVar(value="None")
            stat_var = tk.StringVar(value=default_main_stat)
            mastery_var = tk.BooleanVar(value=False)
            twohand_var = tk.BooleanVar(value=False)
            twf_var = tk.BooleanVar(value=False)

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
    # Scroll helpers
    # ------------------------------------------------------------------
    def _on_table_configure(self, event):
        self.table_canvas.configure(scrollregion=self.table_canvas.bbox("all"))

    def _on_canvas_resize(self, event):
        self.table_canvas.itemconfig(self._table_window, width=event.width)

    def _scroll(self, delta):
        if delta < 0 and self.table_canvas.yview()[0] <= 0:
            return  # already at top, don't scroll further up
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
        # Gather active party members
        active_rows = [
            (n, sv, spv, de, stv, mv, thv, twfv)
            for (n, sv, spv, de, stv, mv, thv, twfv) in self.char_rows
            if sv.get()
        ]
        if not active_rows:
            messagebox.showwarning("No characters", "Check at least one party member.", parent=self.win)
            return

        # Gather active enemies
        active_enemies = [
            (name_v.get(), role_v.get(), hp_v.get(), ac_v.get(), dmg_v.get())
            for (enabled_v, _, name_v, role_v, hp_v, ac_v, dmg_v) in self.enemy_rows
            if enabled_v.get()
        ]
        if not active_enemies:
            messagebox.showwarning("No enemies", "Add at least one enemy.", parent=self.win)
            return

        # Validate enemy inputs
        try:
            validated_enemies = []
            for name, role, hp_str, ac_str, dmg_str in active_enemies:
                validated_enemies.append({
                    "name": name if name else "Enemy",
                    "role": role,
                    "hp": int(hp_str),
                    "ac": int(ac_str),
                    "damage": float(dmg_str),
                })
        except ValueError:
            messagebox.showerror("Error", "Enemy HP, AC, and Damage must be valid numbers.", parent=self.win)
            return

        mode = self.mode_var.get()
        total_dpt = 0.0
        party_hp = 0
        lines = []

        # Calculate party DPT against each enemy AC (using first enemy's AC for now as aggregate)
        # In a real simulation, you'd pick targets dynamically
        aggregate_ac = validated_enemies[0]["ac"] if validated_enemies else 15

        for (name, _sel, spell_var_row, dice_entry_row, stat_var_row, mastery_var_row, twohand_var_row,
             twf_var_row) in active_rows:
            char_data = self.characters.get(name, {})
            party_hp += int(char_data.get("HP", 0))

            # Build Character object
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

            # --- Priority 1: Spell selected ---
            if spell_name_row != "None":
                spell_class = self.spell_mapping.get(spell_name_row)
                if spell_class is None:
                    lines.append(f"{name}: ⚠ Spell '{spell_name_row}' not found, skipped.")
                    continue
                if not dice_str:
                    lines.append(f"{name}: ⚠ Spell selected but no dice entered (e.g. 1d10), skipped.")
                    continue
                spell_obj = spell_class(char_obj)
                spell_magic_bonus = char_data.get("standard_weapon_bonus", 0)
                s_ctx = SpellContext(
                    stat=stat,
                    magic_bonus=spell_magic_bonus,
                    dice=dice_str,
                    damage_bonus=0,
                )
                try:
                    result = spell_obj.expected_damage(aggregate_ac, s_ctx)
                except Exception as e:
                    lines.append(f"{name}: ⚠ Spell error: {e}")
                    continue
                dpt = result.get(mode, 0)
                total_dpt += dpt
                lines.append(f"{name} [{spell_name_row}]: {dpt:.2f} dmg/turn")
                continue

            # --- Priority 2: Custom weapon ---
            cw = char_data.get("custom_weapon", {})
            if cw and cw.get("name") and cw.get("dice"):
                from weapon_files.damage_modifiers.weapon_masteries import WeaponMasteryGraze, WeaponMasteryNick
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
                # --- Priority 3: Standard weapon ---
                weapon_obj = char_obj.get_default_weapon(self.weapon_mapping)
                magic_bonus_used = char_data.get("standard_weapon_bonus", 0)

            if weapon_obj is None:
                lines.append(f"{name}: ⚠ No spell, no weapon set — skipped.")
                continue

            a_ctx = AttackContext(
                stat=stat,
                magic_bonus=magic_bonus_used,
                use_mastery=mastery_var_row.get(),
                two_handed=twohand_var_row.get(),
                damage_bonus=0,
                use_twf=twf_var_row.get(),
            )
            result = weapon_obj.expected_damage(aggregate_ac, a_ctx)
            dpt = result.get(mode, 0)
            total_dpt += dpt
            _class_gui = getattr(type(weapon_obj), "gui_name", "")
            weapon_label = weapon_obj.name if _class_gui == "_custom_" else (_class_gui or weapon_obj.name)
            lines.append(f"{name} [{weapon_label}]: {dpt:.2f} dmg/turn")

        # Enemy summary
        total_enemy_hp = sum(e["hp"] for e in validated_enemies)
        total_enemy_dpt = sum(e["damage"] for e in validated_enemies)

        lines.append("\n--- Enemy Roster ---")
        for e in validated_enemies:
            lines.append(f"  {e['name']} ({e['role']}): HP={e['hp']}, AC={e['ac']}, DPT={e['damage']}")

        if total_dpt <= 0:
            lines.append("\n⚠ Cannot estimate (no valid party damage).")
        else:
            rounds_to_kill_enemies = total_enemy_hp / total_dpt
            rounds_to_kill_party = party_hp / total_enemy_dpt if total_enemy_dpt > 0 else float('inf')

            lines.append(f"\n--- Aggregate Estimate ---")
            lines.append(f"Total party DPT ({mode}): {total_dpt:.2f}")
            lines.append(f"Total enemy HP: {total_enemy_hp}")
            lines.append(f"Rounds to kill all enemies: {rounds_to_kill_enemies:.1f}")
            lines.append(
                f"Estimated time: ~{rounds_to_kill_enemies * 6:.0f} sec ({rounds_to_kill_enemies / 10:.1f} min)")

            lines.append(f"\nTotal enemy DPT: {total_enemy_dpt:.2f}")
            lines.append(f"Party HP: {party_hp}")
            lines.append(f"Rounds to kill party: {rounds_to_kill_party:.1f}")
            lines.append(f"Estimated time: ~{rounds_to_kill_party * 6:.0f} sec ({rounds_to_kill_party / 10:.1f} min)")

            if rounds_to_kill_enemies < rounds_to_kill_party:
                lines.append(f"\n✓ Party wins (kills enemies in {rounds_to_kill_enemies:.1f} rounds)")
            elif rounds_to_kill_party < rounds_to_kill_enemies:
                lines.append(f"\n✗ Enemies win (kills party in {rounds_to_kill_party:.1f} rounds)")
            else:
                lines.append("\n⚔ Mutual destruction (tie)")

        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, "\n".join(lines))


# ----------------------------------------------------------------------
# Backward-compatible function wrapper.
# Kept so any older code that imported ``open_simulator_window`` still works.
# ----------------------------------------------------------------------
def open_simulator_window(parent_gui):
    """Open the Boss Fight Simulator. Returns the BossSimulatorGUI instance."""
    return BossSimulatorGUI(parent_gui)
