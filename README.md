# UnturnedCraft

Unturned-elemek a Minecraftban (Java Edition 26.3, NeoForge 26.3.0.58-beta).
Első darab: az **1911-es pisztoly** ("Colt") és a tára. Jelenlegi verzió: **0.2.0**.

## Mit tud most

| Gomb | Mit csinál |
| --- | --- |
| **Bal klikk** | Lövés. Félautomata: egy kattintás egy lövés, akármeddig tartod a gombot. |
| **Jobb klikk (nyomva tartva)** | Célzás: a pisztoly a szemed elé emelkedik, a kép ránagyít, a szórás a huszadára csökken. |
| **R** | Újratöltés egy `1911 tár` tárgyból (1,5 mp). A gomb átállítható a játék billentyűbeállításai között, az UnturnedCraft csoportban. |

- **Találat:** a golyó azonnal talál (nincs repülő lövedék), ahogy az Unturnedben. Lőtáv: 100 blokk.
- **Sebzés:** az Unturned értékei, a Minecraft 20-as életerejére átszámolva. Fejre több, lábra kevesebb.
  Zombi: 2 testlövés vagy 1 fejlövés.
- **Szórás:** csípőből pontatlan (30 blokkról egy tehenet nagyjából 10-ből 1 lövés talál el), célozva
  pontos. A célzás 0,15 mp alatt "áll be", addig még a csípőszórás él.
- **Célzás közben** nem lehet sprintelni, és a szokásos sebesség 75%-ával mozogsz.
- **Tár:** 7 lövés. Üres fegyverrel a bal klikk csak kattan, és kiírja, melyik gomb az újratöltés.
  Újratölteni bármikor lehet, ha nincs tele a tár. Kreatív módban nem fogy a töltény.
- **Fegyverrel a kézben a bal klikk nem üt és nem tör blokkot.**
- **Receptek:** pisztoly = 4 vasrúd + 1 deszka (`III` / ` IP`), tár = 1 vasrúd + 1 puskapor.

## Hogyan készült

1. **Assetek kinyerése.** A `tools/extract_unturned_assets.py` megnyitja az Unturned
   `Bundles/core.masterbundle` fájlját (ez egy Unity asset bundle), és kiszedi belőle a fegyver
   modelljét, textúráját és hangjait. A modellt `.obj`, a textúrát `.png`, a hangot `.ogg`
   formátumba írja a `src/main/resources/assets/unturnedcraft/` alá.
2. **Statok.** A sebzés, lőtáv, tűzgyorsaság stb. az Unturned sima szöveges `.dat` fájljaiból jön
   (`Bundles/Items/Guns/Colt/Colt.dat`). Ezek a `GunStats.java` aljára vannak átírva.
3. **Viselkedés.** A lövést, a célzást és az újratöltést Javában kellett megírni, mert az
   Unturned kódja C#, és nem vihető át.

## Hogyan működik a fegyver (kliens és szerver)

A Minecraft két félből áll, egyjátékos módban is:

- a **kliens** az, amit látsz és irányítasz (ablak, billentyűk, hang, kamera),
- a **szerver** az, ahol a világ "valójában" van (lények, életerő, tárgyak).

Egyjátékos módban a kettő ugyanabban a programban fut, de külön szálon, és ugyanúgy hálózati
csomagokkal beszélget, mintha két külön gép lenne. Ebből két szabály következik:

1. **Ami számít, az a szerveren történik.** Találat, sebzés, töltényfogyás. Ha ezt a kliens
   döntené el, többjátékos módban csalni lehetne, és mindenki mást látna.
2. **A szerver nem bízik a kliensben.** A kliens csak annyit mondhat: "lőni szeretnék". Hogy tényleg
   lehet-e (van-e fegyver a kézben, van-e töltény, lejárt-e a várakozás), azt a szerver a saját
   adataiból ellenőrzi újra.

### A három gomb három különböző úton jut el a szerverhez

**Jobb klikk (célzás).** Ezt a Minecraft magától elküldi a szervernek, ezért nem kell hozzá saját
csomag. A célzás a beépített "tárgyhasználat" rendszerre épül, ugyanarra, amivel az íjat felhúzod:
amíg nyomod a gombot, a játékos "használja" a tárgyat (`GunItem.use`). Ezt az állapotot a játék
szinkronban tartja a két oldal között, így a szerver mindig tudja, célzol-e (`GunItem.isAiming`).

**Bal klikk (lövés) és R (újratöltés).** A bal klikk a Minecraftban ütést jelent, az R gombot pedig
a játék nem is ismeri, ezért ezeket a kliensen "eltérítjük" (`client/GunInputHandler`), és saját
hálózati csomagot küldünk róluk (`network/FireGunPayload`, `network/ReloadGunPayload`).

### Egy lövés útja

```
KLIENS (amit látsz)                               SZERVER (a világ)

bal klikk
  |
GunInputHandler.onClientTick
  |-- FireGunPayload(pitch, yaw) -------------->  ModNetworking.handleFire
  |                                                 |  ellenőrzés: él? fegyver van a kezében?
  '-- GunItem.fire  (kliensoldali futás)            '-- GunItem.fire  (szerveroldali futás)
        |-- lövéshang azonnal                             |-- lövéshang a többi játékosnak
        |-- várakozás indul (jóslat)                      |-- várakozás indul ----------> kliens
        '-- visszarúgás (kamera)                          |-- vonal a szemtől: blokk? lény?
                                                          |-- sebzés
                                                          '-- töltény -1 ---------------> kliens
```

A `GunItem.fire` tehát **kétszer** fut le. A kliensen azért, hogy a hang és a visszarúgás azonnal
megtörténjen, ne a szerver válaszára várva; ezt hívják kliensoldali jóslásnak (prediction). A
szerveren azért, mert a lövés ott történik meg igazából. A töltényszámot és a várakozási időt a
szerver küldi vissza, a kliens a sajátját ehhez igazítja.

A csomagban benne van a nézés iránya is. A szerver ugyanis a játékos forgásáról csak tickenként
(másodpercenként 20-szor) kap hírt, a kattintás pedig két frissítés közé is eshet; így a golyó
pontosan arra megy, amerre a kattintás pillanatában néztél.

### Miért félautomata

A `GunInputHandler` minden kliens-tick elején megkérdezi a játéktól, hányszor **nyomták le** a bal
gombot az előző tick óta (`consumeClick`), nem azt, hogy éppen le van-e nyomva. Egy lenyomás egy
lövés. A `GunStats.automatic` kapcsoló már benne van a kódban a későbbi sorozatlövő fegyverekhez:
azoknál az is elég lesz, ha a gomb le van nyomva, a tempót pedig a várakozási idő adja.

### A célzás nézete

Kétféle modell-leírás tartozik a pisztolyhoz, és az `items/colt.json` választ közülük aszerint, hogy
a játékos éppen használja-e a tárgyat (`minecraft:using_item`):

- `models/item/colt.json`: a szokásos tartás,
- `models/item/colt_aiming.json`: célzás. Ez a `colt.json`-ból örököl mindent, csak a belső nézet
  eltolását írja felül.

Az eltolás nem találomra készült. Az Unturned fegyvermodelljeiben van egy `View` nevű segédpont: oda
teszi az Unturned a kamerát célzáskor. A `colt_aiming.json` úgy tolja el a modellt, hogy ez a pont
pontosan a szemedbe essen, így az irányzék a célkereszt alá kerül. (A segédpontok helyét a
`tools/extract_unturned_assets.py` futás közben kiírja.) A ránagyítást a `GunInputHandler.onComputeFov`
adja: célzáskor a látószög a 0,8-szorosára szűkül.

## Mi hol van

| Fájl | Mire való |
| --- | --- |
| `src/main/java/hu/unturnedcraft/UnturnedCraft.java` | A mod belépési pontja (mindkét oldalon) |
| `.../ModItems.java` | A tárgyak listája és a kreatív menü füle |
| `.../GunItem.java` | A fegyver működése: célzás, lövés, találat, sebzés, újratöltés |
| `.../GunStats.java` | Egy fegyver számai (az Unturned `.dat` fájlból) |
| `.../ModSounds.java`, `ModDataComponents.java`, `ModDamageTypes.java` | Hangok, a töltényszám tárolása, a "golyó" sebzéstípus |
| `.../network/FireGunPayload.java`, `ReloadGunPayload.java` | A két saját hálózati csomag |
| `.../network/ModNetworking.java` | A csomagok bejelentése és szerveroldali kezelése |
| `.../client/UnturnedCraftClient.java` | A mod kliensoldali belépési pontja |
| `.../client/GunInputHandler.java` | Bal klikk és R figyelése, az ütés letiltása, ránagyítás |
| `src/main/resources/assets/unturnedcraft/items/*.json` | Melyik modell-leírás tartozik a tárgyhoz (a pisztolynál: célzol-e) |
| `.../models/item/*.json` | A modell és az, **hogyan áll kézben** (`display` rész) |
| `.../models/item/*.obj`, `*.mtl`, `textures/item/*.png`, `sounds/` | Az Unturnedből kinyert assetek |
| `.../sounds.json`, `lang/hu_hu.json`, `lang/en_us.json` | Hangok bekötése, feliratok, a billentyű neve |
| `src/main/resources/data/` | Receptek, a sebzéstípus és a címkéi |
| `tools/extract_unturned_assets.py` | Az asset-kinyerő |

A `client` csomagra külön szabály vonatkozik: ami benne van, az csak a játék kliensén töltődik be.
A csomagon kívüli kód (pl. a `GunItem`) ezért **nem hivatkozhat** rá, különben egy dedikált szerver
összeomlana, mert ott nincs billentyűzet, képernyő és kamera.

## Ha rosszul áll a pisztoly a kézben

A `models/item/colt.json` `display` részében minden nézetnek van egy forgatása (`rotation`, fok),
eltolása (`translation`, 1/16 blokk) és mérete (`scale`):

- `firstperson_righthand`: belső nézet
- `thirdperson_righthand`: külső nézet (F5)
- `gui`: hotbar és inventory
- `ground`: eldobva a földön
- `fixed`: item frame-ben

A célzás belső nézete külön fájlban van: `models/item/colt_aiming.json`.

Írd át a számokat, és nézd meg az eredményt. (Fejlesztői futtatásban, `gradlew runClient`, elég
az F3+T a játékban, nem kell újraindítani.)

## Buildelés

Kell hozzá JDK (17 vagy újabb; a 25-öst a Gradle magától letölti a fordításhoz), és az első
futás sok mindent letölt, ezért percekig tarthat. A mod mappájában, parancssorból:

```
gradlew build
```

A kész mod a `build\libs\unturnedcraft-<verzió>.jar` (most `unturnedcraft-0.2.0.jar`). Ezt kell
bemásolni ide: `%APPDATA%\.minecraft\mods\`, aztán a launcherben a **NeoForge** profillal indítani.

**Figyelj rá, hogy a `mods` mappában a modból csak egy változat legyen.** Ha verziót váltasz (a
`gradle.properties` `mod_version` sora), a jar neve is megváltozik, és a régit törölni kell,
különben a játék kétszer találja meg ugyanazt a modot, és hibával leáll.

Gyors kipróbáláshoz másolgatás nélkül: `gradlew runClient` (külön tesztjátékot indít a moddal).

## Új fegyver hozzáadása

1. `tools/extract_unturned_assets.py`: új bejegyzés az `ITEMS` listába, majd futtasd újra.
2. `GunStats.java`: új `GunStats` a fegyver `.dat` fájljának számaival.
3. `ModSounds.java` és `sounds.json`: a fegyver hangjai.
4. `ModItems.java`: a fegyver és a tára regisztrálása (a Colt mintájára).
5. `items/<név>.json`, `models/item/<név>.json` és `models/item/<név>_aiming.json` a Colt fájljainak
   másolásával; a célzó nézet eltolását a fegyver `View` segédpontjából kell kiszámolni.
6. `lang/*.json`: a fegyver neve.

A kezelést (bal klikk, jobb klikk, R) nem kell újra megírni: az minden `GunItem`-re érvényes.

## Ismert egyszerűsítések

- Újratöltéskor a tár egész darabként fogy el: ha 3 tölténnyel a fegyverben töltesz újra, az a 3
  elvész (az Unturnedben a félig üres tár visszakerül a táskába).
- A célzó nézetre váltás azonnali, nincs átmenet-animáció; a ránagyítás viszont folyamatos.
- A visszarúgás csak felrántja a kamerát, magától nem áll vissza, ezért az Unturned értékének a
  negyede.
- Nincs torkolattűz, hüvelykidobás és újratöltés-animáció.
- Külső nézetben (F5) a kar nem emelkedik fel célzáskor.
- A fegyver nem kopik (az Unturnedben igen).

## Változások

**0.2.0**
- Unturned-szerű kezelés: bal klikk lövés, jobb klikk célzás, R újratöltés.
- Valódi félautomata tüzelés.
- Célzó nézet az Unturned `View` pontja alapján, ránagyítással.
- A szórás a célzástól függ (korábban a guggolástól).
- Újratölteni nem csak üres fegyverrel lehet; az üres fegyver nem tölt újra magától.
- Fegyverrel a kézben a bal klikk nem üt és nem tör blokkot.

**0.1.0**
- Az 1911 pisztoly és a tára: modell, textúra, hangok és statok az Unturnedből.

## Fontos

Az Unturned modelljei, textúrái és hangjai a Smartly Dressed Games tulajdonai. Saját gépen, saját
használatra rendben van, de ezekkel a fájlokkal együtt **ne tedd közzé** a modot.
