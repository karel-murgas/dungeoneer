# Metagame — perky, skilly, progrese

> Pracovní nápady. Vše zatím bez finálního balancu — projít poctivě později.

---

## 1. Cyberware (perky)

Cyberware dává perky. Buď přes sloty, nebo libovolně kombinovatelné — zatím otevřená otázka.

Perky mohou být **aktivní (A)** nebo **pasivní (P)**. Lze je zapínat a vypínat dle chuti.

### Energie

- Aktivní perky stojí **energii**.
- Postava má zásobu energie na začátek každého runu (100).
- Energii lze dobíjet na náhodně spawnovaných místech (ve stěně chodeb) — ale zvyšuje to **heat**.
- Dobíjení je **limitované** (1× na místo? Určité maximální množství na místě? — dořešit) a nejde vždy o plné dobití
- Aktivní perky by bez dobíjení mělo být možné použít několikrát za běh (rámcově 3-5, dle perku), dobíjení počet použití zvýší za cenu vyšího heatu.
- Hráč by měl řešit volbu, zda dobíjet nebo držet nízký heat
- Má mít hráč kontrolu nad tím, kolik dobije? (Nedobít třeba vše)

### Perky — přehled

| Cyberware                          | Typ | Cena | Efekt                                                                                                                                                                                                |               |
| ---------------------------------- | --- | ---- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------- |
| Neuronová ochrana (mozek)          | (A) | 10   | **Zabrání efektu ICE** — udělá z ICE uzlu neutral uzel. Musí se ale stihnout aktivovat během warning zprávy, jinak energie přijde vniveč. 2 levely, kadžý umožňuje 1 použití v rámci stejné minihry. | Je hra ready? |
| Smartlink (oči)                    | (P) |      | **Bonus při criticalu - střelba**  — Dává na 1 kolo stun                                                                                                                                             | Ano           |
| Svalové implantáty (ruce)          | (P) |      | **Bonus při criticalu - melee**  — Dává krvácení / zkrat (organiční vs mechaničtí nepřátelé) ve výši 30% původního zranění za kolo                                                                   | Ano           |
| Skener citlivých míst (oči)        | (P) |      | **Zrychlí ručičku** při aimu o 20 %, **zvýší damage** o 20 %.                                                                                                                                        | Ano           |
| Chameleoní kůže (tělo)             | (A) |      | **Neviditelnost** — stojí energii za každé kolo, zruší se útokem nebo hackem.                                                                                                                        | Ano           |
| Přepěťové kontakty na dlani (ruce) | (A) |      | **Otevírání tajných chodeb** — stojí energii za použití zvenku.                                                                                                                                      | Ne            |
| Zesílení kostry (tělo)             | (P) |      | **Odemknutí zbroje** — bez toho zbroj nejde obléci                                                                                                                                                   | Ano           |
| Protokol samopalu (mozek)          | (P) |      | **Odemknutí SMG** — bez toho má SMG poloviční přesnost; 2. a 3. level umožnují vylepšování zbraně v rámci běhu                                                                                       | Ano           |
| Protokol brokovnice (mozek)        | (P) |      | **Odemknutí brokovnice** — bez toho má brokovnice poloviční dmg; 2. a 3. level umožnují vylepšování zbraně v rámci běhu                                                                              | Ano           |
| Protokol pušky (mozek)             | (P) |      | **Odemknutí pušky** — bez toho má puška poloviční dmg; 2. a 3. level umožnují vylepšování zbraně v rámci běhu                                                                                        | Ano           |
| Protokol energomeče (mozek)        | (P) |      | **Odemknutí energomeče** — bez toho má energomeč poloviční dmg; 2. a 3. level umožnují vylepšování zbraně v rámci běhu                                                                               | Ano           |
| Mechanické rameno (ruka)           | (P) |      | **Odemknutí granátů** — Bez toho nejdou použít                                                                                                                                                       | Ne            |
| Schrána ve stehně (nohy)           | (A) |      | **Past** — nastražíš na políčko, kdo do ní vstoupí dostane dmg.                                                                                                                                      | Ne            |
| Kompenzátory zpětného rázu (ruka)  | (A) |      | **Strip armor** — příští zásah sníží armor cíle o 1. Má 2 levely.                                                                                                                                    | Ano           |
| Reflexní vlákna (nohy)             | (A) | 0    | **Pohyb a střelba** (aktivní, zadarmo) — provedeš obojí, ale s poloviční přesností.                                                                                                                  | Ano           |
| Elektronické čočky (oči)           | (P) |      | Vyšší **dohled** o 1.                                                                                                                                                                                | Ano           |
| Nanoboti (tělo)                    | (A) |      | **Heal** (5 nebo 10?) — sníží přesnost na příští fight o x % (kumulativně).                                                                                                                          | Ano           |
| Analytický okruh (mozek)           | (P) |      | **Network scan** Zviditelní loot při hackovací minihře (které náboje, která zbraň, ...) - více levelů (1. = heal, 2. = munice, 3. = zbraně)                                                          | Ano           |


Některé perky mohou mít **více levelů**.

Zbraňové perky umožňují vylepšovat zbraně, pokud ji hráč najde v bedně podruhé, tak se zkombinuje s tou co už má a dá malý bonus (dmg, přesnost nebo podobně) - max level zbraně odpovídá max levelu perku.

Pokud hráč equipne zbraň, kterou neovládá, bude na to upozorněn (tutorial + zbraň nějak vizuálně + textově odlišená).

Pokud se pokusí equipnout armor nebo granát bez příslušného perku, hra jej upozorní, že pro tu akci musí mít perk.

---

## 2. Skilly

Skilly se **odemykají a levelují automaticky za zajímavé akce** — postava postupně expí. EXP nejsou přímo vidět, jen hinty (modrá žárovečka nad hlavou? modrá pluska která vyletí vzhůru?).

### Mechanika levelování

- Každý skill má **5 levelů**.
- Pokud děláš furt stejný typ akce, počet EXP za ni klesá.
- Když uděláš jinou akci, EXP za původní se zase zvednou — systém motivuje k variabilitě.
- Skilly musíš nejprve **odemknout** za expy, pak teprve koupit za kredity.

### Přehled skillů

| Skill               | Jak se odemkne                                                    | Pasivní efekt po levelu                             |
| ------------------- | ----------------------------------------------------------------- | --------------------------------------------------- |
| **Point blank**     | Zásah ze sousedního pole                                          | 10 % šance na stun při point blank útoku            |
| **Sniper**          | Zásah na maximální vzdálenost                                     | +10 % přesnost na max. vzdálenost — nebo dohled o 1 |
| **Melee**           | Melee útok, když máš náboje alespoň v jedné zbrani                | Melee doplňuje životy (1 za 15 dmg)                 |
| **Crit**            | Kritický zásah                                                    | Náhodný status na 1 kolo?                           |
| **Precision**       | Dorazit nepřítele zásahem přesně za tolik, kolik mu zbývá HP      | Zvýší šanci na loot při precision killu             |
| **From the hip**    | Zásah před tím, než ručička narazí do zdi                         | 5 % šance spustit hned další útok                   |
| **Aiming**          | Zásah až po třetím odražení ručičky od stěny                      | Zpomalení zrychlování ručičky o 10 %                |
| **Close escape**    | Dokončit hack loot uzlu v poslední vteřině a pak utéct            | Hack v poslední vteřině přidá čas (0,2 s)           |
| **Hoarder**         | Vylootit všechny loot uzly a ukončit minihru předčasně            | Při vylootu všeho +20 000 kreditů                   |
| **Hacker**          | Counterovat efekt ICE pomocí perku                                | ICE uzly problikávají (1 uzel)                      |
| **Ghost**           | Melee z neviditelnosti                                            | 10 % šance na instakill při melee z neviditelnosti  |
| **Treasure hunter** | Otevírání tajných chodeb                                          | +10 % nábojů z lootu                                |
| **Hunter**          | Zásah pastí                                                       | Cíl pasti jde 1 kolo pryč od hráče                  |
| **Energic**         | Vyčerpání zásob energie                                           | +10 % dobíjení (bez zvednutí alarmu)                |
| **Stripper**        | Strip armoru                                                      | 1 armor penetration při critu                       |
| **Healer**          | Perfect heal                                                      | Perfect heal dá regeneraci na 1 kolo                |
| **Run and gun**     | Zásah při pohybu                                                  | ???                                                 |
| **Under pressure**  | Hack v combat                                                     | 10 % šance na loot node navíc                       |
| **Field medic**     | Heal v combat                                                     | 5 % šance, že heal nebude stát akci                 |
| **Berserk**         | Zásah pod 5 HP                                                    | Při 9 a méně HP: +10 % dmg                          |
| **Get it all**      | Vylootování celého vaultu                                         | ???                                                 |
| **Cautious**        | Odejití z hacking minihry před půlkou času, když ještě zbývá loot | Při cautious hacku se snižuje heat o 1              |
| **Overheal**        | Heal by vyléčil víc, než může                                     | Healovat je možné o 1 nad maximum                   |
| **Last bullet**     | Vyprázdnění celého zásobníku                                      | 5%, že přebití nebude stát akci                     |

---

## 3. Nákupy za kredity

Skilly i perky se kupují za **kredity**. Skilly nejprve odemknout, pak koupit. Perky dostupné od začátku, různá cena.

### Věci na run

- Zbraň na začátek
- Lékárnička
- … (limitovaný počet)

### Možné rozšíření

- Ovlivňování lootu — jaké zbraně víc padají?
- Nové typy uzlů v hackování?

---

## 4. Challenges

Hráč si může nakoupit challenge do runu. Jsou **dvojsečné** — komplikují run, ale dávají odměnu nebo bonus.

### Odměny za challenges

- Rychlejší levelení relevantních skillů
- Unikátní zbraň (mírně lepší než základní)

### Přehled challenges

| Challenge       | Nevýhoda                              | Výhoda                        |
| --------------- | ------------------------------------- | ----------------------------- |
| **Glass canon** | Míň HP                                | Víc damage                    |
| **Crowded**     | Víc nepřátel                          | Víc nábojů                    |
| **Commando**    | Jen nůž a pistole                     | Nepřátelé mají kratší dostřel |


---

## 5. Unikátní zbraně

- Odměna za challenge, nebo malá šance dropu z miniher / bossů.
- **Mírně lepší** než základní zbraně: větší zásobník, přesnost, damage, unikátní efekt.
- **Přetrvávají mezi hrami** (meta-progrese).
