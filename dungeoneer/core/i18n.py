"""Minimal localisation module.

Usage::

    from dungeoneer.core.i18n import t, set_language
    set_language("cs")          # switch at runtime (e.g. from main menu)
    label = t("help.title")     # returns localised string

Supported languages: "en" (default), "cs", "es".
Unknown keys fall back to the key name itself so nothing silently breaks.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Active language — change via set_language()
# ---------------------------------------------------------------------------

_lang: str = "en"


def set_language(lang: str) -> None:
    """Switch the active language.  Silently ignored if lang is unknown."""
    global _lang
    if lang in _STRINGS:
        _lang = lang


def get_language() -> str:
    return _lang


def t(key: str) -> str:
    """Return the localised string for *key* in the active language.

    Falls back to English, then to the raw key if nothing is found.
    """
    return (
        _STRINGS.get(_lang, {}).get(key)
        or _STRINGS["en"].get(key)
        or key
    )


# ---------------------------------------------------------------------------
# String tables
# ---------------------------------------------------------------------------

_STRINGS: dict[str, dict[str, str]] = {
    "en": {
        # --- Main menu ---
        "menu.title":                   "DUNGEONEER",
        "menu.subtitle":                "Between Runs",
        "menu.difficulty":              "DIFFICULTY",
        "menu.easy":                    "Easy",
        "menu.normal":                  "Normal",
        "menu.hard":                    "Hard",
        "menu.loot_mode":               "LOOT MODE",
        "menu.loot.minigame":           "Hack Minigame",
        "menu.loot.random":             "Random Loot",
        "menu.language":                "LANGUAGE",
        "menu.start":                   "Start Run",
        "menu.quit":                    "Quit",
        "menu.aim_minigame":            "AIM MINIGAME",
        "menu.aim_minigame_on":         "ON",
        "menu.aim_minigame_off":        "OFF",
        "menu.hints":                   "[Enter] Start   [F1] Help   [Esc] Quit",

        # --- Game over ---
        "gameover.victory":             "EXTRACTION COMPLETE",
        "gameover.defeat":              "KILLED IN ACTION",
        "gameover.victory_sub":         "You made it out alive.",
        "gameover.defeat_sub":          "Your signal has gone dark.",
        "gameover.floors":              "Floors cleared: {n}",
        "gameover.credits":             "Credits earned: \u00a5 {n}",
        "gameover.menu":                "Main Menu  [R]",
        "gameover.quit":                "Quit  [Esc]",

        # --- Help screen ---
        "help.title":                   "HELP",
        "help.footer":                  "[F1 / Esc / Enter]  Close",

        "help.section.movement":        "MOVEMENT & ACTIONS",
        "help.section.combat":          "COMBAT",
        "help.section.items":           "ITEMS",
        "help.section.general":         "GENERAL",

        "help.key.wasd":                "WASD / Arrows",
        "help.desc.wasd":               "Move — or attack adjacent enemy",
        "help.key.wait":                "Space / .",
        "help.desc.wait":               "Wait (skip turn)",
        "help.key.interact":            "E",
        "help.desc.interact":           "Stairs down / open container",

        "help.key.shoot":               "F",
        "help.desc.shoot":              "Attack nearest enemy (melee or ranged)",
        "help.key.target":              "Tab",
        "help.desc.target":             "Cycle aim target through visible enemies",
        "help.key.aim":                 "F / click",
        "help.desc.aim":                "Stop needle in zone — centre = max damage / crit. Outside = miss.",
        "help.key.reload":              "R",
        "help.desc.reload":             "Reload weapon",

        # --- Aim minigame ---
        "aim.title":                    "TARGETING",
        "aim.press_f":                  "F / click to fire",
        "aim.shot_n":                   "Shot {n}/{total}",
        "aim.miss":                     "MISS",
        "aim.hit":                      "HIT",
        "aim.crit":                     "CRITICAL",

        # --- Aim help overlay (F1) ---
        "aim.help.hint":                "[F1] help",
        "aim.help.title":               "// TARGETING \u2014 HELP //",
        "aim.help.mechanic":            "HOW AIMING WORKS",
        "aim.help.mech.1":              "Needle sweeps back and forth on the arc",
        "aim.help.mech.2":              "Press F or click to stop the needle",
        "aim.help.mech.3":              "Green zone = hit;  outside = miss",
        "aim.help.mech.4":              "Centre of zone = max damage",
        "aim.help.mech.5":              "Needle speeds up after each bounce",
        "aim.help.mech.zone":           "Zone shrinks the farther the target",
        "aim.help.armor":               "ARMOR",
        "aim.help.armor.1":             "Equipped armor absorbs 1 damage per hit",
        "aim.help.armor.2":             "Auto-equipped on pickup; only stronger replaces",
        "aim.help.crit":                "CRITICAL HITS",
        "aim.help.crit.1":              "Stop needle at \u226595% accuracy for CRITICAL",
        "aim.help.crit.2":              "Critical = max weapon damage (unlocks as you progress)",
        "aim.help.controls":            "CONTROLS",
        "aim.help.ctrl.f.key":          "F / click",
        "aim.help.ctrl.f.desc":         "stop needle / fire",
        "aim.help.ctrl.tab.key":        "Tab",
        "aim.help.ctrl.tab.desc":       "cycle target",
        "aim.help.ctrl.esc.key":        "Esc",
        "aim.help.ctrl.esc.desc":       "cancel \u2014 remaining shots miss",
        "aim.help.ctrl.f1.key":         "F1",
        "aim.help.ctrl.f1.desc":        "toggle this help",
        "aim.help.close":               "[F1]  Close help",

        "help.key.heal":                "H",
        "help.desc.heal":               "Quick heal (best available item)",
        "help.key.inventory":           "I",
        "help.desc.inventory":          "Inventory",
        "help.key.swap":                "C",
        "help.desc.swap":               "Swap weapon",

        "help.key.help":                "F1",
        "help.desc.help":               "This help screen",
        "help.key.escape":              "Esc",
        "help.desc.escape":             "Close menu / Quit",

        # --- Cheat / debug menu (F11) ---
        "cheat.title":                  "CHEAT MENU  [F11]",
        "cheat.section.items":          "Items",
        "cheat.section.enemies":        "Enemies",
        "cheat.section.container":      "Container",
        "cheat.section.player":         "Player",
        "cheat.item.ammo_9mm":          "9mm Ammo  ×10",
        "cheat.item.ammo_rifle":        "Rifle Ammo  ×6",
        "cheat.item.ammo_shell":        "Shotgun Ammo  ×8",
        "cheat.spawn_chest":            "Spawn Chest",
        "cheat.hp.full":                "Set HP → full",
        "cheat.hp.set1":                "Set HP → 1",
        "cheat.hp.plus10":              "Heal  +10 HP",
        "cheat.hp.plus20":              "Heal  +20 HP",
        "cheat.credits.plus100":        "+100 Credits",
        "cheat.hint":                   "[↑↓] Navigate   [Enter] Use   [Esc] Close",

        # --- Quit confirm dialog (in-game) ---
        "quit_confirm.title":           "ABORT RUN",
        "quit_confirm.question":        "Return to main menu?",
        "quit_confirm.confirm":         "[Y / Enter]  Yes",
        "quit_confirm.cancel":          "[N / Esc]   No",

        # --- Overheal confirm dialog ---
        "overheal_confirm.title":       "OVERHEAL WARNING",
        "overheal_confirm.question":    "Healing may exceed max HP — use anyway?",
        "overheal_confirm.confirm":     "[H / Y / Enter]  Use it",
        "overheal_confirm.cancel":      "[N / Esc]        Cancel",

        # --- Exit confirm dialog (main menu) ---
        "exit_confirm.title":           "EXIT GAME",
        "exit_confirm.question":        "Quit the game?",
        "exit_confirm.confirm":         "[Y / Enter]  Yes",
        "exit_confirm.cancel":          "[N / Esc]   No",

        # --- Items ---
        "item.pistol.name":             "Pistol",
        "item.pistol.desc":             "Standard 9mm sidearm. Reliable backup.",
        "item.combat_knife.name":       "Combat Knife",
        "item.combat_knife.desc":       "Lightweight blade. Fast and silent.",
        "item.shotgun.name":            "Shotgun",
        "item.shotgun.desc":            "Devastating up close. Useless at range. 4 shells.",
        "item.smg.name":                "SMG",
        "item.smg.desc":                "Burst fire \u2014 3 rounds per shot. Shreds at close range.",
        "item.energy_sword.name":       "Energy Sword",
        "item.energy_sword.desc":       "Military-grade energy blade. Cuts through armour.",
        "item.rifle.name":              "Rifle",
        "item.rifle.desc":              "Long-range precision. Lower burst than shotgun. 6 rounds.",
        "item.stim_pack.name":          "Stim Pack",
        "item.stim_pack.desc":          "Combat stimulant. Restores 10 HP.",
        "item.medkit.name":             "Med Kit",
        "item.medkit.desc":             "Full trauma kit. Restores 20 HP.",
        "item.ammo_9mm.name":           "9mm Ammo \u00d7{n}",
        "item.ammo_9mm.desc":           "{n} rounds of 9mm ammunition.",
        "item.ammo_rifle.name":         "Rifle Ammo \u00d7{n}",
        "item.ammo_rifle.desc":         "{n} high-calibre rifle rounds.",
        "item.ammo_shell.name":         "Shells \u00d7{n}",
        "item.ammo_shell.desc":         "{n} shotgun shells.",
        "item.basic_armor.name":        "Basic Armor",
        "item.basic_armor.desc":        "A lightweight tactical vest. Absorbs some incoming damage.",

        # --- Entities ---
        "entity.player.name":           "Diver",
        "entity.guard.name":            "Corp Guard",
        "entity.drone.name":            "Sec Drone",
        "entity.crate.name":            "Crate",
        "entity.corp_vault.name":       "Corp Vault",

        # --- HUD ---
        "hud.floor":                    "FLOOR {n}",
        "hud.full_hp":                  "[H] Full HP",
        "hud.no_heal":                  "[H] --",
        "hud.armor_label":              "[ARMOR]",
        "hud.armor_none":               "\u2014",

        # --- Inventory UI ---
        "inv.title":                    "INVENTORY  {n}/8",
        "inv.weapon_label":             "WEAPON:",
        "inv.armor_label":              "ARMOR:",
        "inv.none":                     "\u2014 none \u2014",
        "inv.empty":                    "(empty)",
        "inv.btn_use":                  "[E] Use",
        "inv.btn_close":                "[I] Close",

        # --- Weapon picker ---
        "weapon_picker.title":          "SWAP WEAPON",
        "weapon_picker.empty":          "(no weapons in inventory)",
        "weapon_picker.close":          "[C/Esc] Close",
        "weapon_picker.hint":           "  [\u2191\u2193] Navigate   [E/Enter] Equip",

        # --- Game log messages ---
        "log.floor_enter":              "Floor {n} \u2014 infiltrating facility.",
        "log.heal_cancel":              "Heal cancelled.",
        "log.no_exit":                  "Nothing to interact with here.",
        "hint.stair_descend":           "[E] Descend deeper",
        "log.no_heals":                 "No healing items.",
        "log.full_hp":                  "Already at full health.",
        "log.reload_full":              "Magazine is full.",
        "log.reload_no_reserves":       "No ammo reserves to reload with.",
        "log.container_already_open":   "Already looted.",
        "log.heal_confirm":             "{item}{count}: +{hp} HP (overheal +{overheal}).  [H/Enter] Confirm",
        "log.hack_success":             "Hacked {container}.{credits}",
        "log.hack_fail":                "Hack failed \u2014 security drone dispatched!",
        "log.no_ranged":                "No ranged weapon equipped.",
        "log.no_target":                "No target in sight.",
        "log.no_melee":                 "No enemy in melee range.",

        # --- Action resolver log messages ---
        "log.pickup_ammo":              "Picked up {item}.",
        "log.armor_duplicate":          "Already wearing {item}, left it.",
        "log.armor_equip":              "Equipped {item}  -{bonus} dmg.",
        "log.item_duplicate":           "Already have {item}, left it.",
        "log.ammo_strip":               "Stripped {item}: +{n} {ammo}.",
        "log.pickup_item":              "Picked up {item}{count}.",
        "log.inv_full":                 "Inventory full \u2014 can't pick up item.",

        # --- Combat messages ---
        "log.melee_hit":                "{attacker} hits {target} for {dmg} dmg.{crit}",
        "log.ranged_hit":               "{attacker} shoots {target}{burst} for {dmg} dmg.{crit}",
        "log.ranged_miss":              "{attacker} fires at {target} — miss!",
        "log.is_down":                  " {name} is down!",
        "log.crit":                     " CRITICAL!",
        "log.no_ammo":                  "Out of ammo! Press R to reload.",

        # --- Container messages ---
        "log.container_secured":        "Data Core secured!{credits} \u2014 EXTRACTING.",
        "log.container_empty":          "The {name} is empty.{credits}",
        "log.container_open":           "Opened {name}: {items}.{credits}",

        # --- Inventory / equipment actions ---
        "log.descend":                  "You descend to the next level.",
        "log.reloaded":                 "Reloaded {item}.",
        "log.equipped":                 "Equipped {item}.",
        "log.dropped":                  "Dropped {item}.",
        "log.credits_drop":             "+\u00a5{n}",

        # --- Consumable use ---
        "log.heal_restored":            "Restored {n} HP.",
        "log.item_used":                "Used {name}. ",

        # --- Hack minigame status ---
        "hack.status.initial":          "Analyse the network, then move to begin.",
        "hack.status.navigate":         "Navigate to loot nodes and hack them.",
        "hack.status.routing":          "Routing to NODE-{n}\u2026",
        "hack.status.extracting":       "Extracting {kind}\u2026",
        "hack.status.cancelled":        "Hack cancelled.",
        "hack.status.time_penalty":     "ICE TRIGGERED \u2014 Time penalty  -3s!",
        "hack.status.cache_destroyed":  "ICE TRIGGERED \u2014 Data cache destroyed!",
        "hack.status.no_targets":       "ICE TRIGGERED \u2014 No targets.",
        "hack.status.access_denied":    "ICE TRIGGERED \u2014 Access denied!",
        "hack.status.bonus_time":       "Bonus time  +3s",
        "hack.status.credits":          "Credits extracted  +\u00a5{n}",
        "hack.status.extracted":        "Extracted: {item}",

        # --- Hack overlay ---
        "hack.overlay.time_title":      "TIME PENALTY",
        "hack.overlay.time_sub":        "\u22123 SECONDS",
        "hack.overlay.cache_title":     "DATA CORRUPTED",
        "hack.overlay.cache_sub":       "CACHE NODE DESTROYED",
        "hack.overlay.notgt_title":     "ICE TRIGGERED",
        "hack.overlay.notgt_sub":       "NO TARGETS",
        "hack.overlay.denied_title":    "ACCESS DENIED",
        "hack.overlay.denied_sub":      "NODE BLOCKED \u2014 REROUTED",
        "hack.overlay.bonus_title":     "BONUS TIME",
        "hack.overlay.bonus_sub":       "+3 SECONDS",
        "hack.overlay.credits_title":   "CREDITS EXTRACTED",
        "hack.overlay.data_title":      "DATA EXTRACTED",

        # --- Hack result ---
        "hack.result.success":          "//  HACK COMPLETE  //",
        "hack.result.fail":             "//  TRACE COMPLETE \u2014 ALARM  //",
        "hack.result.no_data":          "No data extracted.",
        "hack.result.drone":            "Security drone dispatched!",

        # --- Hack header + node label ---
        "hack.header.title":            "INTRUSION PROTOCOL",
        "hack.header.esc_cancel":       "[Q]  CANCEL EXTRACTION",
        "hack.header.move_start":       "\u2014 MOVE TO START TIMER \u2014",
        "hack.header.esc_abort":        "[Q]  ABORT HACK",
        "hack.footer.hint":             "W A S D / Arrows  +  Mouse  |  [Q] Quit  [F1] Help",
        "hack.footer.counter":          "DATA: {n}/{total}",
        "hack.node.corrupt":            "CORRUPT",

        # --- Hack loot kind labels ---
        "hack.loot.ammo":               "Ammo",
        "hack.loot.rifle_ammo":         "Rifle Ammo",
        "hack.loot.shotgun_ammo":       "Shotgun Ammo",
        "hack.loot.heal":               "Med",
        "hack.loot.medkit":             "Medkit",
        "hack.loot.weapon":             "Weapon",
        "hack.loot.credits":            "Credits",
        "hack.loot.bonus_time":         "Bonus Time",
        "hack.loot.armor":              "Armor",
        "hack.loot.mystery":            "Unknown",

        # --- Hack help overlay ---
        "hack.help.title":              "// INTRUSION PROTOCOL \u2014 HELP //",
        "hack.help.node_types":         "NODE TYPES",
        "hack.help.node.entry.lbl":     "\u25ba  ENTRY     ",
        "hack.help.node.entry.desc":    "your starting position",
        "hack.help.node.cache.lbl":     "\u25aa  DATA CACHE",
        "hack.help.node.cache.desc":    "hack to extract loot",
        "hack.help.node.empty.lbl":     "\u25aa  EMPTY     ",
        "hack.help.node.empty.desc":    "traversal only",
        "hack.help.node.ice.lbl":       "\u25aa  ICE       ",
        "hack.help.node.ice.desc":      "hidden trap \u2014 looks like EMPTY!",
        "hack.help.ice_section":        "ICE EFFECTS  (triggered on entry)",
        "hack.help.ice.time.lbl":       "TIME PENALTY",
        "hack.help.ice.time.desc":      "\u22123 seconds removed from the clock",
        "hack.help.ice.corrupt.lbl":    "DATA CORRUPTED",
        "hack.help.ice.corrupt.desc":   "destroys a random unhacked loot node",
        "hack.help.ice.blocked.lbl":    "ACCESS DENIED",
        "hack.help.ice.blocked.desc":   "blocks entry \u2014 bounces you back",
        "hack.help.timer":              "TIMER",
        "hack.help.timer.1":            "Starts on your first move",
        "hack.help.timer.2":            "Bar at top: green \u2192 orange \u2192 red",
        "hack.help.timer.3":            "BONUS TIME node: +3 seconds",
        "hack.help.timer.4":            "Collect all data caches to finish early",
        "hack.help.controls":           "CONTROLS",
        "hack.help.ctrl.wasd.key":      "W / A / S / D",
        "hack.help.ctrl.wasd.desc":     "move to adjacent node",
        "hack.help.ctrl.arrows.key":    "Arrow keys",
        "hack.help.ctrl.arrows.desc":   "same as W A S D",
        "hack.help.ctrl.mouse.key":     "Mouse click",
        "hack.help.ctrl.mouse.desc":    "click a neighbour to move",
        "hack.help.ctrl.esc.key":       "Q  /  Esc",
        "hack.help.ctrl.esc.desc":      "cancel extraction / abort hack",
        "hack.help.ctrl.f1.key":        "F1",
        "hack.help.ctrl.f1.desc":       "toggle this help (timer paused)",
        "hack.help.close":              "[F1]  Close help",
        "hack.help.grid_section":       "GRID",
        "hack.help.grid.automove":      "Auto-move: press a direction",
        "hack.help.grid.stop":          "Stops at node or direction change",
        "hack.help.grid.lit":           "Lit paths = reachable nodes",

        # --- HUD hint ---
        "hud.help_hint":                "[F1] Help",

        # --- Settings overlay ---
        "settings.title":               "SETTINGS",
        "settings.section.difficulty":  "DIFFICULTY",
        "settings.section.gameplay":    "GAMEPLAY",
        "settings.section.audio":       "AUDIO",
        "settings.section.language":    "LANGUAGE",
        "settings.gameplay.loot":       "Loot",
        "settings.gameplay.aim":        "Aim",
        "settings.gameplay.heal":       "Healing",
        "settings.gameplay.heal_threshold": "Quickheal",
        "settings.gameplay.heal_threshold_suffix": "threshold",
        "menu.heal.thr.80":             "New to minigame",
        "menu.heal.thr.90":             "Learning",
        "menu.heal.thr.100":            "Default",
        "menu.heal.thr.110":            "Experienced",
        "menu.heal.thr.120":            "Skilled",
        "settings.audio.master":        "Master",
        "settings.audio.music":         "Music",
        "settings.audio.sfx":           "Effects",
        "settings.footer":              "[Esc]  Close",

        # --- Help catalog ---
        "help_catalog.title":           "HELP & CONTROLS",
        "help_catalog.tab.exploration": "EXPLORATION",
        "help_catalog.tab.combat":      "COMBAT",
        "help_catalog.tab.shooting":    "SHOOTING",
        "help_catalog.tab.aiming":      "AIMING",
        "help_catalog.tab.hacking":     "HACKING",
        "help_catalog.tab.healing":     "HEALING",
        "help_catalog.footer":          "[\u25c4 \u25ba] Switch tab   [Esc] Close",

        # Exploration tab
        "help_catalog.expl.h1":         "MOVEMENT",
        "help_catalog.expl.1.1":        "WASD / Arrow keys \u2014 move one tile; attacks adjacent enemy",
        "help_catalog.expl.1.2":        "Each step uses one turn \u2014 enemies react",
        "help_catalog.expl.1.3":        "Space or . \u2014 wait (skip your turn)",
        "help_catalog.expl.h2":         "FIELD OF VIEW",
        "help_catalog.expl.2.1":        "Sight radius: 10 tiles from your position",
        "help_catalog.expl.2.2":        "Explored areas visible in dark \u2014 enemies not tracked",
        "help_catalog.expl.h3":         "STAIRS & CONTAINERS",
        "help_catalog.expl.3.1":        "E \u2014 descend stairs or open a container",
        "help_catalog.expl.3.2":        "Containers may hold items, weapons, or credits",
        "help_catalog.expl.3.3":        "All containers trigger the hack minigame for bonus loot (if enabled)",

        # Combat tab
        "help_catalog.comb.h1":         "MELEE COMBAT",
        "help_catalog.comb.1.1":        "Move into an enemy to melee attack (bumping)",
        "help_catalog.comb.1.2":        "Diagonal movement and attacks are allowed",
        "help_catalog.comb.1.3":        "F \u2014 attack nearest enemy in melee range",
        "help_catalog.comb.h2":         "ARMOR",
        "help_catalog.comb.2.1":        "Armor reduces incoming damage by its defense value",
        "help_catalog.comb.2.2":        "Auto-equipped on pickup; stronger armor replaces weaker",
        "help_catalog.comb.2.3":        "View equipped armor in inventory (I key)",
        "help_catalog.comb.h3":         "ENEMIES",
        "help_catalog.comb.3.1":        "Corp Guards: melee attackers, patrol corridors, chase on sight",
        "help_catalog.comb.3.2":        "Sec Drones: ranged, prefer distance, dispatched by failed hacks",
        "help_catalog.comb.3.3":        "Enemies only react within line of sight",

        # Shooting tab
        "help_catalog.shoot.h1":        "RANGED COMBAT",
        "help_catalog.shoot.1.1":       "F \u2014 aim and fire at selected target",
        "help_catalog.shoot.1.2":       "Tab \u2014 cycle through visible enemies",
        "help_catalog.shoot.1.3":       "R \u2014 reload weapon",
        "help_catalog.shoot.1.4":       "C \u2014 swap equipped weapon",
        "help_catalog.shoot.h2":        "AMMO",
        "help_catalog.shoot.2.1":       "9mm \u2014 Pistol and SMG",
        "help_catalog.shoot.2.2":       "Rifle Ammo \u2014 Rifle",
        "help_catalog.shoot.2.3":       "Shells \u2014 Shotgun",
        "help_catalog.shoot.2.4":       "Ammo auto-picked up from enemies and containers",
        "help_catalog.shoot.h3":        "WEAPONS",
        "help_catalog.shoot.3.1":       "Pistol \u2014 reliable sidearm, medium range",
        "help_catalog.shoot.3.2":       "SMG \u2014 3-round burst, deadly up close",
        "help_catalog.shoot.3.3":       "Shotgun \u2014 devastating close range, 4 shells",
        "help_catalog.shoot.3.4":       "Rifle \u2014 long range, precision shots",
        "help_catalog.shoot.3.5":       "Energy Sword \u2014 melee only, cuts through armor",
        "help_catalog.shoot.3.6":       "Combat Knife \u2014 melee only, fast close-range attack",

        # Aiming tab
        "help_catalog.aim.h1":          "HOW AIMING WORKS",
        "help_catalog.aim.1.1":         "A needle sweeps back and forth on a curved arc",
        "help_catalog.aim.1.2":         "Press F or click to stop the needle and fire",
        "help_catalog.aim.1.3":         "Green zone = hit;  outside the zone = miss",
        "help_catalog.aim.1.4":         "Stopping near the centre = maximum damage",
        "help_catalog.aim.1.5":         "Needle speeds up after each bounce from arc end",
        "help_catalog.aim.h2":          "ACCURACY & CRITICAL HITS",
        "help_catalog.aim.2.1":         "Zone shrinks the farther the target",
        "help_catalog.aim.2.2":         "Stop needle at \u226595% accuracy for a CRITICAL HIT",
        "help_catalog.aim.2.3":         "Critical = max weapon damage \u2014 effect unlocks as you progress",
        "help_catalog.aim.h3":          "CONTROLS",
        "help_catalog.aim.3.1":         "F / click \u2014 stop needle and fire",
        "help_catalog.aim.3.2":         "Tab \u2014 cycle target before firing",
        "help_catalog.aim.3.3":         "Esc \u2014 cancel; remaining shots miss automatically",

        # Exploration illustration labels
        "help_catalog.expl.icon.container": "Container",
        "help_catalog.expl.icon.ammo":      "Ammo",
        "help_catalog.expl.icon.stairs":    "Stairs",
        "help_catalog.expl.icon.vault":     "Vault",

        # Hack node illustration labels
        "help_catalog.hack.node.entry":     "ENTRY",
        "help_catalog.hack.node.cache":     "DATA CACHE",
        "help_catalog.hack.node.empty":     "EMPTY",
        "help_catalog.hack.node.ice":       "ICE (hidden)",
        "help_catalog.hack.loot_label":     "Loot examples:",

        # Hacking tab
        "help_catalog.hack.h1":         "HACKING BASICS",
        "help_catalog.hack.1.1":        "Move to DATA CACHE nodes and enter them to extract loot",
        "help_catalog.hack.1.2":        "Timer starts on your first move",
        "help_catalog.hack.1.3":        "Collect all caches or wait for timer to finish the hack",
        "help_catalog.hack.h2":         "NODE TYPES",
        "help_catalog.hack.2.1":        "\u25ba ENTRY \u2014 your starting position",
        "help_catalog.hack.2.2":        "\u25aa DATA CACHE \u2014 hack to extract loot",
        "help_catalog.hack.2.3":        "\u25aa EMPTY \u2014 traversal only",
        "help_catalog.hack.2.4":        "\u25aa ICE \u2014 hidden trap, looks like EMPTY!",
        "help_catalog.hack.h3":         "ICE EFFECTS",
        "help_catalog.hack.3.1":        "TIME PENALTY \u2014 \u22123 seconds removed from timer",
        "help_catalog.hack.3.2":        "DATA CORRUPTED \u2014 destroys a random unhacked loot node",
        "help_catalog.hack.3.3":        "ACCESS DENIED \u2014 bounces you back, blocks entry",
        "help_catalog.hack.h4":         "CONTROLS",
        "help_catalog.hack.4.1":        "WASD / Arrows \u2014 move to adjacent node",
        "help_catalog.hack.4.2":        "Mouse click \u2014 click a neighbour to move",
        "help_catalog.hack.4.3":        "Q / Esc \u2014 cancel extraction / abort hack",

        # Healing tab
        "heal.help.h1":                 "HOW HEALING WORKS",
        "heal.help.1":                  "Watch two heartbeats \u2014 du-dum, du-dum",
        "heal.help.2":                  "Press H on the third beat, hold through the gap",
        "heal.help.3":                  "Release H when the second thump should sound",
        "heal.help.4":                  "Perfect timing \u2192 +20%   Miss \u2192 \u221220%",
        "heal.help.h2":                 "SCORING",
        "heal.help.s1":                 "Perfect +20%  |  Great +10%  |  Good \u00b10%",
        "heal.help.s2":                 "Poor \u221210%  |  Miss \u221220%",
        "heal.help.s3":                 "Score = sum of press + release timing error",
        "heal.help.h3":                 "CONTROLS",
        "heal.help.key1":               "[H hold] \u2014 press on beat (contraction)",
        "heal.help.key2":               "[H release] \u2014 release after gap (relaxation)",
        "heal.help.key3":               "[Esc] \u2014 cancel heal",
        "heal.help.key4":               "[F1] \u2014 toggle this help",

        # Heal overlay runtime strings
        "heal.overlay.title":           "Cardiac Rhythm",
        "heal.overlay.watch":           "Watch...",
        "heal.overlay.now":             "NOW!",
        "heal.overlay.hint":            "[H] press & hold on the 3rd beat",
        "heal.overlay.perfect":         "Perfect!",
        "heal.overlay.great":           "Great",
        "heal.overlay.good":            "Good",
        "heal.overlay.poor":            "Weak",
        "heal.overlay.miss":            "Poor",
    },

    "cs": {
        # --- Main menu ---
        "menu.title":                   "DUNGEONEER",
        "menu.subtitle":                "Mezi b\u011bhy",
        "menu.difficulty":              "OBT\u00cd\u017dNOST",
        "menu.easy":                    "Lehk\u00fd",
        "menu.normal":                  "Norm\u00e1ln\u00ed",
        "menu.hard":                    "T\u011bžk\u00fd",
        "menu.loot_mode":               "ZP\u016aSO\u0042 LOOTU",
        "menu.loot.minigame":           "Hackov\u00e1n\u00ed",
        "menu.loot.random":             "N\u00e1hodn\u00fd loot",
        "menu.language":                "JAZYK",
        "menu.start":                   "Spustit b\u011bh",
        "menu.quit":                    "Ukon\u010dit",
        "menu.aim_minigame":            "M\u00cd\u0158EN\u00cd",
        "menu.aim_minigame_on":         "ZAP",
        "menu.aim_minigame_off":        "VYP",
        "menu.hints":                   "[Enter] Spustit   [F1] N\u00e1pov\u011bda   [Esc] Ukon\u010dit",

        # --- Game over ---
        "gameover.victory":             "EXTRAKCE DOKON\u010cENA",
        "gameover.defeat":              "VY\u0158AZEN Z BOJE",
        "gameover.victory_sub":         "Dostal ses ven \u017eiv\u00fd.",
        "gameover.defeat_sub":          "Tv\u016fj sign\u00e1l zmizel.",
        "gameover.floors":              "Patra prob\u00e1d\u00e1na: {n}",
        "gameover.credits":             "Z\u00edskan\u00e9 kredity: \u00a5 {n}",
        "gameover.menu":                "Hlavn\u00ed menu  [R]",
        "gameover.quit":                "Ukon\u010dit  [Esc]",

        # --- Help screen ---
        "help.title":                   "N\u00c1POV\u011aDA",
        "help.footer":                  "[F1 / Esc / Enter]  Zav\u0159\u00edt",

        "help.section.movement":        "POHYB & AKCE",
        "help.section.combat":          "BOJ",
        "help.section.items":           "P\u0158EDMĚTY",
        "help.section.general":         "OBECN\u00c9",

        "help.key.wasd":                "WASD / \u0160ipky",
        "help.desc.wasd":               "Pohyb \u2014 nebo \u00fatok na sousedn\u00edho nep\u0159\u00edtele",
        "help.key.wait":                "Space / .",
        "help.desc.wait":               "\u010cek\u00e1n\u00ed (p\u0159esko\u010den\u00ed tahu)",
        "help.key.interact":            "E",
        "help.desc.interact":           "Schody dol\u016f / otev\u0159\u00edt kontejner",

        "help.key.shoot":               "F",
        "help.desc.shoot":              "\u00datok na nejbli\u017e\u0161\u00edho nep\u0159\u00edtele (melee nebo na d\u00e1lku)",
        "help.key.target":              "Tab",
        "help.desc.target":             "P\u0159epni c\u00edl m\u00ed\u0159en\u00ed mezi viditeln\u00fdmi nep\u0159\u00e1teli",
        "help.key.aim":                 "F / klik",
        "help.desc.aim":                "Zastav ru\u010di\u010dku v z\u00f3n\u011b \u2014 st\u0159ed = max damage / krit. Vn\u011b = minul.",
        "help.key.reload":              "R",
        "help.desc.reload":             "P\u0159ebit\u00ed zbran\u011b",

        # --- Aim minigame ---
        "aim.title":                    "M\u00cd\u0158EN\u00cd",
        "aim.press_f":                  "F / klik pro v\u00fdst\u0159el",
        "aim.shot_n":                   "V\u00fdst\u0159el {n}/{total}",
        "aim.miss":                     "MINUL",
        "aim.hit":                      "Z\u00c1SAH",
        "aim.crit":                     "KRITICK\u00dd Z\u00c1SAH",

        # --- Aim help overlay (F1) ---
        "aim.help.hint":                "[F1] n\u00e1pov\u011bda",
        "aim.help.title":               "// M\u00cd\u0158EN\u00cd \u2014 N\u00c1POV\u011aDA //",
        "aim.help.mechanic":            "JAK FUNGUJE M\u00cd\u0158EN\u00cd",
        "aim.help.mech.1":              "Ru\u010di\u010dka kmit\u00e1 tam a zp\u011bt po oblouku",
        "aim.help.mech.2":              "Stiskni F nebo klikni a zastav ji",
        "aim.help.mech.3":              "Zelen\u00e1 z\u00f3na = z\u00e1sah;  mimo = minul",
        "aim.help.mech.4":              "St\u0159ed z\u00f3ny = maxim\u00e1ln\u00ed po\u0161kozen\u00ed",
        "aim.help.mech.5":              "Ru\u010di\u010dka se po ka\u017ed\u00e9m odrazu zrychl\u00ed",
        "aim.help.mech.zone":           "Z\u00f3na se zmen\u0161uje se vzd\u00e1lenost\u00ed c\u00edle",
        "aim.help.armor":               "ZBROJ",
        "aim.help.armor.1":             "Vybaven\u00e1 zbroj absorbuje 1 po\u0161kozen\u00ed za z\u00e1sah",
        "aim.help.armor.2":             "Auto-vybav\u00ed p\u0159i sb\u011bru; nahrad\u00ed jen siln\u011bj\u0161\u00ed",
        "aim.help.crit":                "KRITICK\u00c9 Z\u00c1SAHY",
        "aim.help.crit.1":              "Zastav ru\u010di\u010dku na \u226595\u00a0% pro KRITICK\u00dd Z\u00c1SAH",
        "aim.help.crit.2":              "Kritick\u00fd = maxim\u00e1ln\u00ed po\u0161kozen\u00ed zbran\u011b (odemyk\u00e1 se b\u011bhem hry)",
        "aim.help.controls":            "OVL\u00c1D\u00c1N\u00cd",
        "aim.help.ctrl.f.key":          "F / klik",
        "aim.help.ctrl.f.desc":         "zastav ru\u010di\u010dku / v\u00fdst\u0159el",
        "aim.help.ctrl.tab.key":        "Tab",
        "aim.help.ctrl.tab.desc":       "p\u0159epni c\u00edl",
        "aim.help.ctrl.esc.key":        "Esc",
        "aim.help.ctrl.esc.desc":       "zru\u0161it \u2014 zb\u00fdvaj\u00edc\u00ed v\u00fdst\u0159ely minuj\u00ed",
        "aim.help.ctrl.f1.key":         "F1",
        "aim.help.ctrl.f1.desc":        "p\u0159epnout n\u00e1pov\u011bdu",
        "aim.help.close":               "[F1]  Zav\u0159\u00edt n\u00e1pov\u011bdu",

        "help.key.heal":                "H",
        "help.desc.heal":               "Rychl\u00e9 l\u00e9\u010den\u00ed (nejlep\u0161\u00ed dostupn\u00fd item)",
        "help.key.inventory":           "I",
        "help.desc.inventory":          "Invent\u00e1\u0159",
        "help.key.swap":                "C",
        "help.desc.swap":               "V\u00fdm\u011bna zbran\u011b",

        "help.key.help":                "F1",
        "help.desc.help":               "Tato n\u00e1pov\u011bda",
        "help.key.escape":              "Esc",
        "help.desc.escape":             "Zav\u0159\u00edt menu / Ukon\u010dit hru",

        # --- Cheat / debug menu (F11) ---
        "cheat.title":                  "CHEAT MENU  [F11]",
        "cheat.section.items":          "P\u0159edm\u011bty",
        "cheat.section.enemies":        "Nep\u0159\u00e1tel\u00e9",
        "cheat.section.container":      "Kontejner",
        "cheat.section.player":         "Hr\u00e1\u010d",
        "cheat.item.ammo_9mm":          "N\u00e1boje 9mm  \u00d710",
        "cheat.item.ammo_rifle":        "N\u00e1boje do pu\u0161ky  \u00d76",
        "cheat.item.ammo_shell":        "Broky  \u00d78",
        "cheat.spawn_chest":            "Spawn truhla",
        "cheat.hp.full":                "HP \u2192 plno",
        "cheat.hp.set1":                "HP \u2192 1",
        "cheat.hp.plus10":              "L\u00e9\u010dit  +10 HP",
        "cheat.hp.plus20":              "L\u00e9\u010dit  +20 HP",
        "cheat.credits.plus100":        "+100 Kredit\u016f",
        "cheat.hint":                   "[\u2191\u2193] Pohyb   [Enter] Pou\u017e\u00edt   [Esc] Zav\u0159\u00edt",

        # --- Quit confirm dialog (in-game) ---
        "quit_confirm.title":           "P\u0158ERU\u0160IT B\u011aH",
        "quit_confirm.question":        "Vr\u00e1tit se do hlavn\u00edho menu?",
        "quit_confirm.confirm":         "[Y / Enter]  Ano",
        "quit_confirm.cancel":          "[N / Esc]   Ne",

        # --- Overheal confirm dialog ---
        "overheal_confirm.title":       "VAROVÁNÍ: PŘELÉČENÍ",
        "overheal_confirm.question":    "Léčení přesáhne max HP — použít stejně?",
        "overheal_confirm.confirm":     "[H / Y / Enter]  Použít",
        "overheal_confirm.cancel":      "[N / Esc]        Zrušit",

        # --- Exit confirm dialog (main menu) ---
        "exit_confirm.title":           "UKON\u010cIT HRU",
        "exit_confirm.question":        "Opravdu ukon\u010dit hru?",
        "exit_confirm.confirm":         "[Y / Enter]  Ano",
        "exit_confirm.cancel":          "[N / Esc]   Ne",

        # --- Items ---
        "item.pistol.name":             "Pistole",
        "item.pistol.desc":             "Standardn\u00ed 9mm pistole. Spolehlivá z\u00e1loha.",
        "item.combat_knife.name":       "Bojov\u00fd n\u016f\u017e",
        "item.combat_knife.desc":       "Lehk\u00e1 \u010depel. Rychl\u00e1 a tich\u00e1.",
        "item.shotgun.name":            "Brokovnice",
        "item.shotgun.desc":            "Devastuj\u00edc\u00ed zbl\u00edzka. Na d\u00e1lku k ni\u010demu. 4 n\u00e1boje.",
        "item.smg.name":                "Samopal",
        "item.smg.desc":                "D\u00e1vkov\u00e9 st\u0159\u00edlen\u00ed \u2014 3 n\u00e1boje za v\u00fdst\u0159el. Ni\u010d\u00ed na bl\u00edzko.",
        "item.energy_sword.name":       "Energetick\u00fd me\u010d",
        "item.energy_sword.desc":       "Vojensk\u00e1 energetick\u00e1 \u010depel. Pron\u00edk\u00e1 skrz zbroj.",
        "item.rifle.name":              "Pu\u0161ka",
        "item.rifle.desc":              "P\u0159esn\u00e1 na d\u00e1lku. Men\u0161\u00ed d\u00e1vka. 6 n\u00e1boj\u016f.",
        "item.stim_pack.name":          "Stimul\u00e1tor",
        "item.stim_pack.desc":          "Bojov\u00fd stimulant. Obnov\u00ed 10 HP.",
        "item.medkit.name":             "L\u00e9k\u00e1rni\u010dka",
        "item.medkit.desc":             "Z\u00e1chransk\u00e1 souprava. Obnov\u00ed 20 HP.",
        "item.ammo_9mm.name":           "9mm Munice \u00d7{n}",
        "item.ammo_9mm.desc":           "{n} n\u00e1boj\u016f 9mm munice.",
        "item.ammo_rifle.name":         "N\u00e1boje do pu\u0161ky \u00d7{n}",
        "item.ammo_rifle.desc":         "{n} vysokokalibern\u00edch n\u00e1boj\u016f.",
        "item.ammo_shell.name":         "Broky \u00d7{n}",
        "item.ammo_shell.desc":         "{n} brokovnicov\u00fdch n\u00e1boj\u016f.",
        "item.basic_armor.name":        "Z\u00e1kladn\u00ed zbroj",
        "item.basic_armor.desc":        "Lehk\u00e1 taktick\u00e1 vesta. Pohlt\u00ed \u010d\u00e1st po\u0161kozen\u00ed.",

        # --- Entities ---
        "entity.player.name":           "Diver",
        "entity.guard.name":            "Str\u00e1\u017en\u00fd",
        "entity.drone.name":            "Bezp. dron",
        "entity.crate.name":            "Bedna",
        "entity.corp_vault.name":       "Korp. trezor",

        # --- HUD ---
        "hud.floor":                    "PATRO {n}",
        "hud.full_hp":                  "[H] Pln\u00e9 \u017eivoty",
        "hud.no_heal":                  "[H] --",
        "hud.armor_label":              "[ZBROJ]",
        "hud.armor_none":               "\u2014",

        # --- Inventory UI ---
        "inv.title":                    "INVENT\u00c1\u0158  {n}/8",
        "inv.weapon_label":             "ZBRA\u0147:",
        "inv.armor_label":              "ZBROJ:",
        "inv.none":                     "\u2014 \u017e\u00e1dn\u00e9 \u2014",
        "inv.empty":                    "(pr\u00e1zdn\u00e9)",
        "inv.btn_use":                  "[E] Pou\u017e\u00edt",
        "inv.btn_close":                "[I] Zav\u0159\u00edt",

        # --- Weapon picker ---
        "weapon_picker.title":          "V\u00ddM\u011aNA ZBRAN\u011a",
        "weapon_picker.empty":          "(\u017e\u00e1dn\u00e9 zbran\u011b v invent\u00e1\u0159i)",
        "weapon_picker.close":          "[C/Esc] Zav\u0159\u00edt",
        "weapon_picker.hint":           "  [\u2191\u2193] Navigace   [E/Enter] Vybavit",

        # --- Game log messages ---
        "log.floor_enter":              "Patro {n} \u2014 infiltrace objektu.",
        "log.heal_cancel":              "L\u00e9\u010den\u00ed zru\u0161eno.",
        "log.no_exit":                  "Zde není nic, s čím by šlo interagovat.",
        "hint.stair_descend":           "[E] Sestoupit hlouběji",
        "log.no_heals":                 "\u017d\u00e1dn\u00e9 l\u00e9\u010div\u00e9 p\u0159edm\u011bty.",
        "log.full_hp":                  "Pln\u00e9 \u017eivoty.",
        "log.reload_full":              "Zásobník je plný.",
        "log.reload_no_reserves":       "Žádné zásoby nábojů pro přebití.",
        "log.container_already_open":   "Již vyrabováno.",
        "log.heal_confirm":             "{item}{count}: +{hp} HP (p\u0159ehoj. +{overheal}).  [H/Enter] Potvrdit",
        "log.hack_success":             "Hackov\u00e1no: {container}.{credits}",
        "log.hack_fail":                "Hack selhal \u2014 vysl\u00e1n bezpe\u010dnostn\u00ed dron!",
        "log.no_ranged":                "\u017d\u00e1dn\u00e1 st\u0159eln\u00e1 zbra\u0148.",
        "log.no_target":                "\u017d\u00e1dn\u00fd c\u00edl v dohledu.",
        "log.no_melee":                 "\u017d\u00e1dn\u00fd nep\u0159\u00edtel v dosahu.",

        # --- Action resolver log messages ---
        "log.pickup_ammo":              "Sebr\u00e1no: {item}.",
        "log.armor_duplicate":          "Zbroj {item} p\u0159esko\u010dena (slot pln\u00fd).",
        "log.armor_equip":              "Oble\u010deno: {item}  -{bonus} dmg.",
        "log.item_duplicate":           "{item} p\u0159esko\u010deno (duplik\u00e1t).",
        "log.ammo_strip":               "Rozebr\u00e1no: {item}: +{n} {ammo}.",
        "log.pickup_item":              "Sebr\u00e1no: {item}{count}.",
        "log.inv_full":                 "Invent\u00e1\u0159 pln\u00fd \u2014 nelze sebrat.",

        # --- Combat messages ---
        "log.melee_hit":                "{attacker} zas\u00e1hl {target} za {dmg} dmg.{crit}",
        "log.ranged_hit":               "{attacker} st\u0159\u00edl\u00ed na {target}{burst} za {dmg} dmg.{crit}",
        "log.ranged_miss":              "{attacker} st\u0159\u00edl\u00ed na {target} \u2014 minul!",
        "log.is_down":                  " {name} padl!",
        "log.crit":                     " KRITICK\u00dd Z\u00c1SAH!",
        "log.no_ammo":                  "Z\u00e1sobn\u00edk pr\u00e1zdn\u00fd! Stiskni R.",

        # --- Container messages ---
        "log.container_secured":        "Datov\u00e9 j\u00e1dro zaji\u0161t\u011bno!{credits} \u2014 EXTRAKCE.",
        "log.container_empty":          "{name}: pr\u00e1zdn\u00e9.{credits}",
        "log.container_open":           "Otev\u0159eno {name}: {items}.{credits}",

        # --- Inventory / equipment actions ---
        "log.descend":                  "Sestupuješ do dalšího patra.",
        "log.reloaded":                 "Přebito: {item}.",
        "log.equipped":                 "Vybaveno: {item}.",
        "log.dropped":                  "Zahozeno: {item}.",
        "log.credits_drop":             "+\u00a5{n}",

        # --- Consumable use ---
        "log.heal_restored":            "Obnoveno {n} HP.",
        "log.item_used":                "Pou\u017eito: {name}. ",

        # --- Hack minigame status ---
        "hack.status.initial":          "Prozkoumej s\u00ed\u0165 a pohni se pro za\u010d\u00e1tek.",
        "hack.status.navigate":         "P\u0159esu\u0148 se na datov\u00e9 uzly a hackni je.",
        "hack.status.routing":          "Sm\u011brov\u00e1n\u00ed na UZEL-{n}\u2026",
        "hack.status.extracting":       "Extrakce: {kind}\u2026",
        "hack.status.cancelled":        "Hack zru\u0161en.",
        "hack.status.time_penalty":     "ICE SPUT\u0164\u011aN \u2014 \u010casov\u00e1 penalta  -3s!",
        "hack.status.cache_destroyed":  "ICE SPUT\u0164\u011aN \u2014 Datov\u00e1 cache zni\u010dena!",
        "hack.status.no_targets":       "ICE SPUT\u0164\u011aN \u2014 \u017d\u00e1dn\u00e9 c\u00edle.",
        "hack.status.access_denied":    "ICE SPUT\u0164\u011aN \u2014 P\u0159\u00edstup odep\u0159en!",
        "hack.status.bonus_time":       "Bonusov\u00fd \u010das  +3s",
        "hack.status.credits":          "Kredity extrahov\u00e1ny  +\u00a5{n}",
        "hack.status.extracted":        "Extrahov\u00e1no: {item}",

        # --- Hack overlay ---
        "hack.overlay.time_title":      "\u010cASOV\u00c1 PENALTA",
        "hack.overlay.time_sub":        "\u22123 SEKUNDY",
        "hack.overlay.cache_title":     "DATA PO\u0160KOZENA",
        "hack.overlay.cache_sub":       "UZEL ZNI\u010cEN",
        "hack.overlay.notgt_title":     "ICE SPUT\u0164\u011aN",
        "hack.overlay.notgt_sub":       "\u017d\u00c1DN\u00c9 C\u00cdLE",
        "hack.overlay.denied_title":    "P\u0158\u00cdSTUP ODEP\u0158EN",
        "hack.overlay.denied_sub":      "UZEL BLOKOV\u00c1N \u2014 P\u0158ESM\u011aROV\u00c1NO",
        "hack.overlay.bonus_title":     "BONUSOV\u00dd \u010cAS",
        "hack.overlay.bonus_sub":       "+3 SEKUNDY",
        "hack.overlay.credits_title":   "KREDITY EXTRAHOV\u00c1NY",
        "hack.overlay.data_title":      "DATA EXTRAHOV\u00c1NA",

        # --- Hack result ---
        "hack.result.success":          "//  HACK DOKON\u010cEN  //",
        "hack.result.fail":             "//  SLEDOV\u00c1N\u00cd DOKON\u010cENO \u2014 ALARM  //",
        "hack.result.no_data":          "\u017d\u00e1dn\u00e1 data extrahov\u00e1na.",
        "hack.result.drone":            "Bezpe\u010dnostn\u00ed dron vysl\u00e1n!",

        # --- Hack header + node label ---
        "hack.header.title":            "INFILTRA\u010cN\u00cd PROTOKOL",
        "hack.header.esc_cancel":       "[Q]  ZARU\u0160IT EXTRAKCI",
        "hack.header.move_start":       "\u2014 POHNI SE PRO ZA\u010c\u00c1TEK \u2014",
        "hack.header.esc_abort":        "[Q]  P\u0158ERU\u0160IT HACK",
        "hack.footer.hint":             "W A S D / \u0161ipky  +  My\u0161  |  [Q] Konec  [F1] N\u00e1pov\u011bda",
        "hack.footer.counter":          "DATA: {n}/{total}",
        "hack.node.corrupt":            "PO\u0160KOZENO",

        # --- Hack loot kind labels ---
        "hack.loot.ammo":               "Munice",
        "hack.loot.rifle_ammo":         "N\u00e1boje do pu\u0161ky",
        "hack.loot.shotgun_ammo":       "N\u00e1boje do brokovnice",
        "hack.loot.heal":               "L\u00e9\u010divo",
        "hack.loot.medkit":             "L\u00e9k\u00e1rni\u010dka",
        "hack.loot.weapon":             "Zbra\u0148",
        "hack.loot.credits":            "Kredity",
        "hack.loot.bonus_time":         "Bonusov\u00fd \u010das",
        "hack.loot.armor":              "Zbroj",
        "hack.loot.mystery":            "Nezn\u00e1m\u00e9",

        # --- Hack help overlay ---
        "hack.help.title":              "// INFILTRA\u010cN\u00cd PROTOKOL \u2014 N\u00c1POV\u011aDA //",
        "hack.help.node_types":         "TYPY UZL\u016e",
        "hack.help.node.entry.lbl":     "\u25ba  VSTUP     ",
        "hack.help.node.entry.desc":    "va\u0161e v\u00fdchoz\u00ed pozice",
        "hack.help.node.cache.lbl":     "\u25aa  DATA CACHE",
        "hack.help.node.cache.desc":    "hackni pro z\u00edskan\u00ed lootu",
        "hack.help.node.empty.lbl":     "\u25aa  PR\u00c1ZDN\u00dd   ",
        "hack.help.node.empty.desc":    "jen pr\u016fchod",
        "hack.help.node.ice.lbl":       "\u25aa  ICE       ",
        "hack.help.node.ice.desc":      "skryt\u00e1 past \u2014 vypad\u00e1 jako PR\u00c1ZDN\u00dd!",
        "hack.help.ice_section":        "EFEKTY ICE  (spu\u0161t\u011bno vstupem)",
        "hack.help.ice.time.lbl":       "\u010cASOV\u00c1 PENALTA",
        "hack.help.ice.time.desc":      "\u22123 sekundy z \u010dasova\u010de",
        "hack.help.ice.corrupt.lbl":    "DATA PO\u0160KOZENA",
        "hack.help.ice.corrupt.desc":   "zni\u010d\u00ed n\u00e1hodn\u00fd nehacknut\u00fd uzel",
        "hack.help.ice.blocked.lbl":    "P\u0158\u00cdSTUP ODEP\u0158EN",
        "hack.help.ice.blocked.desc":   "blokuje vstup \u2014 odraz\u00ed t\u011b zp\u011bt",
        "hack.help.timer":              "\u010cASOVA\u010c",
        "hack.help.timer.1":            "Spust\u00ed se p\u0159i prvn\u00edm pohybu",
        "hack.help.timer.2":            "Ukazatel naho\u0159e: zelen\u00fd \u2192 oran\u017eov\u00fd \u2192 \u010derven\u00fd",
        "hack.help.timer.3":            "Uzel BONUSOV\u00dd \u010cAS: +3 sekundy",
        "hack.help.timer.4":            "Sesbírej v\u0161e pro rychl\u00e9 ukon\u010den\u00ed",
        "hack.help.controls":           "OVL\u00c1D\u00c1N\u00cd",
        "hack.help.ctrl.wasd.key":      "W / A / S / D",
        "hack.help.ctrl.wasd.desc":     "pohyb na sousedn\u00ed uzel",
        "hack.help.ctrl.arrows.key":    "\u0160ipky",
        "hack.help.ctrl.arrows.desc":   "stejn\u00e9 jako W A S D",
        "hack.help.ctrl.mouse.key":     "Klik my\u0161\u00ed",
        "hack.help.ctrl.mouse.desc":    "klikni na souseda pro pohyb",
        "hack.help.ctrl.esc.key":       "Q  /  Esc",
        "hack.help.ctrl.esc.desc":      "zru\u0161it extrakci / p\u0159eru\u0161it hack",
        "hack.help.ctrl.f1.key":        "F1",
        "hack.help.ctrl.f1.desc":       "p\u0159epnout n\u00e1pov\u011bdu (\u010dasova\u010d zastaven)",
        "hack.help.close":              "[F1]  Zav\u0159\u00edt n\u00e1pov\u011bdu",
        "hack.help.grid_section":       "GRID",
        "hack.help.grid.automove":      "Auto-pohyb: stiskni sm\u011br",
        "hack.help.grid.stop":          "Zastav\u00ed u uzlu nebo zm\u011bnou sm\u011bru",
        "hack.help.grid.lit":           "Osv\u00edtit cesty = dosa\u017eiteln\u00e9 uzly",

        # --- HUD hint ---
        "hud.help_hint":                "[F1] N\u00e1pov\u011bda",

        # --- Settings overlay ---
        "settings.title":               "NASTAVEN\u00cd",
        "settings.section.difficulty":  "OBT\u00cd\u017dNOST",
        "settings.section.gameplay":    "HRA",
        "settings.section.audio":       "ZVUK",
        "settings.section.language":    "JAZYK",
        "settings.gameplay.loot":       "Loot",
        "settings.gameplay.aim":        "M\u00ed\u0159en\u00ed",
        "settings.gameplay.heal":       "L\u00e9\u010den\u00ed",
        "settings.gameplay.heal_threshold": "Quickheal",
        "settings.gameplay.heal_threshold_suffix": "pr\u00e1h",
        "menu.heal.thr.80":             "Za\u010d\u00e1te\u010dn\u00edk",
        "menu.heal.thr.90":             "U\u010d\u00edm se",
        "menu.heal.thr.100":            "V\u00fdchoz\u00ed",
        "menu.heal.thr.110":            "Zku\u0161en\u00fd",
        "menu.heal.thr.120":            "Zdatn\u00fd",
        "settings.audio.master":        "Hlavn\u00ed",
        "settings.audio.music":         "Hudba",
        "settings.audio.sfx":           "Efekty",
        "settings.footer":              "[Esc]  Zav\u0159\u00edt",

        # --- Help catalog ---
        "help_catalog.title":           "N\u00c1POV\u011aDA",
        "help_catalog.tab.exploration": "PR\u016aSKUM",
        "help_catalog.tab.combat":      "BOJ",
        "help_catalog.tab.shooting":    "ST\u0158ELBA",
        "help_catalog.tab.aiming":      "M\u00cd\u0158EN\u00cd",
        "help_catalog.tab.hacking":     "HACKING",
        "help_catalog.tab.healing":     "L\u00c9\u010c\u00c9N\u00cd",
        "help_catalog.footer":          "[\u25c4 \u25ba] P\u0159epnout   [Esc] Zav\u0159\u00edt",

        # Exploration illustration labels
        "help_catalog.expl.icon.container": "Kontejner",
        "help_catalog.expl.icon.ammo":      "Munice",
        "help_catalog.expl.icon.stairs":    "Schody",
        "help_catalog.expl.icon.vault":     "Trezor",

        # Hack node illustration labels
        "help_catalog.hack.node.entry":     "VSTUP",
        "help_catalog.hack.node.cache":     "DATA CACHE",
        "help_catalog.hack.node.empty":     "PR\u00c1ZDN\u00dd",
        "help_catalog.hack.node.ice":       "ICE (skryt\u00fd)",
        "help_catalog.hack.loot_label":     "P\u0159\u00edklady lootu:",

        # Exploration tab
        "help_catalog.expl.h1":         "POHYB",
        "help_catalog.expl.1.1":        "WASD / \u0161ipky \u2014 pohyb o dla\u017edici; \u00fatok na sousedn\u00edho nep\u0159\u00edtele",
        "help_catalog.expl.1.2":        "Ka\u017ed\u00fd krok spot\u0159ebuje jedno kolo \u2014 nep\u0159\u00e1tel\u00e9 reaguj\u00ed",
        "help_catalog.expl.1.3":        "Mezer\u00edk nebo . \u2014 \u010dek\u00e1n\u00ed (p\u0159esko\u010den\u00ed kola)",
        "help_catalog.expl.h2":         "ZORN\u00c9 POLE",
        "help_catalog.expl.2.1":        "Dosah vid\u011bn\u00ed: 10 dla\u017edic od tv\u00e9 pozice",
        "help_catalog.expl.2.2":        "Prozkoumaná oblast viditelná ve tm\u011b \u2014 nep\u0159\u00e1tel\u00e9 nejsou sledov\u00e1ni",
        "help_catalog.expl.h3":         "SCHODY & KONTEJNERY",
        "help_catalog.expl.3.1":        "E \u2014 schody dol\u016f nebo otev\u0159\u00edt kontejner",
        "help_catalog.expl.3.2":        "Kontejnery mohou obsahovat p\u0159edm\u011bty, zbran\u011b nebo kredity",
        "help_catalog.expl.3.3":        "V\u0161echny kontejnery spust\u00ed hackov\u00e1n\u00ed pro bonus (pokud je povoleno)",

        # Combat tab
        "help_catalog.comb.h1":         "BOJ ZBLÍZKA",
        "help_catalog.comb.1.1":        "Jdi na nep\u0159\u00edtele pro \u00fatok zbl\u00edzka (narážen\u00ed)",
        "help_catalog.comb.1.2":        "Diagon\u00e1ln\u00ed pohyb a \u00fatok jsou povolen\u00e9",
        "help_catalog.comb.1.3":        "F \u2014 zaú\u010dtuj na nejbli\u017e\u0161\u00edho nep\u0159\u00edtele v dosahu",
        "help_catalog.comb.h2":         "ZBROJ",
        "help_catalog.comb.2.1":        "Zbroj sn\u00ed\u017e\u00ed p\u0159\u00edchoz\u00ed po\u0161kozen\u00ed o svou obrannou hodnotu",
        "help_catalog.comb.2.2":        "Auto-vybav\u00ed p\u0159i sb\u011bru; siln\u011bj\u0161\u00ed nahrad\u00ed slabš\u00ed",
        "help_catalog.comb.2.3":        "Vybavenú zbroj zobraz v invent\u00e1\u0159i (kl\u00e1vesa I)",
        "help_catalog.comb.h3":         "NEP\u0158\u00c1TEL\u00c9",
        "help_catalog.comb.3.1":        "Str\u00e1\u017en\u00ed: \u00fato\u010d\u00ed zbl\u00edzka, hlidkuj\u00ed chodby, st\u00ed\u017e\u00ed p\u0159i spatřen\u00ed",
        "help_catalog.comb.3.2":        "Drony: st\u0159\u00edlej\u00ed, dr\u017e\u00ed si vzd\u00e1lenost, vysl\u00e1ni p\u0159i sel\u00e1n\u00ed hacku",
        "help_catalog.comb.3.3":        "Nep\u0159\u00e1tel\u00e9 reaguj\u00ed jen v linii dohledu",

        # Shooting tab
        "help_catalog.shoot.h1":        "BOJI NA D\u00c1LKU",
        "help_catalog.shoot.1.1":       "F \u2014 nam\u00ed\u0159\u00ed a vystr\u011bl na vybran\u00fd c\u00edl",
        "help_catalog.shoot.1.2":       "Tab \u2014 p\u0159ep\u00edn\u00e1n\u00ed mezi viditeln\u00fdmi nep\u0159\u00e1teli",
        "help_catalog.shoot.1.3":       "R \u2014 p\u0159ebit\u00ed zbran\u011b",
        "help_catalog.shoot.1.4":       "C \u2014 v\u00fdm\u011bna zbran\u011b",
        "help_catalog.shoot.h2":        "MUNICE",
        "help_catalog.shoot.2.1":       "9mm \u2014 Pistole a samopal",
        "help_catalog.shoot.2.2":       "N\u00e1boje do pu\u0161ky \u2014 Pu\u0161ka",
        "help_catalog.shoot.2.3":       "Broky \u2014 Brokovnice",
        "help_catalog.shoot.2.4":       "Munice se automaticky sb\u00edr\u00e1 od nep\u0159\u00e1tel a z kontejner\u016f",
        "help_catalog.shoot.h3":        "ZBRAN\u011a",
        "help_catalog.shoot.3.1":       "Pistole \u2014 spolehlivá, st\u0159edn\u00ed dosah",
        "help_catalog.shoot.3.2":       "Samopal \u2014 d\u00e1vka 3 n\u00e1boj\u016f, smrteln\u00fd zbl\u00edzka",
        "help_catalog.shoot.3.3":       "Brokovnice \u2014 devastující zbl\u00edzka, 4 broky",
        "help_catalog.shoot.3.4":       "Pu\u0161ka \u2014 velk\u00fd dosah, p\u0159esn\u00e9 st\u0159ely",
        "help_catalog.shoot.3.5":       "Energetick\u00fd me\u010d \u2014 jen zbl\u00edzka, pron\u00edk\u00e1 zbrojí",
        "help_catalog.shoot.3.6":       "Bojov\u00fd n\u016f\u017e \u2014 jen zbl\u00edzka, rychl\u00fd \u00fatok na kr\u00e1tkou vzd\u00e1lenost",

        # Aiming tab
        "help_catalog.aim.h1":          "JAK FUNGUJE M\u00cd\u0158EN\u00cd",
        "help_catalog.aim.1.1":         "Ru\u010di\u010dka kmit\u00e1 tam a zp\u011bt po oblouku",
        "help_catalog.aim.1.2":         "Stiskni F nebo klikni a zastav ji",
        "help_catalog.aim.1.3":         "Zelen\u00e1 z\u00f3na = z\u00e1sah;  mimo z\u00f3nu = minul",
        "help_catalog.aim.1.4":         "Zastaven\u00ed bl\u00edzko st\u0159edu = maxim\u00e1ln\u00ed po\u0161kozen\u00ed",
        "help_catalog.aim.1.5":         "Ru\u010di\u010dka se po ka\u017ed\u00e9m odrazu zrychl\u00ed",
        "help_catalog.aim.h2":          "P\u0158ESNOST & KRITICK\u00c9 Z\u00c1SAHY",
        "help_catalog.aim.2.1":         "Z\u00f3na se zmen\u0161uje se vzd\u00e1lenost\u00ed c\u00edle",
        "help_catalog.aim.2.2":         "Zastav na \u226595\u00a0% pro KRITICK\u00dd Z\u00c1SAH",
        "help_catalog.aim.2.3":         "Kritick\u00fd = max po\u0161kozen\u00ed \u2014 efekt se odemyk\u00e1 b\u011bhem hry",
        "help_catalog.aim.h3":          "OVL\u00c1D\u00c1N\u00cd",
        "help_catalog.aim.3.1":         "F / klik \u2014 zastav ru\u010di\u010dku a vystr\u011bl",
        "help_catalog.aim.3.2":         "Tab \u2014 p\u0159epni c\u00edl p\u0159ed v\u00fdst\u0159elem",
        "help_catalog.aim.3.3":         "Esc \u2014 zru\u0161it; zb\u00fdvaj\u00edc\u00ed v\u00fdst\u0159ely automaticky minuj\u00ed",

        # Hacking tab
        "help_catalog.hack.h1":         "Z\u00c1KLADY HACKOVÁNÍ",
        "help_catalog.hack.1.1":        "P\u0159esuň se na uzly DATA CACHE a vstup do nich",
        "help_catalog.hack.1.2":        "\u010casova\u010d startuje p\u0159i prvn\u00edm pohybu",
        "help_catalog.hack.1.3":        "Sesbírej v\u0161echny cache nebo po\u010dkej na uplynut\u00ed \u010dasu",
        "help_catalog.hack.h2":         "TYPY UZL\u016e",
        "help_catalog.hack.2.1":        "\u25ba VSTUP \u2014 tv\u00e1 v\u00fdchoz\u00ed pozice",
        "help_catalog.hack.2.2":        "\u25aa DATA CACHE \u2014 hackni pro z\u00edskan\u00ed lootu",
        "help_catalog.hack.2.3":        "\u25aa PR\u00c1ZDN\u00dd \u2014 jen pr\u016fchod",
        "help_catalog.hack.2.4":        "\u25aa ICE \u2014 skryt\u00e1 past, vypad\u00e1 jako PR\u00c1ZDN\u00dd!",
        "help_catalog.hack.h3":         "EFEKTY ICE",
        "help_catalog.hack.3.1":        "\u010cASOV\u00c1 PENALTA \u2014 \u22123 sekundy z \u010dasova\u010de",
        "help_catalog.hack.3.2":        "DATA PO\u0160KOZENA \u2014 zni\u010d\u00ed n\u00e1hodn\u00fd nehacknut\u00fd uzel",
        "help_catalog.hack.3.3":        "P\u0158\u00cdSTUP ODEP\u0158EN \u2014 odraz\u00ed t\u011b zp\u011bt, blokuje vstup",
        "help_catalog.hack.h4":         "OVL\u00c1D\u00c1N\u00cd",
        "help_catalog.hack.4.1":        "WASD / \u0161ipky \u2014 pohyb na sousedn\u00ed uzel",
        "help_catalog.hack.4.2":        "Klik my\u0161\u00ed \u2014 klikni na souseda pro pohyb",
        "help_catalog.hack.4.3":        "Q / Esc \u2014 zru\u0161it extrakci / p\u0159eru\u0161it hack",

        # Healing tab
        "heal.help.h1":                 "JAK FUNGUJE L\u00c9\u010cEN\u00cd",
        "heal.help.1":                  "Sleduj dva tepy \u2014 du-dum, du-dum",
        "heal.help.2":                  "Stiskni H na t\u0159et\u00edm tepu, dr\u017e p\u0159es mezeru",
        "heal.help.3":                  "Uvolni H kdy\u017e by m\u011bl zaznít druh\u00fd tep",
        "heal.help.4":                  "Perfektn\u00ed \u2192 +20%   Mimo \u2192 \u221220%",
        "heal.help.h2":                 "HODNOCEN\u00cd",
        "heal.help.s1":                 "Perfektn\u00ed +20%  |  Skvěle +10%  |  Dob\u0159e \u00b10%",
        "heal.help.s2":                 "Slab\u011b \u221210%  |  \u0160patn\u011b \u221220%",
        "heal.help.s3":                 "Sk\u00f3re = sou\u010det odchylek stisku + uvoln\u011bn\u00ed",
        "heal.help.h3":                 "OVLÁD\u00c1N\u00cd",
        "heal.help.key1":               "[H dr\u017e] \u2014 stisk na tep (stah)",
        "heal.help.key2":               "[uvolni H] \u2014 uvolni po meze\u0159e (rozta\u017een\u00ed)",
        "heal.help.key3":               "[Esc] \u2014 zru\u0161it l\u00e9\u010den\u00ed",
        "heal.help.key4":               "[F1] \u2014 zobrazit/skr\u00fdt n\u00e1pov\u011bdu",

        # Heal overlay runtime strings
        "heal.overlay.title":           "Srde\u010dn\u00ed rytmus",
        "heal.overlay.watch":           "Sleduj...",
        "heal.overlay.now":             "TE\u010e!",
        "heal.overlay.hint":            "[H] stiskni a dr\u017e na 3. tep",
        "heal.overlay.perfect":         "Perfektn\u00ed!",
        "heal.overlay.great":           "Skvěle",
        "heal.overlay.good":            "Dob\u0159e",
        "heal.overlay.poor":            "Slab\u011b",
        "heal.overlay.miss":            "Špatně",
    },

    "es": {
        # --- Main menu ---
        "menu.title":                   "DUNGEONEER",
        "menu.subtitle":                "Entre partidas",
        "menu.difficulty":              "DIFICULTAD",
        "menu.easy":                    "F\u00e1cil",
        "menu.normal":                  "Normal",
        "menu.hard":                    "Dif\u00edcil",
        "menu.loot_mode":               "MODO DE SAQUEO",
        "menu.loot.minigame":           "Hackeo",
        "menu.loot.random":             "Loot aleatorio",
        "menu.language":                "IDIOMA",
        "menu.start":                   "Iniciar partida",
        "menu.quit":                    "Salir",
        "menu.aim_minigame":            "APUNTADO",
        "menu.aim_minigame_on":         "S\u00cd",
        "menu.aim_minigame_off":        "NO",
        "menu.hints":                   "[Enter] Iniciar   [F1] Ayuda   [Esc] Salir",

        # --- Game over ---
        "gameover.victory":             "EXTRACCI\u00d3N COMPLETA",
        "gameover.defeat":              "MUERTO EN COMBATE",
        "gameover.victory_sub":         "Lograste salir con vida.",
        "gameover.defeat_sub":          "Tu se\u00f1al se ha apagado.",
        "gameover.floors":              "Plantas despejadas: {n}",
        "gameover.credits":             "Cr\u00e9ditos ganados: \u00a5 {n}",
        "gameover.menu":                "Men\u00fa principal  [R]",
        "gameover.quit":                "Salir  [Esc]",

        # --- Help screen ---
        "help.title":                   "AYUDA",
        "help.footer":                  "[F1 / Esc / Enter]  Cerrar",

        "help.section.movement":        "MOVIMIENTO Y ACCIONES",
        "help.section.combat":          "COMBATE",
        "help.section.items":           "OBJETOS",
        "help.section.general":         "GENERAL",

        "help.key.wasd":                "WASD / Flechas",
        "help.desc.wasd":               "Mover \u2014 o atacar al enemigo adyacente",
        "help.key.wait":                "Space / .",
        "help.desc.wait":               "Esperar (saltar turno)",
        "help.key.interact":            "E",
        "help.desc.interact":           "Bajar escaleras / abrir contenedor",

        "help.key.shoot":               "F",
        "help.desc.shoot":              "Atacar al enemigo m\u00e1s cercano (cuerpo a cuerpo o a distancia)",
        "help.key.target":              "Tab",
        "help.desc.target":             "Cambiar objetivo entre enemigos visibles",
        "help.key.aim":                 "F / clic",
        "help.desc.aim":                "Para la aguja en la zona \u2014 centro = m\u00e1x da\u00f1o / cr\u00edtico. Fuera = fallo.",
        "help.key.reload":              "R",
        "help.desc.reload":             "Recargar arma",

        # --- Aim minigame ---
        "aim.title":                    "APUNTANDO",
        "aim.press_f":                  "F / clic para disparar",
        "aim.shot_n":                   "Disparo {n}/{total}",
        "aim.miss":                     "FALLO",
        "aim.hit":                      "IMPACTO",
        "aim.crit":                     "CR\u00cdTICO",

        # --- Aim help overlay (F1) ---
        "aim.help.hint":                "[F1] ayuda",
        "aim.help.title":               "// APUNTADO \u2014 AYUDA //",
        "aim.help.mechanic":            "C\u00d3MO FUNCIONA EL APUNTADO",
        "aim.help.mech.1":              "La aguja oscila de un lado a otro en el arco",
        "aim.help.mech.2":              "Pulsa F o haz clic para detener la aguja",
        "aim.help.mech.3":              "Zona verde = impacto;  fuera = fallo",
        "aim.help.mech.4":              "Centro de zona = da\u00f1o m\u00e1ximo",
        "aim.help.mech.5":              "La aguja acelera en cada rebote",
        "aim.help.mech.zone":           "La zona se reduce con la distancia al objetivo",
        "aim.help.armor":               "ARMADURA",
        "aim.help.armor.1":             "La armadura equipada absorbe 1 da\u00f1o por impacto",
        "aim.help.armor.2":             "Se equipa sola; solo una m\u00e1s fuerte la reemplaza",
        "aim.help.crit":                "GOLPES CR\u00cdTICOS",
        "aim.help.crit.1":              "Para la aguja a \u226595% de precisi\u00f3n para CR\u00cdTICO",
        "aim.help.crit.2":              "Cr\u00edtico = da\u00f1o m\u00e1ximo del arma (se desbloquea al progresar)",
        "aim.help.controls":            "CONTROLES",
        "aim.help.ctrl.f.key":          "F / clic",
        "aim.help.ctrl.f.desc":         "detener aguja / disparar",
        "aim.help.ctrl.tab.key":        "Tab",
        "aim.help.ctrl.tab.desc":       "cambiar objetivo",
        "aim.help.ctrl.esc.key":        "Esc",
        "aim.help.ctrl.esc.desc":       "cancelar \u2014 disparos restantes fallan",
        "aim.help.ctrl.f1.key":         "F1",
        "aim.help.ctrl.f1.desc":        "alternar esta ayuda",
        "aim.help.close":               "[F1]  Cerrar ayuda",

        "help.key.heal":                "H",
        "help.desc.heal":               "Curar r\u00e1pido (mejor objeto disponible)",
        "help.key.inventory":           "I",
        "help.desc.inventory":          "Inventario",
        "help.key.swap":                "C",
        "help.desc.swap":               "Cambiar arma",

        "help.key.help":                "F1",
        "help.desc.help":               "Esta pantalla de ayuda",
        "help.key.escape":              "Esc",
        "help.desc.escape":             "Cerrar men\u00fa / Salir",

        # --- Cheat / debug menu (F11) ---
        "cheat.title":                  "CHEAT MENU  [F11]",
        "cheat.section.items":          "Objetos",
        "cheat.section.enemies":        "Enemigos",
        "cheat.section.container":      "Contenedor",
        "cheat.section.player":         "Jugador",
        "cheat.item.ammo_9mm":          "Muni\u00f3n 9mm  \u00d710",
        "cheat.item.ammo_rifle":        "Muni\u00f3n Rifle  \u00d76",
        "cheat.item.ammo_shell":        "Cartuchos  \u00d78",
        "cheat.spawn_chest":            "Generar Ba\u00fal",
        "cheat.hp.full":                "HP \u2192 completo",
        "cheat.hp.set1":                "HP \u2192 1",
        "cheat.hp.plus10":              "Curar  +10 HP",
        "cheat.hp.plus20":              "Curar  +20 HP",
        "cheat.credits.plus100":        "+100 Cr\u00e9ditos",
        "cheat.hint":                   "[\u2191\u2193] Navegar   [Enter] Usar   [Esc] Cerrar",

        # --- Quit confirm dialog (in-game) ---
        "quit_confirm.title":           "ABANDONAR PARTIDA",
        "quit_confirm.question":        "\u00bfVolver al men\u00fa principal?",
        "quit_confirm.confirm":         "[Y / Enter]  S\u00ed",
        "quit_confirm.cancel":          "[N / Esc]   No",

        # --- Overheal confirm dialog ---
        "overheal_confirm.title":       "AVISO: SOBREC\u00dara",
        "overheal_confirm.question":    "La curación superará el HP máx. — ¿usar igual?",
        "overheal_confirm.confirm":     "[H / Y / Enter]  Usar",
        "overheal_confirm.cancel":      "[N / Esc]        Cancelar",

        # --- Exit confirm dialog (main menu) ---
        "exit_confirm.title":           "SALIR DEL JUEGO",
        "exit_confirm.question":        "\u00bfSalir del juego?",
        "exit_confirm.confirm":         "[Y / Enter]  S\u00ed",
        "exit_confirm.cancel":          "[N / Esc]   No",

        # --- Items ---
        "item.pistol.name":             "Pistola",
        "item.pistol.desc":             "Pistola 9mm est\u00e1ndar. Respaldo confiable.",
        "item.combat_knife.name":       "Cuchillo",
        "item.combat_knife.desc":       "Hoja ligera. R\u00e1pida y silenciosa.",
        "item.shotgun.name":            "Escopeta",
        "item.shotgun.desc":            "Devastadora de cerca. In\u00fatil a distancia. 4 cartuchos.",
        "item.smg.name":                "Subfusil",
        "item.smg.desc":                "Fuego en r\u00e1faga \u2014 3 rondas por disparo. Destruye de cerca.",
        "item.energy_sword.name":       "Espada de energ\u00eda",
        "item.energy_sword.desc":       "Hoja de energ\u00eda militar. Atraviesa la armadura.",
        "item.rifle.name":              "Fusil",
        "item.rifle.desc":              "Precisi\u00f3n a larga distancia. 6 rondas.",
        "item.stim_pack.name":          "Estimulante",
        "item.stim_pack.desc":          "Estimulante de combate. Restaura 10 HP.",
        "item.medkit.name":             "Botiquin",
        "item.medkit.desc":             "Kit de trauma completo. Restaura 20 HP.",
        "item.ammo_9mm.name":           "Mun. 9mm \u00d7{n}",
        "item.ammo_9mm.desc":           "{n} rondas de munición 9mm.",
        "item.ammo_rifle.name":         "Mun. fusil \u00d7{n}",
        "item.ammo_rifle.desc":         "{n} rondas de alto calibre.",
        "item.ammo_shell.name":         "Cartuchos \u00d7{n}",
        "item.ammo_shell.desc":         "{n} cartuchos de escopeta.",
        "item.basic_armor.name":        "Armadura b\u00e1sica",
        "item.basic_armor.desc":        "Chaleco t\u00e1ctico ligero. Absorbe algo del da\u00f1o.",

        # --- Entities ---
        "entity.player.name":           "Diver",
        "entity.guard.name":            "Guardia Corp.",
        "entity.drone.name":            "Dron Seg.",
        "entity.crate.name":            "Cajón",
        "entity.corp_vault.name":       "Cámara Corp.",

        # --- HUD ---
        "hud.floor":                    "PLANTA {n}",
        "hud.full_hp":                  "[H] Salud llena",
        "hud.no_heal":                  "[H] --",
        "hud.armor_label":              "[ARMADURA]",
        "hud.armor_none":               "\u2014",

        # --- Inventory UI ---
        "inv.title":                    "INVENTARIO  {n}/8",
        "inv.weapon_label":             "ARMA:",
        "inv.armor_label":              "ARMADURA:",
        "inv.none":                     "\u2014 ninguno \u2014",
        "inv.empty":                    "(vac\u00edo)",
        "inv.btn_use":                  "[E] Usar",
        "inv.btn_close":                "[I] Cerrar",

        # --- Weapon picker ---
        "weapon_picker.title":          "CAMBIAR ARMA",
        "weapon_picker.empty":          "(sin armas en el inventario)",
        "weapon_picker.close":          "[C/Esc] Cerrar",
        "weapon_picker.hint":           "  [\u2191\u2193] Navegar   [E/Enter] Equipar",

        # --- Game log messages ---
        "log.floor_enter":              "Planta {n} \u2014 infiltrando el edificio.",
        "log.heal_cancel":              "Curaci\u00f3n cancelada.",
        "log.no_exit":                  "No hay nada con lo que interactuar aquí.",
        "hint.stair_descend":           "[E] Descender más profundo",
        "log.no_heals":                 "No hay objetos de curaci\u00f3n.",
        "log.full_hp":                  "Ya tienes salud completa.",
        "log.reload_full":              "El cargador está lleno.",
        "log.reload_no_reserves":       "Sin reservas de munición para recargar.",
        "log.container_already_open":   "Ya saqueado.",
        "log.heal_confirm":             "{item}{count}: +{hp} HP (exceso +{overheal}).  [H/Enter] Confirmar",
        "log.hack_success":             "Hackeado: {container}.{credits}",
        "log.hack_fail":                "Hackeo fallido \u2014 \u00a1dr\u00f3n de seguridad enviado!",
        "log.no_ranged":                "Sin arma a distancia equipada.",
        "log.no_target":                "Sin objetivo a la vista.",
        "log.no_melee":                 "Sin enemigo al alcance.",

        # --- Action resolver log messages ---
        "log.pickup_ammo":              "Recogido: {item}.",
        "log.armor_duplicate":          "Armadura {item} ignorada (ranura ocupada).",
        "log.armor_equip":              "Equipado: {item}  -{bonus} dmg.",
        "log.item_duplicate":           "{item} ignorado (duplicado).",
        "log.ammo_strip":               "Desmontado: {item}: +{n} {ammo}.",
        "log.pickup_item":              "Recogido: {item}{count}.",
        "log.inv_full":                 "Inventario lleno \u2014 no se puede recoger.",

        # --- Combat messages ---
        "log.melee_hit":                "{attacker} golpea a {target} por {dmg} dmg.{crit}",
        "log.ranged_hit":               "{attacker} dispara a {target}{burst} por {dmg} dmg.{crit}",
        "log.ranged_miss":              "{attacker} dispara a {target} \u2014 \u00a1fallo!",
        "log.is_down":                  " \u00a1{name} ca\u00eddo!",
        "log.crit":                     " \u00a1CR\u00cdTICO!",
        "log.no_ammo":                  "\u00a1Sin munición! Pulsa R.",

        # --- Container messages ---
        "log.container_secured":        "\u00a1N\u00facleo asegurado!{credits} \u2014 EXTRAYENDO.",
        "log.container_empty":          "{name}: vac\u00edo.{credits}",
        "log.container_open":           "Abierto {name}: {items}.{credits}",

        # --- Inventory / equipment actions ---
        "log.descend":                  "Desciendes al siguiente nivel.",
        "log.reloaded":                 "Recargado: {item}.",
        "log.equipped":                 "Equipado: {item}.",
        "log.dropped":                  "Tirado: {item}.",
        "log.credits_drop":             "+\u00a5{n}",

        # --- Consumable use ---
        "log.heal_restored":            "Restaurados {n} HP.",
        "log.item_used":                "Usado: {name}. ",

        # --- Hack minigame status ---
        "hack.status.initial":          "Analiza la red y mu\u00e9vete para comenzar.",
        "hack.status.navigate":         "Navega a los nodos de datos y hackéalos.",
        "hack.status.routing":          "Enrutando al NODO-{n}\u2026",
        "hack.status.extracting":       "Extrayendo {kind}\u2026",
        "hack.status.cancelled":        "Hackeo cancelado.",
        "hack.status.time_penalty":     "ICE ACTIVADO \u2014 Penalizaci\u00f3n  -3s!",
        "hack.status.cache_destroyed":  "ICE ACTIVADO \u2014 \u00a1Cach\u00e9 destruida!",
        "hack.status.no_targets":       "ICE ACTIVADO \u2014 Sin objetivos.",
        "hack.status.access_denied":    "ICE ACTIVADO \u2014 \u00a1Acceso denegado!",
        "hack.status.bonus_time":       "Tiempo extra  +3s",
        "hack.status.credits":          "Cr\u00e9ditos extra\u00eddos  +\u00a5{n}",
        "hack.status.extracted":        "Extra\u00eddo: {item}",

        # --- Hack overlay ---
        "hack.overlay.time_title":      "PENALIZACI\u00d3N",
        "hack.overlay.time_sub":        "\u22123 SEGUNDOS",
        "hack.overlay.cache_title":     "DATOS CORRUPTOS",
        "hack.overlay.cache_sub":       "NODO DESTRUIDO",
        "hack.overlay.notgt_title":     "ICE ACTIVADO",
        "hack.overlay.notgt_sub":       "SIN OBJETIVOS",
        "hack.overlay.denied_title":    "ACCESO DENEGADO",
        "hack.overlay.denied_sub":      "NODO BLOQUEADO \u2014 REDIRIGIDO",
        "hack.overlay.bonus_title":     "TIEMPO EXTRA",
        "hack.overlay.bonus_sub":       "+3 SEGUNDOS",
        "hack.overlay.credits_title":   "CR\u00c9DITOS EXTRA\u00cdDOS",
        "hack.overlay.data_title":      "DATOS EXTRA\u00cdDOS",

        # --- Hack result ---
        "hack.result.success":          "//  HACKEO COMPLETO  //",
        "hack.result.fail":             "//  RASTREO COMPLETO \u2014 ALARMA  //",
        "hack.result.no_data":          "No se extrajeron datos.",
        "hack.result.drone":            "\u00a1Dr\u00f3n de seguridad enviado!",

        # --- Hack header + node label ---
        "hack.header.title":            "PROTOCOLO DE INTRUSI\u00d3N",
        "hack.header.esc_cancel":       "[Q]  CANCELAR EXTRACCI\u00d3N",
        "hack.header.move_start":       "\u2014 MU\u00c9VETE PARA INICIAR \u2014",
        "hack.header.esc_abort":        "[Q]  ABORTAR HACK",
        "hack.footer.hint":             "W A S D / Flechas  +  Rat\u00f3n  |  [Q] Salir  [F1] Ayuda",
        "hack.footer.counter":          "DATOS: {n}/{total}",
        "hack.node.corrupt":            "CORRUPTO",

        # --- Hack loot kind labels ---
        "hack.loot.ammo":               "Munición",
        "hack.loot.rifle_ammo":         "Mun. fusil",
        "hack.loot.shotgun_ammo":       "Mun. escopeta",
        "hack.loot.heal":               "Medicamento",
        "hack.loot.medkit":             "Botiquin",
        "hack.loot.weapon":             "Arma",
        "hack.loot.credits":            "Cr\u00e9ditos",
        "hack.loot.bonus_time":         "Tiempo extra",
        "hack.loot.armor":              "Armadura",
        "hack.loot.mystery":            "Desconocido",

        # --- Hack help overlay ---
        "hack.help.title":              "// PROTOCOLO DE INTRUSI\u00d3N \u2014 AYUDA //",
        "hack.help.node_types":         "TIPOS DE NODOS",
        "hack.help.node.entry.lbl":     "\u25ba  ENTRADA   ",
        "hack.help.node.entry.desc":    "tu posici\u00f3n inicial",
        "hack.help.node.cache.lbl":     "\u25aa  CACH\u00c9     ",
        "hack.help.node.cache.desc":    "hackea para extraer bot\u00edn",
        "hack.help.node.empty.lbl":     "\u25aa  VAC\u00cdO     ",
        "hack.help.node.empty.desc":    "solo travesia",
        "hack.help.node.ice.lbl":       "\u25aa  ICE       ",
        "hack.help.node.ice.desc":      "trampa oculta \u2014 \u00a1parece VAC\u00cdO!",
        "hack.help.ice_section":        "EFECTOS ICE  (activados al entrar)",
        "hack.help.ice.time.lbl":       "PENALIZACI\u00d3N",
        "hack.help.ice.time.desc":      "\u22123 segundos del reloj",
        "hack.help.ice.corrupt.lbl":    "DATOS CORRUPTOS",
        "hack.help.ice.corrupt.desc":   "destruye un nodo no hackeado",
        "hack.help.ice.blocked.lbl":    "ACCESO DENEGADO",
        "hack.help.ice.blocked.desc":   "bloquea la entrada \u2014 te devuelve",
        "hack.help.timer":              "TEMPORIZADOR",
        "hack.help.timer.1":            "Empieza con tu primer movimiento",
        "hack.help.timer.2":            "Barra: verde \u2192 naranja \u2192 rojo",
        "hack.help.timer.3":            "Nodo TIEMPO EXTRA: +3 segundos",
        "hack.help.timer.4":            "Recoge todos los cach\u00e9s para terminar antes",
        "hack.help.controls":           "CONTROLES",
        "hack.help.ctrl.wasd.key":      "W / A / S / D",
        "hack.help.ctrl.wasd.desc":     "mover al nodo adyacente",
        "hack.help.ctrl.arrows.key":    "Teclas de flecha",
        "hack.help.ctrl.arrows.desc":   "igual que W A S D",
        "hack.help.ctrl.mouse.key":     "Clic de rat\u00f3n",
        "hack.help.ctrl.mouse.desc":    "haz clic en un vecino para mover",
        "hack.help.ctrl.esc.key":       "Q  /  Esc",
        "hack.help.ctrl.esc.desc":      "cancelar extracci\u00f3n / abortar hackeo",
        "hack.help.ctrl.f1.key":        "F1",
        "hack.help.ctrl.f1.desc":       "alternar esta ayuda (temporizador pausado)",
        "hack.help.close":              "[F1]  Cerrar ayuda",
        "hack.help.grid_section":       "GRID",
        "hack.help.grid.automove":      "Auto-mover: pulsa una direcci\u00f3n",
        "hack.help.grid.stop":          "Para en nodo o al cambiar direcci\u00f3n",
        "hack.help.grid.lit":           "Rutas iluminadas = nodos alcanzables",

        # --- HUD hint ---
        "hud.help_hint":                "[F1] Ayuda",

        # --- Settings overlay ---
        "settings.title":               "CONFIGURACI\u00d3N",
        "settings.section.difficulty":  "DIFICULTAD",
        "settings.section.gameplay":    "JUEGO",
        "settings.section.audio":       "AUDIO",
        "settings.section.language":    "IDIOMA",
        "settings.gameplay.loot":       "Saqueo",
        "settings.gameplay.aim":        "Apuntado",
        "settings.gameplay.heal":       "Curaci\u00f3n",
        "settings.gameplay.heal_threshold": "Quickheal",
        "settings.gameplay.heal_threshold_suffix": "umbral",
        "menu.heal.thr.80":             "Principiante",
        "menu.heal.thr.90":             "Aprendiendo",
        "menu.heal.thr.100":            "Equilibrado",
        "menu.heal.thr.110":            "Experimentado",
        "menu.heal.thr.120":            "Experto",
        "settings.audio.master":        "Principal",
        "settings.audio.music":         "M\u00fasica",
        "settings.audio.sfx":           "Efectos",
        "settings.footer":              "[Esc]  Cerrar",

        # --- Help catalog ---
        "help_catalog.title":           "AYUDA Y CONTROLES",
        "help_catalog.tab.exploration": "EXPLORACI\u00d3N",
        "help_catalog.tab.combat":      "COMBATE",
        "help_catalog.tab.shooting":    "DISPARO",
        "help_catalog.tab.aiming":      "APUNTADO",
        "help_catalog.tab.hacking":     "HACKEO",
        "help_catalog.tab.healing":     "CURACI\u00d3N",
        "help_catalog.footer":          "[\u25c4 \u25ba] Cambiar tab   [Esc] Cerrar",

        # Exploration illustration labels
        "help_catalog.expl.icon.container": "Contenedor",
        "help_catalog.expl.icon.ammo":      "Muni\u00f3n",
        "help_catalog.expl.icon.stairs":    "Escaleras",
        "help_catalog.expl.icon.vault":     "B\u00f3veda",

        # Hack node illustration labels
        "help_catalog.hack.node.entry":     "ENTRADA",
        "help_catalog.hack.node.cache":     "DATA CACHE",
        "help_catalog.hack.node.empty":     "VAC\u00cdO",
        "help_catalog.hack.node.ice":       "ICE (oculto)",
        "help_catalog.hack.loot_label":     "Ejemplos de bot\u00edn:",

        # Exploration tab
        "help_catalog.expl.h1":         "MOVIMIENTO",
        "help_catalog.expl.1.1":        "WASD / Flechas \u2014 moverse una casilla; ataca al enemigo adyacente",
        "help_catalog.expl.1.2":        "Cada paso usa un turno \u2014 los enemigos reaccionan",
        "help_catalog.expl.1.3":        "Espacio o . \u2014 esperar (saltar turno)",
        "help_catalog.expl.h2":         "CAMPO DE VISI\u00d3N",
        "help_catalog.expl.2.1":        "Radio de visi\u00f3n: 10 casillas desde tu posici\u00f3n",
        "help_catalog.expl.2.2":        "\u00c1reas exploradas visibles en oscuro \u2014 enemigos no rastreados",
        "help_catalog.expl.h3":         "ESCALERAS Y CONTENEDORES",
        "help_catalog.expl.3.1":        "E \u2014 bajar escaleras o abrir un contenedor",
        "help_catalog.expl.3.2":        "Los contenedores pueden tener objetos, armas o cr\u00e9ditos",
        "help_catalog.expl.3.3":        "Todos los contenedores activan el minijuego de hackeo (si est\u00e1 habilitado)",

        # Combat tab
        "help_catalog.comb.h1":         "COMBATE CUERPO A CUERPO",
        "help_catalog.comb.1.1":        "Muévete hacia un enemigo para atacar (choque)",
        "help_catalog.comb.1.2":        "El movimiento y ataque diagonal est\u00e1n permitidos",
        "help_catalog.comb.1.3":        "F \u2014 atacar al enemigo m\u00e1s cercano al alcance",
        "help_catalog.comb.h2":         "ARMADURA",
        "help_catalog.comb.2.1":        "La armadura reduce el da\u00f1o entrante por su valor defensivo",
        "help_catalog.comb.2.2":        "Se equipa sola; la m\u00e1s fuerte reemplaza a la m\u00e1s d\u00e9bil",
        "help_catalog.comb.2.3":        "Ver armadura equipada en inventario (tecla I)",
        "help_catalog.comb.h3":         "ENEMIGOS",
        "help_catalog.comb.3.1":        "Guardias: atacan cuerpo a cuerpo, patrullan, persiguen al verte",
        "help_catalog.comb.3.2":        "Drones: a distancia, mantienen distancia, enviados por hackeos fallidos",
        "help_catalog.comb.3.3":        "Los enemigos solo reaccionan en l\u00ednea de visi\u00f3n",

        # Shooting tab
        "help_catalog.shoot.h1":        "COMBATE A DISTANCIA",
        "help_catalog.shoot.1.1":       "F \u2014 apuntar y disparar al objetivo seleccionado",
        "help_catalog.shoot.1.2":       "Tab \u2014 cambiar entre enemigos visibles",
        "help_catalog.shoot.1.3":       "R \u2014 recargar arma",
        "help_catalog.shoot.1.4":       "C \u2014 cambiar arma equipada",
        "help_catalog.shoot.h2":        "MUNI\u00c9N",
        "help_catalog.shoot.2.1":       "9mm \u2014 Pistola y subfusil",
        "help_catalog.shoot.2.2":       "Muni\u00f3n fusil \u2014 Fusil",
        "help_catalog.shoot.2.3":       "Cartuchos \u2014 Escopeta",
        "help_catalog.shoot.2.4":       "Muni\u00f3n recogida autom\u00e1ticamente de enemigos y contenedores",
        "help_catalog.shoot.h3":        "ARMAS",
        "help_catalog.shoot.3.1":       "Pistola \u2014 confiable, alcance medio",
        "help_catalog.shoot.3.2":       "Subfusil \u2014 r\u00e1faga de 3, letal de cerca",
        "help_catalog.shoot.3.3":       "Escopeta \u2014 devastadora de cerca, 4 cartuchos",
        "help_catalog.shoot.3.4":       "Fusil \u2014 largo alcance, disparos de precisi\u00f3n",
        "help_catalog.shoot.3.5":       "Espada de energ\u00eda \u2014 solo cuerpo a cuerpo, atraviesa armadura",
        "help_catalog.shoot.3.6":       "Cuchillo de combate \u2014 solo cuerpo a cuerpo, ataque r\u00e1pido de corto alcance",

        # Aiming tab
        "help_catalog.aim.h1":          "C\u00d3MO FUNCIONA EL APUNTADO",
        "help_catalog.aim.1.1":         "Una aguja oscila de un lado a otro en el arco",
        "help_catalog.aim.1.2":         "Pulsa F o haz clic para detener la aguja y disparar",
        "help_catalog.aim.1.3":         "Zona verde = impacto;  fuera de la zona = fallo",
        "help_catalog.aim.1.4":         "Parar cerca del centro = da\u00f1o m\u00e1ximo",
        "help_catalog.aim.1.5":         "La aguja acelera en cada rebote del arco",
        "help_catalog.aim.h2":          "PRECISI\u00d3N Y GOLPES CR\u00cdTICOS",
        "help_catalog.aim.2.1":         "La zona se reduce con la distancia al objetivo",
        "help_catalog.aim.2.2":         "Para la aguja a \u226595% de precisi\u00f3n para CR\u00cdTICO",
        "help_catalog.aim.2.3":         "Cr\u00edtico = da\u00f1o m\u00e1ximo \u2014 el efecto se desbloquea al progresar",
        "help_catalog.aim.h3":          "CONTROLES",
        "help_catalog.aim.3.1":         "F / clic \u2014 detener aguja y disparar",
        "help_catalog.aim.3.2":         "Tab \u2014 cambiar objetivo antes de disparar",
        "help_catalog.aim.3.3":         "Esc \u2014 cancelar; disparos restantes fallan autom\u00e1ticamente",

        # Hacking tab
        "help_catalog.hack.h1":         "CONCEPTOS B\u00c1SICOS DE HACKEO",
        "help_catalog.hack.1.1":        "Muévete a nodos DATA CACHE y entra para extraer bot\u00edn",
        "help_catalog.hack.1.2":        "El temporizador empieza con tu primer movimiento",
        "help_catalog.hack.1.3":        "Recoge todas las cach\u00e9s o espera que acabe el tiempo",
        "help_catalog.hack.h2":         "TIPOS DE NODOS",
        "help_catalog.hack.2.1":        "\u25ba ENTRADA \u2014 tu posici\u00f3n inicial",
        "help_catalog.hack.2.2":        "\u25aa DATA CACHE \u2014 hackea para extraer bot\u00edn",
        "help_catalog.hack.2.3":        "\u25aa VAC\u00cdO \u2014 solo travesia",
        "help_catalog.hack.2.4":        "\u25aa ICE \u2014 trampa oculta, \u00a1parece VAC\u00cdO!",
        "help_catalog.hack.h3":         "EFECTOS ICE",
        "help_catalog.hack.3.1":        "PENALIZACI\u00d3N \u2014 \u22123 segundos del temporizador",
        "help_catalog.hack.3.2":        "DATOS CORRUPTOS \u2014 destruye un nodo no hackeado",
        "help_catalog.hack.3.3":        "ACCESO DENEGADO \u2014 te devuelve, bloquea entrada",
        "help_catalog.hack.h4":         "CONTROLES",
        "help_catalog.hack.4.1":        "WASD / Flechas \u2014 mover al nodo adyacente",
        "help_catalog.hack.4.2":        "Clic de rat\u00f3n \u2014 haz clic en un vecino para mover",
        "help_catalog.hack.4.3":        "Q / Esc \u2014 cancelar extracci\u00f3n / abortar hackeo",

        # Healing tab
        "heal.help.h1":                 "C\u00d3MO FUNCIONA LA CURACI\u00d3N",
        "heal.help.1":                  "Observa dos latidos \u2014 du-dum, du-dum",
        "heal.help.2":                  "Pulsa H en el tercer latido, mant\u00e9n durante la pausa",
        "heal.help.3":                  "Suelta H cuando deber\u00eda sonar el segundo golpe",
        "heal.help.4":                  "Perfecto \u2192 +20%   Fallo \u2192 \u221220%",
        "heal.help.h2":                 "PUNTUACI\u00d3N",
        "heal.help.s1":                 "Perfecto +20%  |  Excelente +10%  |  Bien \u00b10%",
        "heal.help.s2":                 "D\u00e9bil \u221210%  |  Pobre \u221220%",
        "heal.help.s3":                 "Puntos = suma de error de pulsar + soltar",
        "heal.help.h3":                 "CONTROLES",
        "heal.help.key1":               "[H mant\u00e9n] \u2014 pulsar en el latido (contracci\u00f3n)",
        "heal.help.key2":               "[soltar H] \u2014 soltar tras la pausa (relajaci\u00f3n)",
        "heal.help.key3":               "[Esc] \u2014 cancelar curaci\u00f3n",
        "heal.help.key4":               "[F1] \u2014 mostrar/ocultar esta ayuda",

        # Heal overlay runtime strings
        "heal.overlay.title":           "Ritmo card\u00edaco",
        "heal.overlay.watch":           "Observa...",
        "heal.overlay.now":             "\u00a1AHORA!",
        "heal.overlay.hint":            "[H] pulsa y mant\u00e9n en el 3er latido",
        "heal.overlay.perfect":         "\u00a1Perfecto!",
        "heal.overlay.great":           "Excelente",
        "heal.overlay.good":            "Bien",
        "heal.overlay.poor":            "D\u00e9bil",
        "heal.overlay.miss":            "Pobre",
    },
}

# ---------------------------------------------------------------------------
# Initialise from settings.LANGUAGE (done after _STRINGS is defined)
# ---------------------------------------------------------------------------


def _init_from_settings() -> None:
    try:
        from dungeoneer.core import settings  # late import avoids circular dep
        set_language(settings.LANGUAGE)
    except Exception:
        pass


_init_from_settings()
