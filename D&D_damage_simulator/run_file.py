import tkinter as tk
from glob import magic_check
from tkinter import filedialog, messagebox
import json
import os
import inspect
from collections import defaultdict
import pkgutil
import importlib

from class_files.base_class import BaseClass
from class_files.base_subclass import BaseSubclass

from character import Character
from attack_context import AttackContext

from weapon_files import *
from weapon_files.damage_modifiers import *

CHAR_FILE = "characters.json"

modifier_package = importlib.import_module("weapon_files.damage_modifiers")
for _, module_name, _ in pkgutil.iter_modules(modifier_package.__path__):
    importlib.import_module(f"weapon_files.damage_modifiers.{module_name}")

class_package = importlib.import_module("class_files")
for _, module_name, _ in pkgutil.iter_modules(class_package.__path__):
    importlib.import_module(f"class_files.{module_name}")

weapon_package = importlib.import_module("weapon_files")
for _, module_name, _ in pkgutil.iter_modules(weapon_package.__path__):
    importlib.import_module(f"weapon_files.{module_name}")

def gather_subclasses(cls):
    result = set()
    for sub in cls.__subclasses__():
        result.add(sub)
        result.update(gather_subclasses(sub))
    return result

def build_weapon_mapping():
    return {
        cls.gui_name if hasattr(cls, "gui_name") else cls.__name__: cls
        for cls in gather_subclasses(Weapon)
        if not inspect.isabstract(cls)
    }

def modifier_mapping():
    return {
        cls.gui_name if hasattr(cls, "gui_name") else cls.__name__: cls
        for cls in DamageModifier.__subclasses__()
    }

def build_class_mapping():
    return {
        cls.name: cls
        for cls in gather_subclasses(BaseClass)
        if cls.name != "Base Class"
    }

def build_subclass_mapping():
    return {
        cls.name: cls
        for cls in gather_subclasses(BaseSubclass)
        if cls.name != "Base Subclass"
    }

class MinimalDNDGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Minimal DND Expected Damage GUI")
        self.master.geometry("630x620")

        self.weapon_mapping = build_weapon_mapping()

        self.modifier_mapping = modifier_mapping()

        self.class_mapping = build_class_mapping()

        self.subclass_mapping = build_subclass_mapping()

        mod_by_cat = defaultdict(list)

        for name, cls in self.modifier_mapping.items():
            mod_by_cat[getattr(cls, "category", "Other")].append(name)

        self.subclasses_by_class = defaultdict(list)

        for subclass_cls in self.subclass_mapping.values():
            parent = getattr(subclass_cls, "parent_class", None)
            if parent:
                self.subclasses_by_class[parent.name].append(subclass_cls.name)

        self.modifier_vars = {}

        # In-memory characters: {name: {str:..., dex:..., cha:..., prof:...}}
        self.characters = {}
        self.load_characters_from_file()

        # Top frame: Character CRUD
        top_frame = tk.Frame(master)
        top_frame.pack(pady=8, fill="x")

        tk.Button(top_frame, text="Create New", command=self.open_create_window).pack(side="left", padx=6)
        tk.Button(top_frame, text="Edit Selected", command=self.open_edit_window).pack(side="left", padx=6)
        tk.Button(top_frame, text="Delete Selected", command=self.delete_selected).pack(side="left", padx=6)
        tk.Button(top_frame, text="Import (JSON)", command=self.import_json).pack(side="left", padx=6)
        tk.Button(top_frame, text="Export (JSON)", command=self.export_json).pack(side="left", padx=6)

        # Character list box
        char_frame = tk.LabelFrame(master, text="Saved Characters")
        char_frame.pack(fill="both", expand=False, padx=8, pady=6)

        self.character_listbox = tk.Listbox(char_frame, height=6)
        self.character_listbox.pack(side="left", fill="both", expand=True, padx=(6,0), pady=6)
        scrollbar = tk.Scrollbar(char_frame, orient="vertical", command=self.character_listbox.yview)
        scrollbar.pack(side="right", fill="y", padx=(0,6), pady=6)
        self.character_listbox.config(yscrollcommand=scrollbar.set)

        # Middle frame: weapon/spell and context controls
        middle_frame = tk.Frame(master)
        middle_frame.pack(fill="x", padx=8, pady=6)

        # --- Row 0: Weapon & Spell ---
        tk.Label(middle_frame, text="Select Weapon:").grid(row=0, column=0, sticky="w")
        self.weapon_var = tk.StringVar(value="Use Character Weapon")
        weapon_choices = ["Use Character Weapon"] + sorted(self.weapon_mapping.keys())
        self.weapon_menu = tk.OptionMenu(middle_frame, self.weapon_var, *weapon_choices)
        self.weapon_menu.grid(row=0, column=1, sticky="w", padx=6)

        tk.Label(middle_frame, text="Select Spell:").grid(row=0, column=2, sticky="w", padx=(20, 0))
        self.spell_var = tk.StringVar(value="None")
        self.spell_menu = tk.OptionMenu(middle_frame, self.spell_var, "None", "Spell Attack", "Spell Save")
        self.spell_menu.grid(row=0, column=3, sticky="w", padx=6)

        # --- Row 1: Target AC & Magic Bonus ---
        tk.Label(middle_frame, text="Target AC:").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.ac_entry = tk.Entry(middle_frame, width=8)
        self.ac_entry.insert(0, "15")
        self.ac_entry.grid(row=1, column=1, sticky="w", pady=(8, 0), padx=6)

        tk.Label(middle_frame, text="Magic Bonus:").grid(row=1, column=2, sticky="w", pady=(8, 0), padx=(20, 0))
        self.magic_entry = tk.Entry(middle_frame, width=8)
        self.magic_entry.insert(0, "")
        self.magic_entry.grid(row=1, column=3, sticky="w", pady=(8, 0), padx=6)

        # --- Row 2: Stat Selection ---
        stat_frame = tk.LabelFrame(middle_frame, text="Attack Stat")
        stat_frame.grid(row=2, column=0, columnspan=4, sticky="w", pady=(10, 0))

        self.stat_var = tk.StringVar(value="str")
        tk.Radiobutton(stat_frame, text="STR", variable=self.stat_var, value="str").grid(row=0, column=0, padx=6, pady=2)
        tk.Radiobutton(stat_frame, text="DEX", variable=self.stat_var, value="dex").grid(row=0, column=1, padx=6, pady=2)
        tk.Radiobutton(stat_frame, text="CHA", variable=self.stat_var, value="cha").grid(row=0, column=2, padx=6, pady=2)
        tk.Radiobutton(stat_frame, text="WIS", variable=self.stat_var, value="wis").grid(row=1, column=0, padx=6, pady=2)
        tk.Radiobutton(stat_frame, text="CON", variable=self.stat_var, value="con").grid(row=1, column=1, padx=6, pady=2)
        tk.Radiobutton(stat_frame, text="INT", variable=self.stat_var, value="int").grid(row=1, column=2, padx=6, pady=2)

        # --- Row 3: Mastery & Two-Handed ---
        self.mastery_var = tk.BooleanVar()
        tk.Checkbutton(middle_frame, text="Use Mastery", variable=self.mastery_var).grid(row=3, column=0, sticky="w", pady=(10, 0))

        self.twohand_var = tk.BooleanVar()
        tk.Checkbutton(middle_frame, text="Two-Handed", variable=self.twohand_var).grid(row=3, column=1, sticky="w", pady=(10, 0))

        # Run simulation / expected damage
        run_frame = tk.Frame(master)
        run_frame.pack(fill="x", padx=8, pady=(8,0))
        tk.Button(run_frame, text="Compute Expected Damage", command=self.run_expected_damage).pack(side="left", padx=6)
        tk.Button(run_frame, text="Show Raw Result (debug)", command=self.show_last_result).pack(side="left", padx=6)

        # Output area
        out_frame = tk.LabelFrame(master, text="Result")
        out_frame.pack(fill="both", expand=True, padx=8, pady=8)
        self.result_text = tk.Text(out_frame, height=12, wrap="word")
        self.result_text.pack(fill="both", expand=True, padx=6, pady=6)

        self.last_result = None

        self.refresh_character_listbox()

    def load_characters_from_file(self):
        if os.path.exists(CHAR_FILE):
            try:
                with open(CHAR_FILE, "r") as f:
                    self.characters = json.load(f)
            except Exception:
                self.characters = {}
        else:
            self.characters = {}

    def save_characters_to_file(self):
        try:
            with open(CHAR_FILE, "w") as f:
                json.dump(self.characters, f, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save characters: {e}")

    def open_create_window(self):
        self.open_character_window(is_edit=False)

    def open_edit_window(self):
        sel = self.character_listbox.curselection()
        if not sel:
            messagebox.showwarning("No selection", "Please select a character to edit.")
            return
        name = self.character_listbox.get(sel)
        self.open_character_window(is_edit=True, existing_name=name)

    def open_character_window(self, is_edit=False, existing_name=None):
        win = tk.Toplevel(self.master)
        win.title("Edit Character" if is_edit else "Create Character")
        win.geometry("600x400")

        # Row 0: Name & Level
        tk.Label(win, text="Character Name:").grid(row=0, column=0, sticky="w", padx=8, pady=2)
        name_entry = tk.Entry(win)
        name_entry.grid(row=0, column=1, padx=8, pady=2)

        tk.Label(win, text="Character Level:").grid(row=0, column=2, sticky="w", padx=8, pady=2)
        lvl_entry = tk.Entry(win)
        lvl_entry.grid(row=0, column=3, padx=8, pady=2)

        # Row 2: Class & Subclass
        tk.Label(win, text="Class:").grid(row=1, column=0, sticky="w", padx=8, pady=2)

        class_var = tk.StringVar(value="None")
        class_choices = ["None"] + sorted(self.class_mapping.keys())
        class_menu = tk.OptionMenu(win, class_var, *class_choices)
        class_menu.grid(row=1, column=1, sticky="w", padx=8, pady=2)

        tk.Label(win, text="Subclass:").grid(row=1, column=2, sticky="w", padx=8, pady=2)

        subclass_var = tk.StringVar(value="None")
        subclass_menu = tk.OptionMenu(win, subclass_var, "None")
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

        # Row 3: STR & DEX
        tk.Label(win, text="STR modifier:").grid(row=2, column=0, sticky="w", padx=6, pady=2)
        str_entry = tk.Entry(win)
        str_entry.grid(row=2, column=1, padx=6, pady=2)

        tk.Label(win, text="DEX modifier:").grid(row=2, column=2, sticky="w", padx=6, pady=2)
        dex_entry = tk.Entry(win)
        dex_entry.grid(row=2, column=3, padx=6, pady=2)

        # Row 4: CON & INT
        tk.Label(win, text="CON modifier:").grid(row=3, column=0, sticky="w", padx=6, pady=2)
        con_entry = tk.Entry(win)
        con_entry.grid(row=3, column=1, padx=6, pady=2)

        tk.Label(win, text="INT modifier:").grid(row=3, column=2, sticky="w", padx=6, pady=2)
        int_entry = tk.Entry(win)
        int_entry.grid(row=3, column=3, padx=6, pady=2)

        # Row 5: CON & INT
        tk.Label(win, text="WIS modifier:").grid(row=4, column=0, sticky="w", padx=6, pady=2)
        wis_entry = tk.Entry(win)
        wis_entry.grid(row=4, column=1, padx=6, pady=2)

        tk.Label(win, text="CHA modifier:").grid(row=4, column=2, sticky="w", padx=6, pady=2)
        cha_entry = tk.Entry(win)
        cha_entry.grid(row=4, column=3, padx=6, pady=2)

        # Row 6: Standard Weapon & Standard Weapon Bonus

        tk.Label(win, text="Standard Weapon:").grid(row=5, column=0, sticky="w", padx=8, pady=2)
        standard_weapon_var = tk.StringVar(value="None")
        standard_weapon_choices = ["None"] + sorted(self.weapon_mapping.keys())
        standard_weapon_menu = tk.OptionMenu(win, standard_weapon_var, *standard_weapon_choices)
        standard_weapon_menu.grid(row=5, column=1, sticky="w", padx=8, pady=2)

        tk.Label(win, text="Standard Weapon Bonus:").grid(row=5, column=2, sticky="w", padx=8, pady=2)
        standard_weapon_bonus_entry = tk.Entry(win)
        standard_weapon_bonus_entry.grid(row=5, column=3, sticky="w", pady=(8, 0), padx=6)

        modifier_vars_local = {}
        mod_by_cat = defaultdict(list)
        for name, cls in self.modifier_mapping.items():
            mod_by_cat[cls.category].append(name)

        category_order = ["Fighting Style", "Feat", "Class Feature Manual", "Other"]
        row_offset = 8
        for cat in category_order:
            mods = mod_by_cat.get(cat, [])
            if not mods:
                continue
            tk.Label(win, text=f"{cat}:").grid(row=row_offset, column=0, sticky="w", padx=6, pady=(8, 2))
            i = 0
            col_count = 4
            for name in mods:
                var = tk.BooleanVar(value=False)
                modifier_vars_local[name] = var
                r = row_offset + 1 + i // col_count
                c = i % col_count
                tk.Checkbutton(win, text=name, variable=var).grid(row=r, column=c, sticky="w", padx=6, pady=2)
                i += 1
            row_offset += 1 + (len(mods) + col_count - 1) // col_count

        # pre-fill fields if editing
        if is_edit and existing_name:
            data = self.characters.get(existing_name, {})
            name_entry.insert(0, existing_name)
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
            standard_weapon_bonus_entry.insert(0, str(data.get("standard_weapon_bonus", 0)))

            # restore selected modifiers
            for mod_name in data.get("modifiers", []):
                if mod_name in modifier_vars_local:
                    modifier_vars_local[mod_name].set(True)

        def save_and_close():
            name = name_entry.get().strip()
            if not name:
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
                stdb = int(standard_weapon_bonus_entry.get().strip())
            except ValueError:
                messagebox.showerror("Error", "STR/DEX/CHA/etc must be integers.")
                return

            # Collect selected modifiers
            selected_mods = [name for name, var in modifier_vars_local.items() if var.get()]
            cls_name = class_var.get()
            subcls_name = subclass_var.get()
            std_weapon = standard_weapon_var.get()

            # Save to in-memory dict and file
            self.characters[name] = {
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
                "standard_weapon_bonus": stdb
            }

            # If renaming, delete old key
            if is_edit and existing_name and existing_name != name:
                self.characters.pop(existing_name, None)

            self.save_characters_to_file()
            self.refresh_character_listbox()
            win.destroy()

        save_button = tk.Button(win, text="Save", command=save_and_close)
        save_button.grid(row=row_offset + (i + 1) // 2, column=0, columnspan=4, pady=10)

    def delete_selected(self):
        sel = self.character_listbox.curselection()
        if not sel:
            messagebox.showwarning("No selection", "Please select a character to delete.")
            return
        name = self.character_listbox.get(sel)
        if messagebox.askyesno("Confirm", f"Delete '{name}'?"):
            self.characters.pop(name, None)
            self.save_characters_to_file()
            self.refresh_character_listbox()

    def refresh_character_listbox(self):
        self.character_listbox.delete(0, tk.END)
        for name in sorted(self.characters.keys()):
            self.character_listbox.insert(tk.END, name)

    def import_json(self):
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json"), ("All files","*.*")])
        if not path:
            return
        try:
            with open(path, "r") as f:
                data = json.load(f)
            if isinstance(data, dict):
                self.characters.update(data)
                self.save_characters_to_file()
                self.refresh_character_listbox()
                messagebox.showinfo("Imported", "Characters imported successfully.")
            else:
                messagebox.showerror("Error", "JSON must be an object/dict mapping names -> attributes.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import: {e}")

    def export_json(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files","*.json")])
        if not path:
            return
        try:
            with open(path, "w") as f:
                json.dump(self.characters, f, indent=2)
            messagebox.showinfo("Exported", f"Exported to {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {e}")

    def run_expected_damage(self):
        sel = self.character_listbox.curselection()
        if not sel:
            messagebox.showwarning("No character", "Please select a character from the list.")
            return
        name = self.character_listbox.get(sel)
        char_data = self.characters.get(name)
        if not char_data:
            messagebox.showerror("Error", "Character data missing.")
            return

        # Instantiate Character
        try:
            char_obj = Character(
                lvl = char_data.get("lvl", 0),
                str_mod=char_data.get("str", 0),
                dex_mod=char_data.get("dex", 0),
                cha_mod=char_data.get("cha", 0),
                wis_mod=char_data.get("wis", 0),
                con_mod=char_data.get("con", 0),
                int_mod=char_data.get("int", 0)
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to instantiate Character: {e}")
            return

        char_obj.clear_modifiers()

        class_name = char_data.get("class", "")
        class_cls = self.class_mapping.get(class_name)
        if class_cls:
            char_obj.set_class(class_cls)

        subclass_name = char_data.get("subclass", "")
        subclass_cls = self.subclass_mapping.get(subclass_name)
        if subclass_cls:
            char_obj.set_subclass(subclass_cls)

        char_obj.apply_class_features()

        for mod_name in char_data.get("modifiers", []):
            modifier_class = self.modifier_mapping.get(mod_name)
            if modifier_class:
                char_obj.add_modifier(modifier_class)

        char_obj.default_weapon_name = char_data.get("standard_weapon", "")

        char_obj.default_weapon_bonus = char_data.get("standard_weapon_bonus", 0)

        # Build AttackContext
        stat = self.stat_var.get()
        if char_obj.default_weapon_bonus == 0:
            magic_str = self.magic_entry.get().strip()
            if magic_str == "":
                magic_bonus = 0
            else:
                try:
                    magic_bonus = int(magic_str)
                except ValueError:
                    messagebox.showerror("Error", "Magic Bonus must be an integer.")
                    return
        else:
            magic_bonus = char_obj.default_weapon_bonus

        ctx = AttackContext(
            stat=stat,
            magic_bonus=magic_bonus,
            use_mastery=self.mastery_var.get(),
            two_handed=self.twohand_var.get()
        )

        # Target AC
        try:
            ac = int(self.ac_entry.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Target AC must be an integer.")
            return

        weapon_mapping = self.weapon_mapping
        weapon_name = self.weapon_var.get()

        # --- Resolve weapon ---
        if weapon_name == "Use Character Weapon":
            weapon_obj = char_obj.get_default_weapon(weapon_mapping)
            if weapon_obj is None:
                messagebox.showerror(
                    "Error",
                    "This character does not have a standard weapon set."
                )
                return
        else:
            weapon_class = weapon_mapping.get(weapon_name)
            if weapon_class is None:
                messagebox.showerror(
                    "Error",
                    f"Weapon '{weapon_name}' not in mapping."
                )
                return
            weapon_obj = weapon_class(char_obj)

        # Spell placeholder
        if self.spell_var.get() != "None":
            messagebox.showinfo(
                "Spell placeholder",
                "Spell support is not yet implemented in the backend. "
                "Select 'None' or add your spell class_files later."
            )
            return

        # Call expected_damage
        try:
            result = weapon_obj.expected_damage(ac, ctx)
            self.last_result = result

            # Save the weapon object so display_result() can show applied modifiers
            self._current_weapon_obj = weapon_obj

        except Exception as e:
            messagebox.showerror("Error", f"Call to expected_damage failed: {e}")
            return

        # Show formatted output
        self.display_result(result, ac, weapon_name, ctx,  char_obj)

    def display_result(self, result, ac, weapon_name, ctx, char_obj):
        self.result_text.delete("1.0", tk.END)

        weapon_obj = getattr(self, "_current_weapon_obj", None)

        num_attacks = result.get("num_attacks", 1)

        per_turn_dis = result.get('disadvantage', 0)
        per_turn_norm = result.get('normal', 0)
        per_turn_adv = result.get('advantage', 0)

        per_attack_dis = per_turn_dis / num_attacks
        per_attack_norm = per_turn_norm / num_attacks
        per_attack_adv = per_turn_adv / num_attacks

        lines = []
        lines.append(f"Expected damage vs AC {ac}")
        lines.append("")

        lines.append("Expected damage per turn:        (per attack)")
        lines.append(f"  With disadvantage : {per_turn_dis:8.2f}   ({per_attack_dis:.2f})")
        lines.append(f"  Normal roll       : {per_turn_norm:8.2f}   ({per_attack_norm:.2f})")
        lines.append(f"  With advantage    : {per_turn_adv:8.2f}   ({per_attack_adv:.2f})")

        breakdown = result.get("breakdown")
        if breakdown:
            lines.append("")
            lines.append("Hit / Crit / Miss probabilities:")

            for mode in ["normal", "advantage", "disadvantage"]:
                p = breakdown.get(mode, {})
                miss = p.get("miss", 0)
                hit = p.get("hit", 0)
                crit = p.get("crit", 0)
                lines.append(
                    f"  {mode.capitalize():13}: "
                    f"hit={hit:.3f}  crit={crit:.3f}  miss={miss:.3f}"
                )

        if weapon_obj:
            char_mods = getattr(weapon_obj.owner, "modifiers", [])
            applied = [
                m for m in char_mods
                if ctx.use_mastery or not getattr(m, "is_mastery", False)
            ]
            mod_names = [type(m).gui_name for m in applied]
            lines.append("")
            lines.append("Applied modifiers: " + (", ".join(mod_names) if mod_names else "None"))
            lines.insert(1, f"Weapon used: {type(weapon_obj).gui_name}")

        self.result_text.insert(tk.END, "\n".join(lines))

    def show_last_result(self):
        if not self.last_result:
            messagebox.showinfo("No result", "No previous result computed.")
            return

        dbg = self.last_result.get("debug", {})
        dmg = dbg.get("damage", {})
        br = dbg.get("breakdown", {})

        lines = []
        lines.append("=== RAW DAMAGE VALUES ===")
        lines.append(f"Miss damage       : {dmg.get('miss', 0):.2f}")
        lines.append(f"Normal hit damage : {dmg.get('hit', 0):.2f}")
        lines.append(f"Critical damage   : {dmg.get('crit', 0):.2f}")
        lines.append("")

        lines.append("=== HIT PROBABILITIES ===")
        for mode in ["disadvantage", "normal", "advantage"]:
            p = br.get(mode, {})
            lines.append(
                f"{mode.capitalize():13}: "
                f"miss={p.get('miss', 0):.3f},  "
                f"hit={p.get('hit', 0):.3f},  "
                f"crit={p.get('crit', 0):.3f}"
            )

        lines.append("")
        lines.append("=== EXPECTED DAMAGE ===")
        lines.append(f"With disadvantage : {self.last_result.get('disadvantage', 0):.2f}")
        lines.append(f"Normal roll       : {self.last_result.get('normal', 0):.2f}")
        lines.append(f"With advantage    : {self.last_result.get('advantage', 0):.2f}")

        win = tk.Toplevel(self.master)
        win.title("Last Result (debug)")
        win.geometry("520x420")

        frame = tk.Frame(win)
        frame.pack(fill="both", expand=True, padx=8, pady=8)

        text = tk.Text(frame, wrap="word")
        text.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(frame, command=text.yview)
        scrollbar.pack(side="right", fill="y")
        text.config(yscrollcommand=scrollbar.set)

        text.insert("1.0", "\n".join(lines))
        text.config(state="disabled")


def main():
    root = tk.Tk()
    app = MinimalDNDGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()