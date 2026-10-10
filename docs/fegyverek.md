# Fegyverek és tárak (0.3.0)

Ez a lista a `src/main/resources/unturnedcraft_guns.json` 0.3.0-s állapotából készült. A számok már
Minecraftra vannak átváltva, ugyanúgy, ahogy a `GunStats.java` teszi.

![Minden fegyver és tár](fegyverek.png)

## Fegyverek

- **Lövés/mp:** ennyit enged a fegyver. Automatánál elég nyomva tartani a gombot, a többinél ennyiszer
  kattinthatsz másodpercenként.
- **Zombi: test / fej:** egy találat sebzése életerőpontban, páncél nélkül számolva (a Minecraft zombijának
  20 életereje és 2 páncélja van, a páncél ebből keveset vesz le). Sörétesnél `sörétek száma × egy sörét`.
- **Lőtáv:** blokkban.

| Fegyver | Azonosító | Működés | Alap tár | Lövés/mp | Zombi: test / fej | Lőtáv | Belefér még |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Ace | `ace` | félautomata | `ace_6` (6) | 5 | 11,9 / 21,8 | 100 | nincs |
| Augewehr | `augewehr` | automata, 4× távcső | `ranger_35` (35) | 6,7 | 11,9 / 21,8 | 200 | `military_100`, `military_30`, `military_tracer_20`, `ranger_75`, `swissgewehr_20` |
| Avenger | `avenger` | félautomata | `avenger_13` (13) | 10 | 11,9 / 21,8 | 100 | nincs |
| Devil's Bane | `bane` | automata | `bane_21` (21) | 5 | 6 × 4,8 / 6 × 7,2 | 20 | nincs |
| Bluntforce | `bluntforce` | pumpás | `shells_8` (8) | 1,2 | 6 × 6,4 / 6 × 9,6 | 35 | nincs |
| Bulldog | `bulldog` | automata | `bulldog_45` (45) | 20 | 9 / 16,5 | 90 | nincs |
| Calling Card | `card` | automata | `card_71` (71) | 10 | 11,9 / 21,8 | 125 | nincs |
| Cobra | `cobra` | automata | `cobra_20` (20) | 10 | 11,9 / 21,8 | 80 | `cobra_40` |
| 1911 | `colt` | félautomata | `colt_7` (7) | 10 | 11,9 / 21,8 | 100 | nincs |
| Desert Falcon | `desert_falcon` | félautomata | `desert_falcon_7` (7) | 5 | 15 / 27,5 | 125 | nincs |
| Determinator | `determinator` | félautomata | `shells_8` (8) | 10 | 6 × 5 / 6 × 5 | 45 | nincs |
| Dragonfang | `dragonfang` | automata | `dragonfang_150` (150) | 10 | 3 × 4,6 / 3 × 8,4 | 175 | nincs |
| Eaglefire | `eaglefire` | félautomata | `military_30` (30) | 10 | 11,9 / 21,8 | 200 | `military_100`, `military_tracer_20`, `swissgewehr_20` |
| Ekho | `ekho` | tolózáras | `ekho_7` (7) | 1 | 15 / 27,5 | 300 | nincs |
| Empire | `empire` | automata | `empire_28` (27) | 10 | 11,9 / 21,8 | 160 | nincs |
| Hell's Fury | `fury` | automata (gépágyú) | `fury_250` (250) | 20 | 4 × 3 / 4 × 5,5 | 150 | nincs |
| Fusilaut | `fusilaut` | félautomata | `ranger_35` (35) | 20 | 11,9 / 21,8 | 200 | `military_100`, `military_30`, `military_tracer_20`, `ranger_75`, `swissgewehr_20` |
| Grizzly | `grizzly` | félautomata | `grizzly_5` (5) | 2,5 | 18 / 33 | 300 | nincs |
| Hawkhound | `hawkhound` | tolózáras | `hawkhound_8` (8) | 1 | 11,9 / 21,8 | 200 | nincs |
| Heartbreaker | `heartbreaker` | automata | `military_30` (30) | 6,7 | 11,9 / 21,8 | 200 | `military_100`, `military_tracer_20`, `swissgewehr_20` |
| PDW | `honeybadger` | automata | `military_30` (30) | 10 | 11,9 / 21,8 | 125 | `military_100`, `military_tracer_20`, `swissgewehr_20` |
| Kryzkarek | `kryzkarek` | félautomata | `kryzkarek_12` (12) | 10 | 11,9 / 21,8 | 90 | nincs |
| Luger | `luger` | félautomata | `luger_9` (9) | 20 | 11,9 / 21,8 | 90 | nincs |
| Maschinengewehr | `mp40` | automata | `mp40_32` (32) | 10 | 11,9 / 21,8 | 140 | nincs |
| Maplestrike | `maplestrike` | automata | `military_30` (30) | 10 | 11,9 / 21,8 | 200 | `military_100`, `military_tracer_20`, `swissgewehr_20` |
| Masterkey | `masterkey` | billenőcsöves | `shells_2` (2) | 10 | 8 × 6,4 / 8 × 9,6 | 30 | nincs |
| Matamorez | `matamorez` | automata | `matamorez_17` (17) | 6,7 | 11,9 / 21,8 | 300 | `matamorez_36` |
| Nailgun | `nailgun` | félautomata | `nailgun_20` (20) | 20 | 2,8 / 5,1 | 25 | nincs |
| Nightraider | `nightraider` | automata | `ranger_35` (35) | 10 | 11,9 / 21,8 | 200 | `military_100`, `military_30`, `military_tracer_20`, `ranger_75`, `swissgewehr_20` |
| Nykorev | `nykorev` | automata | `nykorev_200` (200) | 10 | 3 × 4 / 3 × 7,3 | 150 | nincs |
| Peacemaker | `peacemaker` | automata | `peacemaker_50` (50) | 20 | 9 / 16,5 | 100 | nincs |
| Quadbarrel | `quadbarrel` | billenőcsöves | `shells_8` (8) | 10 | 6 × 6,9 / 6 × 10,3 | 20 | nincs |
| Birch Rifle | `rifle_birch` | tolózáras | `rifle_5` (5) | 1 | 11,9 / 21,8 | 175 | nincs |
| Maple Rifle | `rifle_maple` | tolózáras | `rifle_5` (5) | 1 | 11,9 / 21,8 | 200 | nincs |
| Pine Rifle | `rifle_pine` | tolózáras | `rifle_5` (5) | 1 | 11,9 / 21,8 | 225 | nincs |
| Sabertooth | `sabertooth` | félautomata | `sabertooth_10` (10) | 5 | 11,9 / 21,8 | 250 | nincs |
| Sawed-Off | `sawed_off` | billenőcsöves | `shells_2` (2) | 10 | 8 × 10 / 8 × 11 | 20 | nincs |
| Scalar | `scalar` | automata | `scalar_30` (30) | 20 | 11,9 / 21,8 | 100 | nincs |
| Schofield | `schofield` | tolózáras | `schofield_5` (5) | 1 | 11,9 / 21,8 | 200 | nincs |
| Snayperskya | `snayperskya` | félautomata | `snayperskya_7` (7) | 4 | 11,9 / 21,8 | 250 | nincs |
| Sportshot | `sportshot` | félautomata | `sportshot_10` (10) | 10 | 3,8 / 7 | 200 | nincs |
| Swissgewehr | `swissgewehr` | félautomata | `swissgewehr_20` (20) | 10 | 11,9 / 21,8 | 210 | `military_100`, `military_30`, `military_tracer_20` |
| Teklowvka | `teklowvka` | félautomata | `teklowvka_15` (15) | 20 | 11,9 / 21,8 | 80 | nincs |
| Timberwolf | `timberwolf` | tolózáras | `timberwolf_6` (6) | 1 | 15 / 27,5 | 300 | nincs |
| Viper | `viper` | automata | `viper_25` (25) | 10 | 11,9 / 21,8 | 125 | nincs |
| Vonya | `vonya` | félautomata | `vonya_7` (7) | 2,5 | 6 × 5,6 / 6 × 8,4 | 25 | nincs |
| Yuri | `yuri` | automata | `yuri_64` (64) | 20 | 9,6 / 17,6 | 100 | nincs |
| Zubeknakov | `zubeknakov` | automata | `ranger_35` (35) | 10 | 11,9 / 21,8 | 200 | `ranger_75` |

## Tárak

Egy tár abba a fegyverbe való, amelyikkel van közös kalibere. A kaliber az Unturned belső száma, nem valódi
lőszerméret.

| Tár | Azonosító | Lőszer | Sörét lövésenként | Kaliber | Ezekbe a fegyverekbe való |
| --- | --- | --- | --- | --- | --- |
| Ace töltőléc | `ace_6` | 6 | 1 | 6 | `ace` |
| Avenger tár | `avenger_13` | 13 | 1 | 23 | `avenger` |
| Devil's Bane tár | `bane_21` | 21 | 6 | 42 | `bane` |
| Bulldog tár | `bulldog_45` | 45 | 1 | 34 | `bulldog` |
| Calling Card tár | `card_71` | 71 | 1 | 35 | `card` |
| Cobra tár | `cobra_20` | 20 | 1 | 4 | `cobra` |
| Cobra lőszeres doboz | `cobra_40` | 40 | 1 | 4 | `cobra` |
| 1911 tár | `colt_7` | 7 | 1 | 3 | `colt` |
| Desert Falcon tár | `desert_falcon_7` | 7 | 1 | 19 | `desert_falcon` |
| Dragonfang lőszeres doboz | `dragonfang_150` | 150 | 3 | 12 | `dragonfang` |
| Ekho tár | `ekho_7` | 7 | 1 | 36 | `ekho` |
| Empire tár | `empire_28` | 27 | 1 | 41 | `empire` |
| Hell's Fury dobtár | `fury_250` | 250 | 4 | 32 | `fury` |
| Grizzly tár | `grizzly_5` | 5 | 1 | 13 | `grizzly` |
| Hawkhound tár | `hawkhound_8` | 8 | 1 | 7 | `hawkhound` |
| Kryzkarek tár | `kryzkarek_12` | 12 | 1 | 26 | `kryzkarek` |
| Luger tár | `luger_9` | 9 | 1 | 43 | `luger` |
| Maschinengewehr tár | `mp40_32` | 32 | 1 | 40 | `mp40` |
| Matamorez tár | `matamorez_17` | 17 | 1 | 21 | `matamorez` |
| Matamorez lőszeres doboz | `matamorez_36` | 36 | 1 | 21 | `matamorez` |
| Military dobtár | `military_100` | 100 | 1 | 1 | `augewehr`, `eaglefire`, `fusilaut`, `heartbreaker`, `honeybadger`, `maplestrike`, `nightraider`, `swissgewehr` |
| Military tár | `military_30` | 30 | 1 | 1 | `augewehr`, `eaglefire`, `fusilaut`, `heartbreaker`, `honeybadger`, `maplestrike`, `nightraider`, `swissgewehr` |
| Military Tracer tár | `military_tracer_20` | 20 | 1 | 1 | `augewehr`, `eaglefire`, `fusilaut`, `heartbreaker`, `honeybadger`, `maplestrike`, `nightraider`, `swissgewehr` |
| Nailgun tár | `nailgun_20` | 20 | 1 | 28 | `nailgun` |
| Nykorev lőszeres doboz | `nykorev_200` | 200 | 3 | 10 | `nykorev` |
| Peacemaker tár | `peacemaker_50` | 50 | 1 | 24 | `peacemaker` |
| Ranger tár | `ranger_35` | 35 | 1 | 9 | `augewehr`, `fusilaut`, `nightraider`, `zubeknakov` |
| Ranger dobtár | `ranger_75` | 75 | 1 | 9 | `augewehr`, `fusilaut`, `nightraider`, `zubeknakov` |
| Rifle töltőléc | `rifle_5` | 5 | 1 | 17 | `rifle_birch`, `rifle_maple`, `rifle_pine` |
| Sabertooth tár | `sabertooth_10` | 10 | 1 | 22 | `sabertooth` |
| Scalar tár | `scalar_30` | 30 | 1 | 39 | `scalar` |
| Schofield töltőléc | `schofield_5` | 5 | 1 | 5 | `schofield` |
| 20-as sörétes lőszer | `shells_2` | 2 | 8 | 16 | `masterkey`, `sawed_off` |
| 12-es sörétes lőszer | `shells_8` | 8 | 6 | 8 | `bluntforce`, `determinator`, `quadbarrel` |
| Snayperskya tár | `snayperskya_7` | 7 | 1 | 11 | `snayperskya` |
| Sportshot tár | `sportshot_10` | 10 | 1 | 18 | `sportshot` |
| Swissgewehr tár | `swissgewehr_20` | 20 | 1 | 1 | `augewehr`, `eaglefire`, `fusilaut`, `heartbreaker`, `honeybadger`, `maplestrike`, `nightraider`, `swissgewehr` |
| Teklowvka tár | `teklowvka_15` | 15 | 1 | 31 | `teklowvka` |
| Timberwolf tár | `timberwolf_6` | 6 | 1 | 2 | `timberwolf` |
| Viper tár | `viper_25` | 25 | 1 | 25 | `viper` |
| Vonya tár | `vonya_7` | 7 | 6 | 33 | `vonya` |
| Yuri tár | `yuri_64` | 64 | 1 | 27 | `yuri` |
