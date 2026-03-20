---
name: Safe characters for pygame font rendering
description: Which Unicode characters are safe vs. broken in Consolas/SysFont — recurring rendering issue
type: feedback
---

Všechny fonty v projektu jsou `pygame.font.SysFont("consolas", ...)`. Consolas pokrývá **Windows-1252 + základní latinku**, ale běžně NEOBSAHUJE široké Unicode symboly.

**Why:** Opakovaně narážíme na broken/prázdné čtverce místo znaku (▶, →, ←, …). Komentář v kódu to explicitně zmiňuje: *"font ▶ unreliable"*.

**How to apply:** Před použitím znaku v `.render()` zkontroluj, zda padá do bezpečné skupiny. Pokud ne, použij ASCII alternativu nebo nakresli tvar přes `pygame.draw`.

## Bezpečné (Consolas je má jistě)
- Veškerý ASCII: `A-Z a-z 0-9 ! @ # $ % ^ & * ( ) - _ = + [ ] { } | ; : ' " , . < > / ? \ ~`
- Základní latin-1 (U+00A0–U+00FF): `é ě š č ž ý á í ú ů ñ ü ö` atd. — potřebné pro i18n
- Běžná interpunkce: `-`, `—` (U+2014 em-dash), `…` (U+2026 ellipsis) — tyto fungují v Consolas

## Nespolehlivé / rozbité v Consolas
| Znak | Kód | Alternativa |
|------|-----|-------------|
| `▶` | U+25B6 | `>>` nebo `pygame.draw.polygon` |
| `◀` | U+25C0 | `<<` nebo polygon |
| `▲` `▼` | U+25B2/25BC | `^` `v` nebo polygon |
| `→` `←` `↑` `↓` | U+2192… | `->` `<-` nebo polygon |
| `●` `○` `■` `□` | U+25CF… | `pygame.draw.circle/rect` |
| Box-drawing znaky | U+2500… | `pygame.draw.line/rect` |

## Pravidlo
Pokud kreslíš ikonu nebo dekorativní symbol — **vždy použij `pygame.draw.*`**, ne font.
Font je pouze pro text (písmena, číslice, interpunkce).
