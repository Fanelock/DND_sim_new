"""
dndbeyond_import.py  –  Drop-in module for DND_sim_new
Fetches a D&D Beyond character JSON via the share link / character ID
and returns a dict that matches the self.characters[name] schema.
"""

import re
import json
import urllib.request
import urllib.error


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _stat_to_mod(score: int) -> int:
    return (score - 10) // 2


def _extract_character_id(raw: str) -> str | None:
    """Accept a full share URL or a bare integer."""
    raw = raw.strip()
    m = re.search(r'/characters/(\d+)', raw)
    if m:
        return m.group(1)
    if raw.isdigit():
        return raw
    return None


def _fetch_json(char_id: str) -> dict:
    url = f"https://character-service.dndbeyond.com/character/v5/character/{char_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


# ──────────────────────────────────────────────────────────────────────────────
# Main parser
# ──────────────────────────────────────────────────────────────────────────────

def parse_character(raw_json: dict) -> dict:
    data = raw_json.get("data", raw_json)

    # ── name ──────────────────────────────────────────────────────────────────
    name: str = data.get("name", "Unknown Character")

    # ── classes ───────────────────────────────────────────────────────────────
    classes = data.get("classes", [])
    total_level = sum(c.get("level", 0) for c in classes)

    if classes:
        primary = max(classes, key=lambda c: (
            c.get("level", 0),
            c.get("isStartingClass", False)
        ))
        class_name: str = primary.get("definition", {}).get("name", "Unknown")
    else:
        class_name = "Unknown"
        total_level = 0

    # ── base ability scores ───────────────────────────────────────────────────
    # stats[]: id 1=STR 2=DEX 3=CON 4=INT 5=WIS 6=CHA
    stat_map = {s["id"]: (s.get("value") or 0) for s in data.get("stats", [])}
    bonus_map = {s["id"]: (s.get("value") or 0) for s in data.get("bonusStats", [])}
    override_map = {s["id"]: s.get("value") for s in data.get("overrideStats", [])}

    def get_score(sid: int) -> int:
        if override_map.get(sid) is not None:
            return override_map[sid]
        return stat_map.get(sid, 10) + bonus_map.get(sid, 0)

    str_score = get_score(1)
    dex_score = get_score(2)
    con_score = get_score(3)
    int_score = get_score(4)
    wis_score = get_score(5)
    cha_score = get_score(6)

    # ── racial ASI ────────────────────────────────────────────────────────────
    racial_traits = (
        data.get("race", {}).get("racialTraits", []) or []
    )
    racial_bonus = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
    for rt in racial_traits:
        defn = rt.get("definition", {})
        display_cfg = defn.get("displayConfiguration", {})
        if display_cfg.get("ABILITYSCORE", 0) != 1:
            continue
        desc = defn.get("description", "")
        # Parse "+N to <stat>"
        for stat_id, keywords in [
            (1, ["strength", "str"]),
            (2, ["dexterity", "dex"]),
            (3, ["constitution", "con"]),
            (4, ["intelligence", "int"]),
            (5, ["wisdom", "wis"]),
            (6, ["charisma", "cha"]),
        ]:
            if any(k in desc.lower() for k in keywords):
                m = re.search(r'[Ii]ncrease\s+\w+\s+by\s+(\d+)|[+](\d+)\s+to', desc)
                if m:
                    val = int(m.group(1) or m.group(2))
                    racial_bonus[stat_id] += val

    str_score += racial_bonus[1]
    dex_score += racial_bonus[2]
    con_score += racial_bonus[3]
    int_score += racial_bonus[4]
    wis_score += racial_bonus[5]
    cha_score += racial_bonus[6]

    # ── feat / choice ASI from modifiers ────────────────────────────────────
    # DDB stores chosen ability-score bonuses in data["modifiers"]["feat"],
    # data["modifiers"]["class"], etc.
    modifier_groups = data.get("modifiers", {})
    if isinstance(modifier_groups, dict):
        all_mods = []
        for group_mods in modifier_groups.values():
            if isinstance(group_mods, list):
                all_mods.extend(group_mods)
    else:
        all_mods = []

    stat_id_map = {
        "strength": 1, "dexterity": 2, "constitution": 3,
        "intelligence": 4, "wisdom": 5, "charisma": 6,
    }
    for mod in all_mods:
        if mod.get("type") != "bonus":
            continue
        sub = (mod.get("subType") or "").lower()
        if sub not in stat_id_map:
            continue
        val = mod.get("value") or mod.get("fixedValue") or 0
        sid = stat_id_map[sub]
        if sid == 1: str_score  = min(str_score  + val, 20)
        if sid == 2: dex_score  = min(dex_score  + val, 20)
        if sid == 3: con_score  = min(con_score  + val, 20)
        if sid == 4: int_score  = min(int_score  + val, 20)
        if sid == 5: wis_score  = min(wis_score  + val, 20)
        if sid == 6: cha_score  = min(cha_score  + val, 20)

    str_mod = _stat_to_mod(str_score)
    dex_mod = _stat_to_mod(dex_score)
    con_mod = _stat_to_mod(con_score)
    int_mod = _stat_to_mod(int_score)
    wis_mod = _stat_to_mod(wis_score)
    cha_mod = _stat_to_mod(cha_score)

    # ── max HP ────────────────────────────────────────────────────────────────
    base_hp    = data.get("baseHitPoints") or 0
    bonus_hp   = data.get("bonusHitPoints") or 0
    override_hp = data.get("overrideHitPoints")
    if override_hp is not None:
        max_hp = override_hp
    else:
        max_hp = base_hp + bonus_hp + total_level * con_mod

    # ── AC ────────────────────────────────────────────────────────────────────
    # Armour from inventory
    inventory = data.get("inventory", [])
    equipped  = [i for i in inventory if i.get("equipped")]

    base_ac = 10  # unarmoured fallback
    armor_ac = None
    uses_dex_for_ac = True
    dex_cap = 99  # no cap by default

    for item in equipped:
        defn = item.get("definition", {})
        if defn.get("armorTypeId") is None:
            continue
        armor_class = defn.get("armorClass")
        if armor_class is None:
            continue
        stealth_check = defn.get("stealthCheck", 0) or 0  # just metadata
        armor_type = defn.get("armorTypeId", 0)
        # 1 = Light, 2 = Medium, 3 = Heavy, 4 = Shield
        if armor_type == 1:    # Light
            armor_ac = armor_class; dex_cap = 99
        elif armor_type == 2:  # Medium
            armor_ac = armor_class; dex_cap = 2
        elif armor_type == 3:  # Heavy
            armor_ac = armor_class; uses_dex_for_ac = False; dex_cap = 0
        # Shields handled via grantedModifiers below

    ac_bonus = 0
    for item in equipped:
        if not (item.get("isAttuned", True)):
            attuned = item.get("isAttuned", False)
            defn = item.get("definition", {})
            if defn.get("canAttune") and not attuned:
                continue
        defn = item.get("definition", {})
        for gm in defn.get("grantedModifiers", []):
            if gm.get("requiresAttunement") and not item.get("isAttuned"):
                continue
            if gm.get("type") == "bonus" and gm.get("subType") == "armor-class":
                ac_bonus += gm.get("value") or gm.get("fixedValue") or 0
            if gm.get("type") == "set" and gm.get("subType") == "unarmored-armor-class":
                if armor_ac is None:
                    base_ac = gm.get("value") or 10

    if armor_ac is not None:
        dex_contribution = min(dex_mod, dex_cap) if uses_dex_for_ac else 0
        computed_ac = armor_ac + dex_contribution + ac_bonus
    else:
        computed_ac = base_ac + dex_mod + ac_bonus

    # ── initiative ────────────────────────────────────────────────────────────
    # Check for any initiative-specific bonuses (feats like Alert, etc.)
    init_bonus_extra = 0
    for mod in all_mods:
        sub = (mod.get("subType") or "").lower()
        if sub == "initiative":
            val = mod.get("value") or mod.get("fixedValue") or 0
            init_bonus_extra += val

    # initiative field: only store the *extra* bonus beyond dex_mod
    initiative_bonus = init_bonus_extra  # 0 if purely dex-based

    return {
        "name":               name,
        "class":              class_name,
        "lvl":                total_level,
        "HP":                 max_hp,
        "str":                str_mod,
        "dex":                dex_mod,
        "con":                con_mod,
        "int":                int_mod,
        "wis":                wis_mod,
        "cha":                cha_mod,
        "AC":                 computed_ac,
        "initiative_bonus":   initiative_bonus,
        "modifiers":          [],
        "standardweapon":     None,
        "standardweaponbonus": 0,
        "mainstat":           "cha",  # Warlock default; user can override
        "customweapon":       {},
        "custommodifiers":    [],
    }


# ──────────────────────────────────────────────────────────────────────────────
# Public entry point used by the GUI
# ──────────────────────────────────────────────────────────────────────────────

def import_from_url(url_or_id: str) -> dict:
    """
    Fetch + parse a D&D Beyond character.
    Returns the character dict on success.
    Raises ValueError with a human-readable message on failure.
    """
    char_id = _extract_character_id(url_or_id)
    if not char_id:
        raise ValueError(
            "Could not find a character ID in the provided URL.\n"
            "Expected format: https://dndbeyond.com/characters/144539009"
        )
    try:
        raw = _fetch_json(char_id)
    except urllib.error.HTTPError as e:
        raise ValueError(
            f"D&D Beyond returned HTTP {e.code}.\n"
            "Make sure the character is set to Public in D&D Beyond sharing settings."
        ) from e
    except Exception as e:
        raise ValueError(f"Network error: {e}") from e

    return parse_character(raw)