# Metagame — perky, skilly, progrese

> Pracovní nápady. Vše zatím bez finálního balancu — projít poctivě později.

---

## 1. Cyberware & perky

Cyberware dává perky. Buď přes sloty, nebo libovolně kombinovatelné — zatím otevřená otázka.

Perky mohou být **aktivní (A)** nebo **pasivní (P)**. Lze je zapínat a vypínat dle chuti.

### Energie

- Aktivní perky stojí **energii**.
- Postava má zásobu energie na začátek každého runu.
- Energii lze dobíjet na vybraných místech — ale zvyšuje to **alert**.
- Dobíjení je **limitované** (1× na místo? Určité množství na místě? — dořešit).

### Perky — přehled

| Typ | Efekt                                                                                                                      |
| --- | -------------------------------------------------------------------------------------------------------------------------- |
| (A) | **Counteruje efekt ICE** — udělá z ICE uzlu neutral uzel. Musí stihnout během warning zprávy, jinak energie přijde vniveč. |
| (P) | **Bonus při criticalu** — statusy? Lze nakoupit víc, ale vybíráš jen jeden?                                                |
| (P) | Zrychlí ručičku při aimu o 20 %, zvýší damage o 20 %.                                                                      |
| (A) | **Neviditelnost** — stojí energii za každé kolo, zruší se útokem nebo hackem.                                              |
| (A) | **Otevírání tajných chodeb** — stojí energii za použití zvenku.                                                            |
| (P) | **Odemykání zbraní a zbrojí** — bez toho zbroj nefunguje a zbraně mají poloviční dmg nebo přesnost (rozmyslet).            |
| (P) | **Odemknutí výbušnin**.                                                                                                    |
| (A) | **Past** — nastražíš na políčko, kdo do ní vstoupí dostane dmg.                                                            |
| (A) | **Strip armor** — příští zásah sníží armor cíle o 1.                                                                       |
| (P) | **Pohyb a střelba** (aktivní, zadarmo) — provedeš obojí, ale s poloviční přesností.                                        |
| (P) | Vyšší **dohled** o 1.                                                                                                      |
| (A) | **Heal** (5 nebo 10?) — sníží přesnost na příští fight o x % (kumulativně).                                                |
| (P) | Zviditelní loot při hackovací minihře (které náboje, která zbraň, ...) - více levelů (heal, munice, zbraně)                |

Perky mohou mít **více levelů**.

Zbraně umožňují vylepšovat zbraně, pokud ji hráč najde v bedně podruhé, tak se zkombinuje a dá malý bonus (dmg, přesnost nebo podobně) - max level odpovídá max levelu perku

---

## 2. Skilly

Skilly se **odemykají a levelují automaticky za zajímavé akce** — postava postupně expí. EXP nejsou přímo vidět, jen hinty (modrá žárovečka nad hlavou? modrá pluska která vyletí vzhůru?).

### Mechanika levelování

- Každý skill má **5 levelů**.
- Pokud děláš furt stejný typ akce, počet EXP za ni klesá.
- Když uděláš jinou akci, EXP za původní se zase zvednou — systém motivuje k variabilitě.
- Skilly musíš nejprve **odemknout**, pak teprve koupit za kredity.

### Přehled skillů

| Skill               | Jak se odemkne                                               | Pasivní efekt po levelu                             |
| ------------------- | ------------------------------------------------------------ | --------------------------------------------------- |
| **Point blank**     | Zásah ze sousedního pole                                     | 10 % šance na stun při point blank útoku            |
| **Sniper**          | Zásah na maximální vzdálenost                                | +10 % přesnost na max. vzdálenost — nebo dohled o 1 |
| **Melee**           | Melee útok, když máš náboje alespoň v jedné zbrani           | Melee doplňuje životy (1 za 15 dmg)                 |
| **Crit**            | Kritický zásah                                               | Náhodný status na 1 kolo?                           |
| **Precision**       | Dorazit nepřítele zásahem přesně za tolik, kolik mu zbývá HP | Zvýší šanci na loot při precision killu             |
| **From the hip**    | Zásah před tím, než ručička narazí do zdi                    | 5 % šance spustit hned další útok                   |
| **Aiming**          | Zásah až po třetím odražení ručičky od stěny                 | Zpomalení zrychlování ručičky o 10 %                |
| **Close escape**    | Dokončit hack loot uzlu v poslední vteřině a pak utéct       | Hack v poslední vteřině přidá čas (0,2 s)           |
| **Hoarder**         | Vylootit všechny loot uzly a ukončit minihru předčasně       | Při vylootu všeho +20 000 kreditů                   |
| **Hacker**          | Counterovat efekt ICE pomocí perku                           | ICE uzly problikávají (1 uzel)                      |
| **Ghost**           | Melee z neviditelnosti                                       | 10 % šance na instakill při melee z neviditelnosti  |
| **Treasure hunter** | Otevírání tajných chodeb                                     | +10 % nábojů z lootu                                |
| **Hunter**          | Zásah pastí                                                  | Cíl pasti jde 1 kolo pryč od hráče                  |
| **Energic**         | Vyčerpání zásob energie                                      | +10 % dobíjení (bez zvednutí alarmu)                |
| **Stripper**        | Strip armoru                                                 | 1 armor penetration při critu                       |
| **Healer**          | Perfect heal                                                 | Perfect heal dá regeneraci na 1 kolo                |
| **Run and gun**     | Zásah při pohybu                                             | ???                                                 |
| **Under pressure**  | Hack v combat                                                | 10 % šance na loot node navíc                       |
| **Field medic**     | Heal v combat                                                | 5 % šance, že heal nebude stát akci                 |
| **Berserk**         | Zásah pod 5 HP                                               | Při 9 a méně HP: +10 % dmg                          |
| **Get it all**      | Vylootování celého vaultu                                    | ???                                                 |

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
| **Quickshoot**  | Menší přesnost nebo rychlejší ručička | ???                           |


---

## 5. Unikátní zbraně

- Odměna za challenge, nebo malá šance dropu z miniher / bossů.
- **Mírně lepší** než základní zbraně: větší zásobník, přesnost, damage, unikátní efekt.
- **Přetrvávají mezi hrami** (meta-progrese).
