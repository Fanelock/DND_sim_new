import tkinter as tk
from tkinter import messagebox
from collections import defaultdict


class CharacterWindow:
    """Character creation/editing window as a reusable class."""

    def __init__(self, parent_gui, is_edit=False, existing_name=None):
        self.parent = parent_gui
        self.master = parent_gui.master
        self.characters = parent_gui.characters
        self.class_mapping = parent_gui.class_mapping
        self.subclass_mapping = parent_gui.subclass_mapping
        self.subclasses_by_class = parent_gui.subclasses_by_class
        self.modifier_mapping = parent_gui.modifier_mapping
        self.weapon_mapping = parent_gui.weapon_mapping
        self.is_edit = is_edit
        self.existing_name = existing_name
        self.win = None
        self._build_ui()

    def _build_ui(self):
        self.win = tk.Toplevel(self.master)
        win = self.win
        win.title("Edit Character" if self.is_edit else "Create Character")
        win.geometry("640x680+50+50")

        canvas = tk.Canvas(win)
        scrollbar = tk.Scrollbar(win, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas)
        canvas_window = canvas.create_window((0, 0), window=inner, anchor="nw")

        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        inner.bind("<Configure>", on_frame_configure)
        canvas.bind("<Configure>", on_canvas_configure)

        # Row 0: Name & Level
        tk.Label(inner, text="Character Name:").grid(row=0, column=0, sticky="w", padx=8, pady=2)
        name_entry = tk.Entry(inner)
        name_entry.grid(row=0, column=1, padx=8, pady=2)
        tk.Label(inner, text="Character Level:").grid(row=0, column=2, sticky="w", padx=8, pady=2)
        lvl_entry = tk.Entry(inner)
        lvl_entry.grid(row=0, column=3, padx=8, pady=2)

        # Row 1: Class & Subclass
        tk.Label(inner, text="Class:").grid(row=1, column=0, sticky="w", padx=8, pady=2)
        class_var = tk.StringVar(value="None")
        class_choices = ["None"] + sorted(self.class_mapping.keys())
        class_menu = tk.OptionMenu(inner, class_var, *class_choices)
        class_menu.grid(row=1, column=1, sticky="w", padx=8, pady=2)
        tk.Label(inner, text="Subclass:").grid(row=1, column=2, sticky="w", padx=8, pady=2)
        subclass_var = tk.StringVar(value="None")
        subclass_menu = tk.OptionMenu(inner, subclass_var, "None")
        subclass_menu.grid(row=1, column=3, sticky="w", padx=8, pady=2)

        def update_subclass_menu(*_):
            menu = subclass_menu["menu"]
            menu.delete(0, "end")
            subclass_var.set("None")
            menu.add_command(label="None", command=lambda: subclass_var.set("None"))
            cls_name = class_var.get()
            if cls_name == "None":
                return
            for sub in sorted(self.subclasses_by_class.get(cls_name, [])):
                menu.add_command(label=sub, command=lambda s=sub: subclass_var.set(s))

        class_var.trace_add("write", update_subclass_menu)

        # Rows 2-4: Stats
        tk.Label(inner, text="STR modifier:").grid(row=2, column=0, sticky="w", padx=6, pady=2)
        str_entry = tk.Entry(inner)
        str_entry.grid(row=2, column=1, padx=6, pady=2)
        tk.Label(inner, text="DEX modifier:").grid(row=2, column=2, sticky="w", padx=6, pady=2)
        dex_entry = tk.Entry(inner)
        dex_entry.grid(row=2, column=3, padx=6, pady=2)

        tk.Label(inner, text="CON modifier:").grid(row=3, column=0, sticky="w", padx=6, pady=2)
        con_entry = tk.Entry(inner)
        con_entry.grid(row=3, column=1, padx=6, pady=2)
        tk.Label(inner, text="INT modifier:").grid(row=3, column=2, sticky="w", padx=6, pady=2)
        int_entry = tk.Entry(inner)
        int_entry.grid(row=3, column=3, padx=6, pady=2)

        tk.Label(inner, text="WIS modifier:").grid(row=4, column=0, sticky="w", padx=6, pady=2)
        wis_entry = tk.Entry(inner)
        wis_entry.grid(row=4, column=1, padx=6, pady=2)
        tk.Label(inner, text="CHA modifier:").grid(row=4, column=2, sticky="w", padx=6, pady=2)
        cha_entry = tk.Entry(inner)
        cha_entry.grid(row=4, column=3, padx=6, pady=2)

        # Row 5: Standard Weapon & Bonus
        tk.Label(inner, text="Standard Weapon:").grid(row=5, column=0, sticky="w", padx=8, pady=2)
        standard_weapon_var = tk.StringVar(value="None")
        standard_weapon_choices = ["None"] + sorted(self.weapon_mapping.keys())
        standard_weapon_menu = tk.OptionMenu(inner, standard_weapon_var, *standard_weapon_choices)
        standard_weapon_menu.grid(row=5, column=1, sticky="w", padx=8, pady=2)
        tk.Label(inner, text="Standard Weapon Bonus:").grid(row=5, column=2, sticky="w", padx=8, pady=2)
        standard_weapon_bonus_entry = tk.Entry(inner)
        standard_weapon_bonus_entry.insert(0, "0")
        standard_weapon_bonus_entry.grid(row=5, column=3, sticky="w", pady=(8, 0), padx=6)

        # Row 6: Main Stat & HP
        tk.Label(inner, text="Main Stat:").grid(row=6, column=0, sticky="w", padx=8, pady=2)
        STATS = ["str", "dex", "cha", "wis", "con", "int"]
        main_stat_var = tk.StringVar(value="str")
        tk.OptionMenu(inner, main_stat_var, *STATS).grid(row=6, column=1, sticky="w", padx=8, pady=2)
        tk.Label(inner, text="HP:").grid(row=6, column=2, sticky="w", padx=8, pady=2)
        HP_entry = tk.Entry(inner)
        HP_entry.grid(row=6, column=3, sticky="w", padx=8, pady=2)

        # Row 7: AC & Init-bonus
        tk.Label(inner, text="AC:").grid(row=7, column=0, sticky="w", padx=8, pady=2)
        AC_entry = tk.Entry(inner, width=6)
        AC_entry.insert(0, "10")
        AC_entry.grid(row=7, column=1, sticky="w", padx=8, pady=2)
        tk.Label(inner, text="Init-bonus:").grid(row=7, column=2, sticky="w", padx=8, pady=2)
        init_bonus_entry = tk.Entry(inner, width=6)
        init_bonus_entry.insert(0, "0")
        init_bonus_entry.grid(row=7, column=3, sticky="w", padx=8, pady=2)

        # Row 8: Custom Weapon section
        sep = tk.LabelFrame(inner, text="Custom Weapon (overrides Standard Weapon if filled)")
        sep.grid(row=8, column=0, columnspan=4, sticky="ew", padx=8, pady=(10, 2))

        tk.Label(sep, text="Name:").grid(row=0, column=0, sticky="w", padx=6, pady=2)
        custom_weapon_name_entry = tk.Entry(sep, width=14)
        custom_weapon_name_entry.grid(row=0, column=1, padx=6, pady=2)
        tk.Label(sep, text="Dice (e.g. 1d8):").grid(row=0, column=2, sticky="w", padx=6, pady=2)
        custom_weapon_dice_entry = tk.Entry(sep, width=10)
        custom_weapon_dice_entry.grid(row=0, column=3, padx=6, pady=2)
        tk.Label(sep, text="Bonus Dice:").grid(row=0, column=4, sticky="w", padx=6, pady=2)
        custom_weapon_bonus_dice_entry = tk.Entry(sep, width=10)
        custom_weapon_bonus_dice_entry.grid(row=0, column=5, padx=6, pady=2)

        WEAPON_TYPES = ["Melee", "Two-Handed", "Finesse", "Light", "Ranged", "Ranged, Light"]
        tk.Label(sep, text="Weapon Type:").grid(row=1, column=0, sticky="w", padx=6, pady=2)
        custom_weapon_type_var = tk.StringVar(value="Melee")
        tk.OptionMenu(sep, custom_weapon_type_var, *WEAPON_TYPES).grid(
            row=1, column=1, sticky="w", padx=6, pady=2)
        tk.Label(sep, text="Magic Bonus:").grid(row=1, column=2, sticky="w", padx=6, pady=2)
        custom_weapon_bonus_entry = tk.Entry(sep, width=6)
        custom_weapon_bonus_entry.insert(0, "0")
        custom_weapon_bonus_entry.grid(row=1, column=3, padx=6, pady=2)
        tk.Label(sep, text="Mastery:").grid(row=2, column=0, sticky="w", padx=6, pady=2)
        MASTERY_OPTIONS = ["None", "Graze", "Nick"]
        custom_weapon_mastery_var = tk.StringVar(value="None")
        tk.OptionMenu(sep, custom_weapon_mastery_var, *MASTERY_OPTIONS).grid(
            row=2, column=1, sticky="w", padx=6, pady=2)

        # Row 9: Custom Modifiers / Feats section
        custom_mod_frame = tk.LabelFrame(
            inner, text="Custom Feats / Damage Modifiers (to-hit and damage offsets)")
        custom_mod_frame.grid(row=9, column=0, columnspan=4, sticky="ew", padx=8, pady=(10, 2))

        custom_mod_rows = []

        cm_header_frame = tk.Frame(custom_mod_frame)
        cm_header_frame.pack(fill="x", padx=4, pady=2)
        tk.Label(cm_header_frame, text="Name", width=16, anchor="w").pack(side="left", padx=4)
        tk.Label(cm_header_frame, text="To-Hit mod", width=10, anchor="w").pack(side="left", padx=4)
        tk.Label(cm_header_frame, text="Damage mod", width=10, anchor="w").pack(side="left", padx=4)

        cm_rows_frame = tk.Frame(custom_mod_frame)
        cm_rows_frame.pack(fill="x", padx=4)

        def add_custom_mod_row(name="", to_hit="0", damage="0"):
            row_frame = tk.Frame(cm_rows_frame)
            row_frame.pack(fill="x", pady=1)
            name_var = tk.StringVar(value=name)
            to_hit_var = tk.StringVar(value=to_hit)
            damage_var = tk.StringVar(value=damage)
            name_e = tk.Entry(row_frame, textvariable=name_var, width=16)
            name_e.pack(side="left", padx=4)
            to_hit_e = tk.Entry(row_frame, textvariable=to_hit_var, width=10)
            to_hit_e.pack(side="left", padx=4)
            damage_e = tk.Entry(row_frame, textvariable=damage_var, width=10)
            damage_e.pack(side="left", padx=4)

            def remove_row():
                custom_mod_rows.remove((name_var, to_hit_var, damage_var))
                row_frame.destroy()

            tk.Button(row_frame, text="✕", command=remove_row, width=2).pack(side="left", padx=2)
            custom_mod_rows.append((name_var, to_hit_var, damage_var))

        tk.Button(custom_mod_frame, text="+ Add Custom Modifier",
                  command=add_custom_mod_row).pack(pady=4)

        # Standard modifier checkboxes
        modifier_vars_local = {}
        mod_by_cat = defaultdict(list)
        for name, cls in self.modifier_mapping.items():
            mod_by_cat[cls.category].append(name)

        category_order = ["Fighting Style", "Feat", "Class Feature Manual", "Other"]
        row_offset = 10
        for cat in category_order:
            mods = mod_by_cat.get(cat, [])
            if not mods:
                continue
            tk.Label(inner, text=f"{cat}:").grid(
                row=row_offset, column=0, sticky="w", padx=6, pady=(8, 2))
            i = 0
            col_count = 4
            for name in mods:
                var = tk.BooleanVar(value=False)
                modifier_vars_local[name] = var
                r = row_offset + 1 + i // col_count
                c = i % col_count
                tk.Checkbutton(inner, text=name, variable=var).grid(
                    row=r, column=c, sticky="w", padx=6, pady=2)
                i += 1
            row_offset += 1 + (len(mods) + col_count - 1) // col_count

        # Pre-fill fields if editing
        if self.is_edit and self.existing_name:
            data = self.characters.get(self.existing_name, {})
            name_entry.insert(0, self.existing_name)
            class_var.set(data.get("class", "None"))
            update_subclass_menu()
            subclass_var.set(data.get("subclass", "None"))
            lvl_entry.insert(0, str(data.get("lvl", 0)))
            str_entry.insert(0, str(data.get("str", 0)))
            dex_entry.insert(0, str(data.get("dex", 0)))
            con_entry.insert(0, str(data.get("con", 0)))
            int_entry.insert(0, str(data.get("int", 0)))
            wis_entry.insert(0, str(data.get("wis", 0)))
            cha_entry.insert(0, str(data.get("cha", 0)))
            standard_weapon_var.set(data.get("standard_weapon", "None") or "None")
            standard_weapon_bonus_entry.delete(0, tk.END)
            standard_weapon_bonus_entry.insert(0, str(data.get("standard_weapon_bonus", 0)))
            main_stat_var.set(data.get("main_stat", "str"))
            HP_entry.insert(0, str(data.get("HP", 0)))
            AC_entry.delete(0, tk.END)
            AC_entry.insert(0, str(data.get("AC", 10)))
            init_bonus_entry.delete(0, tk.END)
            init_bonus_entry.insert(0, str(data.get("init_bonus", 0)))

            # Restore custom weapon
            cw = data.get("custom_weapon", {})
            if cw:
                custom_weapon_name_entry.insert(0, cw.get("name", ""))
                custom_weapon_dice_entry.insert(0, cw.get("dice", ""))
                custom_weapon_bonus_dice_entry.insert(0, cw.get("bonus_dice", ""))
                custom_weapon_type_var.set(cw.get("weapon_type", "Melee"))
                custom_weapon_bonus_entry.delete(0, tk.END)
                custom_weapon_bonus_entry.insert(0, str(cw.get("magic_bonus", 0)))
                custom_weapon_mastery_var.set(cw.get("mastery", "None"))

            # Restore custom modifiers
            for cm in data.get("custom_modifiers", []):
                add_custom_mod_row(
                    name=cm.get("name", ""),
                    to_hit=str(cm.get("to_hit", 0)),
                    damage=str(cm.get("damage", 0)),
                )

            # Restore selected modifiers
            for mod_name in data.get("modifiers", []):
                if mod_name in modifier_vars_local:
                    modifier_vars_local[mod_name].set(True)

        # Save button & logic
        def save_and_close():
            char_name = name_entry.get().strip()
            if not char_name:
                messagebox.showerror("Error", "Name required.")
                return
            try:
                l = int(lvl_entry.get().strip())
                s = int(str_entry.get().strip())
                d = int(dex_entry.get().strip())
                co = int(con_entry.get().strip())
                i = int(int_entry.get().strip())
                w = int(wis_entry.get().strip())
                c = int(cha_entry.get().strip())
                stdb = int(standard_weapon_bonus_entry.get().strip() or "0")
                hp = int(HP_entry.get().strip())
                ac = int(AC_entry.get().strip() or "10")
                init_bonus = int(init_bonus_entry.get().strip() or "0")
            except ValueError:
                messagebox.showerror("Error", "STR/DEX/CHA/HP/AC/Init etc must be integers.")
                return

            selected_mods = [n for n, var in modifier_vars_local.items() if var.get()]
            cls_name = class_var.get()
            subcls_name = subclass_var.get()
            std_weapon = standard_weapon_var.get()

            # Collect custom weapon
            cw_name = custom_weapon_name_entry.get().strip()
            cw_dice = custom_weapon_dice_entry.get().strip()
            cw_bonus_dice = custom_weapon_bonus_dice_entry.get().strip()
            if cw_name and cw_dice:
                try:
                    cw_bonus = int(custom_weapon_bonus_entry.get().strip() or "0")
                except ValueError:
                    messagebox.showerror("Error", "Custom weapon magic bonus must be an integer.")
                    return
                custom_weapon_data = {
                    "name": cw_name,
                    "dice": cw_dice,
                    "bonus_dice": cw_bonus_dice,
                    "weapon_type": custom_weapon_type_var.get(),
                    "magic_bonus": cw_bonus,
                    "mastery": custom_weapon_mastery_var.get(),
                }
            else:
                custom_weapon_data = {}

            # Collect custom modifiers
            custom_mods_data = []
            for name_var, to_hit_var, damage_var in custom_mod_rows:
                cm_name = name_var.get().strip()
                if not cm_name:
                    continue
                try:
                    cm_to_hit = int(to_hit_var.get().strip() or "0")
                    cm_damage = int(damage_var.get().strip() or "0")
                except ValueError:
                    messagebox.showerror(
                        "Error",
                        f"Custom modifier '{cm_name}': to-hit and damage must be integers.")
                    return
                custom_mods_data.append({
                    "name": cm_name,
                    "to_hit": cm_to_hit,
                    "damage": cm_damage,
                })

            self.characters[char_name] = {
                "lvl": l,
                "class": "" if cls_name == "None" else cls_name,
                "subclass": "" if subcls_name == "None" else subcls_name,
                "str": s,
                "dex": d,
                "cha": c,
                "wis": w,
                "con": co,
                "int": i,
                "modifiers": selected_mods,
                "standard_weapon": "" if std_weapon == "None" else std_weapon,
                "standard_weapon_bonus": stdb,
                "main_stat": main_stat_var.get(),
                "HP": hp,
                "AC": ac,
                "init_bonus": init_bonus,
                "custom_weapon": custom_weapon_data,
                "custom_modifiers": custom_mods_data,
            }

            if self.is_edit and self.existing_name and self.existing_name != char_name:
                self.characters.pop(self.existing_name, None)

            self.parent.save_characters_to_file()
            self.parent.refresh_character_listbox(reselect=char_name)
            self.win.destroy()

        save_button = tk.Button(inner, text="Save", command=save_and_close)
        save_button.grid(row=row_offset + 2, column=0, columnspan=4, pady=10)