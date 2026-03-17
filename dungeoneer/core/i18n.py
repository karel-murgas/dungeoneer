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
        "menu.hack_variant":            "HACK VARIANT",
        "menu.hack.grid":               "Grid",
        "menu.hack.classic":            "Classic",
        "menu.aim_minigame":            "AIM MINIGAME",
        "menu.aim_minigame_on":         "ON",
        "menu.aim_minigame_off":        "OFF",
        "menu.hints":                   "[1/2/3] Difficulty   [M] Loot   [A] Aim   [L] Language   [Enter] Start   [Esc] Quit",

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
        "help.desc.shoot":              "Aim (ranged) / Attack nearest (melee)",
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
        "aim.help.crit.2":              "Critical = max weapon damage",
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

        # --- Quit confirm dialog ---
        "quit_confirm.title":           "ABORT RUN",
        "quit_confirm.question":        "Return to main menu?",
        "quit_confirm.confirm":         "[Y / Enter]  Yes",
        "quit_confirm.cancel":          "[N / Esc]   No",

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
        "inv.btn_equip":                "[E] Equip",
        "inv.btn_use":                  "[U] Use",
        "inv.btn_drop":                 "[D] Drop",
        "inv.btn_close":                "[I] Close",

        # --- Weapon picker ---
        "weapon_picker.title":          "SWAP WEAPON",
        "weapon_picker.empty":          "(no weapons in inventory)",
        "weapon_picker.close":          "[C/Esc] Close",
        "weapon_picker.hint":           "  [\u2191\u2193] Navigate   [E/Enter] Equip",

        # --- Game log messages ---
        "log.floor_enter":              "Floor {n} \u2014 infiltrating facility.",
        "log.heal_cancel":              "Heal cancelled.",
        "log.no_exit":                  "No exit here.",
        "log.no_heals":                 "No healing items.",
        "log.full_hp":                  "Already at full health.",
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
        "hack.header.esc_cancel":       "[ESC]  CANCEL EXTRACTION",
        "hack.header.move_start":       "\u2014 MOVE TO START TIMER \u2014",
        "hack.header.esc_abort":        "[ESC]  ABORT HACK",
        "hack.footer.hint":             "W A S D / Arrows  +  Mouse  |  [F1] Help",
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
        "hack.help.ctrl.esc.key":       "ESC",
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
        "menu.hack_variant":            "VARIANTA HACKU",
        "menu.hack.grid":               "M\u0159\u00ed\u017eka",
        "menu.hack.classic":            "Klasick\u00fd",
        "menu.aim_minigame":            "M\u00cd\u0158EN\u00cd",
        "menu.aim_minigame_on":         "ZAP",
        "menu.aim_minigame_off":        "VYP",
        "menu.hints":                   "[1/2/3] Obt\u00ed\u017enost   [M] Loot   [A] M\u00ed\u0159en\u00ed   [L] Jazyk   [Enter] Spustit   [Esc] Ukon\u010dit",

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
        "help.desc.shoot":              "M\u00ed\u0159en\u00ed (st\u0159eln\u00e9) / \u00datok na nejbli\u017e\u0161\u00edho (melee)",
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
        "aim.help.crit.2":              "Kritick\u00fd = maxim\u00e1ln\u00ed po\u0161kozen\u00ed zbran\u011b",
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

        # --- Quit confirm dialog ---
        "quit_confirm.title":           "P\u0158ERU\u0160IT B\u011aH",
        "quit_confirm.question":        "Vr\u00e1tit se do hlavn\u00edho menu?",
        "quit_confirm.confirm":         "[Y / Enter]  Ano",
        "quit_confirm.cancel":          "[N / Esc]   Ne",

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
        "inv.btn_equip":                "[E] Vybavit",
        "inv.btn_use":                  "[U] Pou\u017e\u00edt",
        "inv.btn_drop":                 "[D] Zahodit",
        "inv.btn_close":                "[I] Zav\u0159\u00edt",

        # --- Weapon picker ---
        "weapon_picker.title":          "V\u00ddM\u011aNA ZBRAN\u011a",
        "weapon_picker.empty":          "(\u017e\u00e1dn\u00e9 zbran\u011b v invent\u00e1\u0159i)",
        "weapon_picker.close":          "[C/Esc] Zav\u0159\u00edt",
        "weapon_picker.hint":           "  [\u2191\u2193] Navigace   [E/Enter] Vybavit",

        # --- Game log messages ---
        "log.floor_enter":              "Patro {n} \u2014 infiltrace objektu.",
        "log.heal_cancel":              "L\u00e9\u010den\u00ed zru\u0161eno.",
        "log.no_exit":                  "Zde nen\u00ed v\u00fdchod.",
        "log.no_heals":                 "\u017d\u00e1dn\u00e9 l\u00e9\u010div\u00e9 p\u0159edm\u011bty.",
        "log.full_hp":                  "Pln\u00e9 \u017eivoty.",
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
        "hack.header.esc_cancel":       "[ESC]  ZARU\u0160IT EXTRAKCI",
        "hack.header.move_start":       "\u2014 POHNI SE PRO ZA\u010c\u00c1TEK \u2014",
        "hack.header.esc_abort":        "[ESC]  P\u0158ERU\u0160IT HACK",
        "hack.footer.hint":             "W A S D / \u0161ipky  +  My\u0161  |  [F1] N\u00e1pov\u011bda",
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
        "hack.help.ctrl.esc.key":       "ESC",
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
        "menu.hack_variant":            "VARIANTE HACK",
        "menu.hack.grid":               "Cuadr\u00edcula",
        "menu.hack.classic":            "Cl\u00e1sico",
        "menu.aim_minigame":            "APUNTADO",
        "menu.aim_minigame_on":         "S\u00cd",
        "menu.aim_minigame_off":        "NO",
        "menu.hints":                   "[1/2/3] Dificultad   [M] Saqueo   [A] Apuntado   [L] Idioma   [Enter] Iniciar   [Esc] Salir",

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
        "help.desc.shoot":              "Apuntar (a distancia) / Atacar al m\u00e1s cercano (cuerpo a cuerpo)",
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
        "aim.help.crit.2":              "Cr\u00edtico = da\u00f1o m\u00e1ximo del arma",
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

        # --- Quit confirm dialog ---
        "quit_confirm.title":           "ABANDONAR PARTIDA",
        "quit_confirm.question":        "\u00bfVolver al men\u00fa principal?",
        "quit_confirm.confirm":         "[Y / Enter]  S\u00ed",
        "quit_confirm.cancel":          "[N / Esc]   No",

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
        "inv.btn_equip":                "[E] Equipar",
        "inv.btn_use":                  "[U] Usar",
        "inv.btn_drop":                 "[D] Tirar",
        "inv.btn_close":                "[I] Cerrar",

        # --- Weapon picker ---
        "weapon_picker.title":          "CAMBIAR ARMA",
        "weapon_picker.empty":          "(sin armas en el inventario)",
        "weapon_picker.close":          "[C/Esc] Cerrar",
        "weapon_picker.hint":           "  [\u2191\u2193] Navegar   [E/Enter] Equipar",

        # --- Game log messages ---
        "log.floor_enter":              "Planta {n} \u2014 infiltrando el edificio.",
        "log.heal_cancel":              "Curaci\u00f3n cancelada.",
        "log.no_exit":                  "No hay salida aqu\u00ed.",
        "log.no_heals":                 "No hay objetos de curaci\u00f3n.",
        "log.full_hp":                  "Ya tienes salud completa.",
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
        "hack.header.esc_cancel":       "[ESC]  CANCELAR EXTRACCI\u00d3N",
        "hack.header.move_start":       "\u2014 MU\u00c9VETE PARA INICIAR \u2014",
        "hack.header.esc_abort":        "[ESC]  ABORTAR HACK",
        "hack.footer.hint":             "W A S D / Flechas  +  Rat\u00f3n  |  [F1] Ayuda",
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
        "hack.help.ctrl.esc.key":       "ESC",
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
