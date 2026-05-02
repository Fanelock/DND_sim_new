"""
dndbeyond_import.py  -  Drop-in module for DND_sim_new

Fetches a D&D Beyond character JSON via the share link / character ID and
returns a dict that matches the schema used by ``self.characters[name]``
elsewhere in this project (see ``character_window.py``).

The schema is, intentionally identical to the one ``CharacterWindow``
writes back on save:

    {
        "lvl":                   int,
        "class":                 str,         # only the highest-level class
                                              #   (multiclassing is collapsed)
        "subclass":              str,
        "str", "dex", "con",
        "int", "wis", "cha":     int,         # MODIFIER values (-5..+10)
        "modifiers":             [str, ...],
        "standard_weapon":       str,
        "standard_weapon_bonus": int,
        "main_stat":             str,         # "str"/"dex"/.../"cha"
        "HP":                    int,
        "AC":                    int,
        "init_bonus":            int,         # EXTRA bonus beyond DEX
                                              #   (0 if initiative == dex)
        "custom_weapon":         dict,
        "custom_modifiers":      [dict, ...],
    }
"""

import json
import re
import urllib.error
import urllib.request


# ---------------------------------------------------------------------------
# Class -> default attack stat mapping. Used to pre-fill ``main_stat`` so the
# DM doesn't have to set it manually. They can still override it in the edit
# window.
# ---------------------------------------------------------------------------
CLASS_MAIN_STAT = {
    "barbarian": "str",
    "fighter":   "str",
    "paladin":   "str",
    "monk":      "dex",
    "ranger":    "dex",
    "rogue":     "dex",
    "artificer": "int",
    "wizard":    "int",
    "cleric":    "wis",
    "druid":     "wis",
    "bard":      "cha",
    "sorcerer":  "cha",
    "warlock":   "cha",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _stat_to_mod(score: int) -> int:
    return (score - 10) // 2


def _extract_character_id(raw: str) -> str | None:
    """Accept a full share URL or a bare integer."""
    raw = raw.strip()
    m = re.search(r"/characters/(\d+)", raw)
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


def _mod_value(mod: dict) -> int:
    """
    Pull a numeric value out of a DDB modifier object.

    DDB stores numeric bonuses in either ``value`` or ``fixedValue`` -- never
    in ``componentId`` (that's an internal reference id, not a value) and
    rarely in ``dataValue`` for stat-style mods. We deliberately ignore the
    id-style fields to avoid pulling in 7-digit junk.
    """
    for key in ("value", "fixedValue"):
        v = mod.get(key)
        if isinstance(v, (int, float)):
            return int(v)
    return 0


# ---------------------------------------------------------------------------
# Main parser
# ---------------------------------------------------------------------------
def parse_character(raw_json: dict) -> dict:
    """Convert a DDB character payload into the local self.characters schema."""
    data = raw_json.get("data", raw_json)

    # ── name ───────────────────────────────────────────────────────────────
    name: str = data.get("name", "Unknown Character")

    # ── class & level (collapse multiclass to the highest-level class) ─────
    classes = data.get("classes", []) or []
    total_level = sum(c.get("level", 0) for c in classes)

    if classes:
        primary = max(
            classes,
            key=lambda c: (
                c.get("level", 0),
                c.get("isStartingClass", False),
            ),
        )
        class_name = primary.get("definition", {}).get("name", "Unknown")
        sub_def = primary.get("subclassDefinition") or {}
        subclass_name = sub_def.get("name", "") if isinstance(sub_def, dict) else ""
    else:
        class_name = "Unknown"
        subclass_name = ""

    # ── base ability scores ────────────────────────────────────────────────
    # stats[]: id 1=STR 2=DEX 3=CON 4=INT 5=WIS 6=CHA
    def _stat_dict(key):
        return {s["id"]: (s.get("value") or 0) for s in (data.get(key, []) or [])}

    stat_map     = _stat_dict("stats")
    bonus_map    = _stat_dict("bonusStats")
    override_map = {
        s["id"]: s.get("value")
        for s in (data.get("overrideStats", []) or [])
    }

    def get_score(sid: int) -> int:
        if override_map.get(sid) is not None:
            return override_map[sid]
        return stat_map.get(sid, 10) + bonus_map.get(sid, 0)

    scores = {sid: get_score(sid) for sid in range(1, 7)}

    # ── racial ASI ─────────────────────────────────────────────────────────
    # We accept either:
    #   * displayConfiguration.ABILITYSCORE == 1   (the strict marker), OR
    #   * trait name starts with "Ability Score Increase"
    racial_traits = (
        (data.get("race") or {}).get("racialTraits", []) or []
    )
    stat_id_map = {
        "strength": 1, "str": 1,
        "dexterity": 2, "dex": 2,
        "constitution": 3, "con": 3,
        "intelligence": 4, "int": 4,
        "wisdom": 5, "wis": 5,
        "charisma": 6, "cha": 6,
    }
    for rt in racial_traits:
        defn = rt.get("definition", {}) or {}
        display_cfg = defn.get("displayConfiguration", {}) or {}
        is_asi = (
            display_cfg.get("ABILITYSCORE", 0) == 1
            or str(defn.get("name", "")).lower().startswith("ability score increase")
        )
        if not is_asi:
            continue

        desc = (defn.get("description") or "") + " " + (defn.get("name") or "")
        desc_l = desc.lower()
        # Try several patterns DDB uses in flavour text.
        amount_match = re.search(
            r"(?:increase\s+\w+\s+by\s+|[+])\s*(\d+)",
            desc_l,
        )
        amount = int(amount_match.group(1)) if amount_match else 1

        for keyword, sid in stat_id_map.items():
            if re.search(rf"\b{keyword}\b", desc_l):
                scores[sid] += amount
                break  # one stat per trait

    # ── feat / class ASI from modifiers (Resilient, Boon, etc.) ────────────
    modifier_groups = data.get("modifiers", {}) or {}
    all_mods = []
    if isinstance(modifier_groups, dict):
        for group_mods in modifier_groups.values():
            if isinstance(group_mods, list):
                all_mods.extend(group_mods)

    for mod in all_mods:
        mtype = (mod.get("type") or "").lower()
        sub = (mod.get("subType") or "").lower()
        if sub not in stat_id_map:
            continue
        sid = stat_id_map[sub]
        val = _mod_value(mod)
        if val <= 0:
            continue
        if mtype == "bonus":
            scores[sid] = min(scores[sid] + val, 20)
        elif mtype == "set":
            # "set base ability score to X"
            scores[sid] = max(scores[sid], val)

    str_mod = _stat_to_mod(scores[1])
    dex_mod = _stat_to_mod(scores[2])
    con_mod = _stat_to_mod(scores[3])
    int_mod = _stat_to_mod(scores[4])
    wis_mod = _stat_to_mod(scores[5])
    cha_mod = _stat_to_mod(scores[6])

    # ── max HP: base + bonus + level × CON_mod ─────────────────────────────
    base_hp     = data.get("baseHitPoints") or 0
    bonus_hp    = data.get("bonusHitPoints") or 0
    override_hp = data.get("overrideHitPoints")
    if override_hp is not None:
        max_hp = int(override_hp)
    else:
        max_hp = int(base_hp) + int(bonus_hp) + total_level * con_mod

    # ── AC ─────────────────────────────────────────────────────────────────
    override_ac = data.get("overrideArmorClass")
    if override_ac is not None:
        computed_ac = int(override_ac)
    else:
        inventory = data.get("inventory", []) or []
        equipped = [i for i in inventory if i.get("equipped")]

        base_ac = 10
        armor_ac = None
        uses_dex_for_ac = True
        dex_cap = 99

        for item in equipped:
            defn = item.get("definition", {}) or {}
            armor_type = defn.get("armorTypeId")
            armor_class = defn.get("armorClass")
            if armor_type is None or armor_class is None:
                continue
            if armor_type == 1:        # Light
                armor_ac = armor_class
                dex_cap = 99
            elif armor_type == 2:      # Medium
                armor_ac = armor_class
                dex_cap = 2
            elif armor_type == 3:      # Heavy
                armor_ac = armor_class
                uses_dex_for_ac = False
                dex_cap = 0
            elif armor_type == 4:      # Shield
                # handled below as a generic +AC bonus, but DDB also
                # ships shields with armorClass=2 sometimes.
                pass

        ac_bonus = 0
        for item in equipped:
            defn = item.get("definition", {}) or {}
            requires_attunement = bool(defn.get("canAttune"))
            is_attuned = bool(item.get("isAttuned"))
            for gm in (defn.get("grantedModifiers", []) or []):
                if gm.get("requiresAttunement") and not is_attuned:
                    continue
                # Skip item-level granted modifiers if the item itself
                # requires attunement and isn't attuned.
                if requires_attunement and not is_attuned:
                    continue
                gtype = (gm.get("type") or "").lower()
                gsub = (gm.get("subType") or "").lower()
                if gtype == "bonus" and gsub == "armor-class":
                    ac_bonus += _mod_value(gm)
                elif gtype == "set" and gsub == "unarmored-armor-class":
                    if armor_ac is None:
                        v = _mod_value(gm)
                        if v:
                            base_ac = v
            # Shield armorTypeId == 4 grants a flat +shield AC even if no
            # grantedModifier mirrors it.
            if (defn.get("armorTypeId") == 4) and defn.get("armorClass"):
                ac_bonus += int(defn.get("armorClass") or 0)

        if armor_ac is not None:
            dex_contribution = min(dex_mod, dex_cap) if uses_dex_for_ac else 0
            computed_ac = armor_ac + dex_contribution + ac_bonus
        else:
            computed_ac = base_ac + dex_mod + ac_bonus

    # ── initiative ─────────────────────────────────────────────────────────
    # Per spec: if initiative_total == dex_mod, the field stays at 0
    # (i.e. "leave empty"). If feats/items add extra to initiative, that
    # delta is written into init_bonus.
    init_extra = 0
    for mod in all_mods:
        sub = (mod.get("subType") or "").lower()
        if sub == "initiative":
            init_extra += _mod_value(mod)

    init_bonus = init_extra  # 0 when initiative == dex_mod

    # ── main_stat: pick a sensible default from the dominant class ─────────
    main_stat = CLASS_MAIN_STAT.get(class_name.lower(), "str")

    # ── return ─────────────────────────────────────────────────────────────
    return {
        "name":                  name,
        "lvl":                   total_level,
        "class":                 class_name,
        "subclass":              subclass_name,
        "str":                   str_mod,
        "dex":                   dex_mod,
        "con":                   con_mod,
        "int":                   int_mod,
        "wis":                   wis_mod,
        "cha":                   cha_mod,
        "HP":                    int(max_hp),
        "AC":                    int(computed_ac),
        "init_bonus":            int(init_bonus),
        "main_stat":             main_stat,
        "modifiers":             [],
        "standard_weapon":       "",
        "standard_weapon_bonus": 0,
        "custom_weapon":         {},
        "custom_modifiers":      [],
    }


# ---------------------------------------------------------------------------
# Public entry point used by the GUI
# ---------------------------------------------------------------------------
def import_from_url(url_or_id: str) -> dict:
    """
    Fetch + parse a D&D Beyond character.

    :returns: character dict (matches CharacterWindow's save schema)
    :raises ValueError: with a human-readable message on failure
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
