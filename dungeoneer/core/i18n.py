"""Minimal localisation module.

Usage::

    from dungeoneer.core.i18n import t, set_language
    set_language("cs")          # switch at runtime (e.g. from main menu)
    label = t("help.title")     # returns localised string

Supported languages: "en" (default), "cs".
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
        "help.desc.shoot":              "Attack nearest visible enemy (melee or ranged)",
        "help.key.reload":              "R",
        "help.desc.reload":             "Reload weapon",

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

        # --- HUD hint ---
        "hud.help_hint":                "[F1] Help",
    },

    "cs": {
        # --- Help screen ---
        "help.title":                   "NÁPOVĚDA",
        "help.footer":                  "[F1 / Esc / Enter]  Zavřít",

        "help.section.movement":        "POHYB & AKCE",
        "help.section.combat":          "BOJ",
        "help.section.items":           "PŘEDMĚTY",
        "help.section.general":         "OBECNÉ",

        "help.key.wasd":                "WASD / Šipky",
        "help.desc.wasd":               "Pohyb — nebo útok na sousedního nepřítele",
        "help.key.wait":                "Space / .",
        "help.desc.wait":               "Čekání (přeskočení tahu)",
        "help.key.interact":            "E",
        "help.desc.interact":           "Schody dolů / otevřít kontejner",

        "help.key.shoot":               "F",
        "help.desc.shoot":              "Útok na nejbližšího viditelného nepřítele (na blízko i na dálku)",
        "help.key.reload":              "R",
        "help.desc.reload":             "Přebití zbraně",

        "help.key.heal":                "H",
        "help.desc.heal":               "Rychlé léčení (nejlepší dostupný item)",
        "help.key.inventory":           "I",
        "help.desc.inventory":          "Inventář",
        "help.key.swap":                "C",
        "help.desc.swap":               "Výměna zbraně",

        "help.key.help":                "F1",
        "help.desc.help":               "Tato nápověda",
        "help.key.escape":              "Esc",
        "help.desc.escape":             "Zavřít menu / Ukončit hru",

        # --- HUD hint ---
        "hud.help_hint":                "[F1] Nápověda",
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
