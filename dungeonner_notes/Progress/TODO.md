## Final vault
- [x] Fix exploration tutorialu
- [x] Check, že do vaultu nevlezu během fightu - fixnout
- [x] Fixnout heartbeat
- [x] Vyvážit drift
- [x] Test spawnu nepřátel
- [x] Test hudby v real vaultu - furt tiché
- [x] Test při různých heatech
- [x] Test, že vylootovat není automatika (lze zpomalit drain)
- [x] Fix toho, že nepřátelé co nemohou útočit, někdy nic nedělají (místo obejití překážky - jdou na jediné konkrétní místo)
- [x] Fix toho, že minihra začíná mimo střed (asi oddriftuje před začátkem) a naopak se resetuje při přerušení
- [x] Do overlaye dát instrukce (W/S nahoru/dolů pro udržení drainu v optimu)
- [ ] Vyzkoušet vault v reálné hře i s únikem
- [x] Kolik dává vault? Optimalizováno na cca 500 kreditů...jinak bychom museli zpomalit, kolik se čerpá za vteřinu...- nechat na rebalanc
## Next steps##
- [x] Main menu
- [x] Ukládání hry
- [x] Po spuštění hry začít v menu
- [ ] Při změně heat levelu notifikace (přidat číslo heat levelu ke jménu)
- [x] Nápověda na final vault píše, že lze ukončit mezerníkem, ale nelze
- [ ] Když při vstupu do dungu vidíš nepřítele, zobraz tutoriál pro boj hned po tutoriálu na pohyb (a i bez tutorialu hoď notifikaci na zpozorování ještě před tím, než se hnu)
- [ ] Rychlý pohyb se zdá, že se zablokuje už při spawnu nepřítele (tj. ještě před tím, než ho vidím a začne bojová scéna) - než vyletí vykřičník - ten jde až po dalším pohybu
- [ ] Přepnout default na novou grafiku
- [ ] Nechat Clauda dopracovat perky včetně balancu
- [ ] Rozdělit perky na ty, co jsou už implementovat a ty, ke kterým chybí feature (granáty, tajné chodby)
- [ ] Nechat Clauda udělat plán pro perky, které lze nasadit teď
- [ ] Implementovat
- [ ] Připravit features k perkům, které ještě nejsou
- [ ] Implementovat featury
- [ ] Implementovat perky
## Úklid
- [ ] Odstranit nepoužívané kusy kódu (např. menší mapa)
- [ ] Reduce complexity / simplify / deduplicate / check consistency
- [ ] Create most usefull documentation for you, so you don't need to read to much of a code (to save context)
- [ ] Check conventions (if there are none, create them and then update the code)
- [ ] Update claude.md to always keep conventions & consistency, simplify if possible, document for you
- [ ] Do claude.md dát pokyny, aby plán implementoval jen jeden krok na 1 session a jinak hlásil, že mám otevřít novou
- [ ] Do claude.md dát, aby v případě, že je jeho kontext k tasku málo relevantní (a stejně by si načítal nový) tak místo načítání kontextu navrhnout novou session
- [ ] Plány (z planning mode) zapisuj do složky v projektu. Krok po kroku oddělený, aby ses v nich snadno vyznal (kde končí a kde začíná)
- [ ] Když děláš úkol, který je větší, kroky si zapiš do plánu a pak na ně aplikuj logiku "1 task na session"
- [ ] Ke krokům plánu si piš potřebný kontext / kde ho najdeš, aby nová session nemusela načítat vše, ale jen relevantní data
- [ ] Plán si udržuj stejný (kvůli cachování), informace o stavu si ukládej bokem

- [ ] Přejít na agentní flow - přepsat komplet claude.md a věci kolem toho. Ušetříme kontext.

- [ ] `showThinkingSummaries: true`