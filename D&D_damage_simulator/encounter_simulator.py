"""
Round-by-round encounter simulator.

Damage is deterministic — each combatant deals the precomputed expected
damage-per-attack supplied by the GUI (no per-attack dice rolls).
The only random element is the **initiative roll** (1d20 + dex / init bonus)
plus, depending on the chosen target-priority strategy, a random pick
between equally-eligible enemy targets for player attacks.

A combat is resolved by stepping through rounds in initiative order until
one side has no living combatants left.
"""

import random
from typing import List, Optional


# ----------------------------------------------------------------------
# Combatant
# ----------------------------------------------------------------------
class Combatant:
    """Generic combatant — used for both party members and enemies."""

    def __init__(self, name, side, hp, ac, to_hit, init_bonus,
                 num_attacks, damage_per_attack, role="", label=""):
        """
        :param side: ``"party"`` or ``"enemy"``.
        :param role: For enemies — ``"Boss"``, ``"Add"`` or ``"Minion"``.
        :param label: Optional descriptor (e.g. weapon / spell name) for the log.
        """
        self.name = name
        self.side = side
        self.max_hp = int(hp)
        self.hp = int(hp)
        self.ac = int(ac)
        self.to_hit = int(to_hit)
        self.init_bonus = int(init_bonus)
        self.num_attacks = max(0, int(num_attacks))
        self.damage_per_attack = float(damage_per_attack)
        self.role = role
        self.label = label
        self.initiative = 0  # set by EncounterSimulator.roll_initiative()

    @property
    def alive(self):
        return self.hp > 0

    def take_damage(self, dmg):
        self.hp = max(0, self.hp - dmg)

    def __repr__(self):
        return f"<Combatant {self.name} {self.side} HP={self.hp}/{self.max_hp}>"


# ----------------------------------------------------------------------
# Encounter
# ----------------------------------------------------------------------
PRIORITY_BOSS_FIRST = "boss_first"
PRIORITY_ADDS_FIRST = "adds_first"
PRIORITY_RANDOM = "random"

VALID_PRIORITIES = (PRIORITY_BOSS_FIRST, PRIORITY_ADDS_FIRST, PRIORITY_RANDOM)


class EncounterSimulator:
    """
    Simulates an encounter round-by-round using deterministic damage.

    Usage:
        sim = EncounterSimulator(party, enemies, priority="boss_first")
        result = sim.run()
        # result == {"winner": "party"|"enemies"|"draw",
        #            "rounds": int,
        #            "log": [str, ...],
        #            "party_survivors": [...],
        #            "enemy_survivors": [...]}
    """

    MAX_ROUNDS = 100  # safety cap to avoid pathological infinite loops

    def __init__(self, party: List[Combatant], enemies: List[Combatant],
                 priority: str = PRIORITY_BOSS_FIRST,
                 rng: Optional[random.Random] = None):
        if priority not in VALID_PRIORITIES:
            raise ValueError(
                f"Invalid priority {priority!r}. Use one of {VALID_PRIORITIES}."
            )
        self.party = list(party)
        self.enemies = list(enemies)
        self.priority = priority
        self.rng = rng or random.Random()
        self.log: List[str] = []
        self.round_no = 0

    # ------------------------------------------------------------------
    # Initiative
    # ------------------------------------------------------------------
    def roll_initiative(self):
        """Roll 1d20 + init_bonus for every combatant. Tie-break randomly."""
        for c in self.party + self.enemies:
            roll = self.rng.randint(1, 20)
            c.initiative = roll + c.init_bonus
            self.log.append(
                f"  {c.name} ({c.side}) rolls {roll} + {c.init_bonus} = {c.initiative}"
            )

        # Sort: highest initiative first; random tie-break.
        order = self.party + self.enemies
        order.sort(
            key=lambda c: (c.initiative, self.rng.random()),
            reverse=True,
        )
        return order

    # ------------------------------------------------------------------
    # Target selection
    # ------------------------------------------------------------------
    def _living(self, combatants):
        return [c for c in combatants if c.alive]

    def _pick_player_target(self):
        """Pick a single enemy target according to the configured priority."""
        living_enemies = self._living(self.enemies)
        if not living_enemies:
            return None

        if self.priority == PRIORITY_RANDOM:
            return self.rng.choice(living_enemies)

        # boss_first / adds_first: bucket by role and pick from the
        # preferred bucket if it has any living members, else fall back.
        bosses = [e for e in living_enemies if e.role == "Boss"]
        non_bosses = [e for e in living_enemies if e.role != "Boss"]

        if self.priority == PRIORITY_BOSS_FIRST:
            primary, fallback = bosses, non_bosses
        else:  # PRIORITY_ADDS_FIRST
            primary, fallback = non_bosses, bosses

        pool = primary if primary else fallback
        # Random pick within the chosen bucket so equally-eligible
        # targets are distributed fairly.
        return self.rng.choice(pool)

    def _pick_enemy_target(self):
        living_party = self._living(self.party)
        if not living_party:
            return None
        return self.rng.choice(living_party)

    # ------------------------------------------------------------------
    # Turn execution
    # ------------------------------------------------------------------
    def _take_turn(self, attacker: Combatant):
        if not attacker.alive:
            return
        if attacker.num_attacks <= 0 or attacker.damage_per_attack <= 0:
            self.log.append(f"    {attacker.name} has no attacks to make.")
            return

        for atk_idx in range(1, attacker.num_attacks + 1):
            if attacker.side == "party":
                target = self._pick_player_target()
            else:
                target = self._pick_enemy_target()

            if target is None:
                return

            label = f" [{attacker.label}]" if attacker.label else ""

            # Enemy attacks: roll to hit against player AC
            if attacker.side == "enemy":
                roll = self.rng.randint(1, 20)
                total_to_hit = roll + attacker.to_hit

                if roll == 1:
                    self.log.append(
                        f"    {attacker.name}{label} attack {atk_idx}/{attacker.num_attacks} "
                        f"targeting {target.name} → rolls 1 + {attacker.to_hit} = {total_to_hit} vs AC {target.ac}: MISS"
                    )
                    continue

                if roll == 20 or total_to_hit >= target.ac:
                    dmg = attacker.damage_per_attack
                    target.take_damage(dmg)
                    self.log.append(
                        f"    {attacker.name}{label} attack {atk_idx}/{attacker.num_attacks} "
                        f"targeting {target.name} → rolls {roll} + {attacker.to_hit} = {total_to_hit} vs AC {target.ac}: HIT "
                        f"for {dmg:.2f} (HP {target.hp:.1f}/{target.max_hp})"
                    )
                    if not target.alive:
                        self.log.append(f"      ✗ {target.name} is down.")
                else:
                    self.log.append(
                        f"    {attacker.name}{label} attack {atk_idx}/{attacker.num_attacks} "
                        f"targeting {target.name} → rolls {roll} + {attacker.to_hit} = {total_to_hit} vs AC {target.ac}: MISS"
                    )

            # Party attacks: keep deterministic expected damage
            else:
                dmg = attacker.damage_per_attack
                target.take_damage(dmg)
                self.log.append(
                    f"    {attacker.name}{label} attack {atk_idx}/{attacker.num_attacks} "
                    f"targeting {target.name} → takes {dmg:.2f} "
                    f"(HP {target.hp:.1f}/{target.max_hp})"
                )
                if not target.alive:
                    self.log.append(f"      ✗ {target.name} is down.")

    def _sides_alive(self):
        return bool(self._living(self.party)) and bool(self._living(self.enemies))

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------
    def run(self):
        """Run the encounter and return a result dict (see class docstring)."""
        self.log.append("=== Initiative ===")
        order = self.roll_initiative()

        self.log.append("\n=== Turn order ===")
        for c in order:
            self.log.append(
                f"  {c.initiative:>3}  {c.name} ({c.side}, "
                f"HP={c.hp}, AC={c.ac}, atks={c.num_attacks}, "
                f"dpa={c.damage_per_attack:.2f})"
            )

        # Step through rounds.
        while self._sides_alive() and self.round_no < self.MAX_ROUNDS:
            self.round_no += 1
            self.log.append(f"\n=== Round {self.round_no} ===")
            for combatant in order:
                if not self._sides_alive():
                    break
                self._take_turn(combatant)

        # Determine winner.
        party_alive = bool(self._living(self.party))
        enemies_alive = bool(self._living(self.enemies))
        if party_alive and not enemies_alive:
            winner = "party"
        elif enemies_alive and not party_alive:
            winner = "enemies"
        else:
            winner = "draw"  # both sides alive at MAX_ROUNDS, or both wiped

        self.log.append(f"\n=== Outcome after {self.round_no} round(s): {winner.upper()} ===")
        for c in self.party:
            self.log.append(
                f"  Party  {c.name}: HP {c.hp:.1f}/{c.max_hp}"
                + ("  (DOWN)" if not c.alive else "")
            )
        for c in self.enemies:
            self.log.append(
                f"  Enemy  {c.name} ({c.role}): HP {c.hp:.1f}/{c.max_hp}"
                + ("  (DOWN)" if not c.alive else "")
            )

        return {
            "winner": winner,
            "rounds": self.round_no,
            "log": self.log,
            "party_survivors": [c.name for c in self.party if c.alive],
            "enemy_survivors": [c.name for c in self.enemies if c.alive],
        }
