## Záměr
Chci podpořit pocit, že hráč je agent na cizím území, kde nesmí udělat moc rozruch - rychle tam, rychle ven
## Co heat dělá
Heat se zvyšuje při různých akcích (viz dále). Má určité tresholdy indikující stav facility. Při přechodu na vyšší stupeň se stanou věci, které udělají hru těžší. Při lootování finálního vaultu defakto určuje, kolik kreditů z něj hráč dostane.
## Vizualizace
- Heat musí být dobře vidět - bar v horním menu, jasně indikovaný level (text + barva).
- Bar se snuluje vždy při dosažení next levelu
- Bar neukazuje přesné číslo, jen se pomalu plní
- Level je označený přesně (popis + barva)
- Interně se udržuje celkový kumulovaný počet
- Pokud klesne na nižší level, tak se sníží i level
- Na max heatu (level 5) se bar nenuluje, je stále plný (pokud neklesne pod 5)
## Akce, co zvedají heat
- Boj s nepřáteli (za počet bojových kol)
- Hacking - určitě neúspěšný, něco i za úspěšný - za každý hacknutý uzel
- Lootování finálního vaultu (TBD)
## Pacing
- Efektivní průchod by měl odpovídat cca 2. levelu z 5 možných. Prvnímu, když má hráč štěstí. Třetímu ne, pokud nemá fakt smůlu.
- Pokud se hodně zdržuje a plýtvá, tak zhruba 4. levelu
- Představuju si, že bar (na naplnění levelu) by mohl mít 100 bodů
- Za kolo boje bych dal +1 heat
- Za hacknutý uzel +2 heat
- Za zkažený hack +10 heat
## Dopady heatu
- Posílení nepřátel - silnější nepřátelé (vyšší tier) a / nebo větší patroly (ovlivňuje spawn v nových místnostech) - pořád tam bude nějaké RNG, co hráč potká
- Okamžitý příchod hlídky (nejen při final vaultu), která hráče vidí (hráč bude ale hrát první - oni přijdou v kole nepřátel)
- Méně času na hackování - změnit základní čas o (+2 - heat) - pozor, aby hard byl stále hratelný, možná bude potřeba upravit
- Těžší minihra při lootování finálního vaultu
## Counter measures
- Loot uzel, který snižuje heat o 10 nebo 20