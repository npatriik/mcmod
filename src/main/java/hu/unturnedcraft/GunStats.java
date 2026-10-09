package hu.unturnedcraft;

/**
 * Egy fegyver számai. Az értékek az Unturned .dat fájljaiból származnak
 * (pl. Unturned/Bundles/Items/Guns/Colt/Colt.dat); zárójelben az a kulcs áll, amelyikből jönnek.
 *
 * Új fegyverhez elég egy új GunStats-ot felvenni a fájl aljára, és regisztrálni a ModItems-ben.
 *
 * @param magazineSize        hány töltény fér a tárba (a tár .dat fájljában: Amount)
 * @param range               lőtávolság blokkban; az Unturned méterben számol, 1 méter = 1 blokk (Range)
 * @param automatic           true: nyomva tartott gombra folyamatosan lő (Auto); false: kattintásonként egyet (Semi)
 * @param fireCooldownTicks   két lövés közti minimális idő Minecraft-tickben (Firerate)
 * @param reloadTicks         az újratöltés ideje tickben; az Unturned Reload hangjának hossza
 * @param spreadDegrees       a szórás kúpjának teljes nyílásszöge fokban, csípőből lőve (Spread_Angle_Degrees)
 * @param aimSpreadMultiplier célzáskor ennyivel szorzódik a szórás (Spread_Aim)
 * @param aimInTicks          ennyi tick, mire a fegyver célzásra emelkedik; addig még a csípőszórás él (Aim_In_Duration)
 * @param recoilMinDegrees    lövésenként legalább ennyi fokkal rúgja fel a kamerát (Recoil_Min_Y)
 * @param recoilMaxDegrees    lövésenként legfeljebb ennyi fokkal rúgja fel a kamerát (Recoil_Max_Y)
 * @param againstPlayers      sebzés játékosok ellen (Player_Damage, Player_*_Multiplier)
 * @param againstZombies      sebzés zombik ellen (Zombie_Damage, Zombie_*_Multiplier)
 * @param againstAnimals      sebzés állatok ellen (Animal_Damage, Animal_*_Multiplier)
 */
public record GunStats(
        int magazineSize,
        double range,
        boolean automatic,
        int fireCooldownTicks,
        int reloadTicks,
        float spreadDegrees,
        float aimSpreadMultiplier,
        int aimInTicks,
        float recoilMinDegrees,
        float recoilMaxDegrees,
        DamageProfile againstPlayers,
        DamageProfile againstZombies,
        DamageProfile againstAnimals) {

    /** Alapsebzés egy célponttípus ellen (az Unturned 100-as életerő-skáláján), testrészenkénti szorzókkal. */
    public record DamageProfile(float damage, float legMultiplier, float spineMultiplier, float skullMultiplier) {}

    /** Az Unturnedben mindenkinek 100 életereje van, Minecraftban egy játékosnak 20 (10 szív). */
    public static final float HEALTH_SCALE = 20f / 100f;

    /** Az Unturned másodpercenként 50-szer léptet, a Minecraft 20-szor. */
    public static int unturnedTicksToMinecraft(int unturnedTicks) {
        return Math.max(1, Math.round(unturnedTicks * 20f / 50f));
    }

    /** Másodpercből Minecraft-tick (1 másodperc = 20 tick). */
    public static int secondsToTicks(float seconds) {
        return Math.max(1, Math.round(seconds * 20f));
    }

    /**
     * Az Unturned a visszarúgás nagy részét magától visszaállítja (Recover_X/Y 0.7).
     * Itt ilyen visszaállás még nincs, ezért csak a negyedét alkalmazzuk.
     */
    public static final float RECOIL_SCALE = 0.25f;

    // ------------------------------------------------------------------------------------
    // 1911 ("Colt") -- Bundles/Items/Guns/Colt/Colt.dat és Bundles/Items/Magazines/Colt_7/
    // ------------------------------------------------------------------------------------
    public static final GunStats COLT = new GunStats(
            7,                                    // Amount 7
            100.0,                                // Range 100
            false,                                // Semi (nincs Auto sor a .dat fájlban)
            unturnedTicksToMinecraft(4),          // Firerate 4
            secondsToTicks(1.44f),                // Reload.mp3: 1,44 mp
            8.53f,                                // Spread_Angle_Degrees 8.53
            0.05f,                                // Spread_Aim 0.05
            secondsToTicks(0.15f),                // Aim_In_Duration 0.15
            10f * RECOIL_SCALE,                   // Recoil_Min_Y 10
            13f * RECOIL_SCALE,                   // Recoil_Max_Y 13
            new DamageProfile(24f, 0.6f, 0.8f, 1.1f),   // Player_Damage 24, Leg 0.6, Spine 0.8, Skull 1.1
            new DamageProfile(99f, 0.3f, 0.6f, 1.1f),   // Zombie_Damage 99, Leg 0.3, Spine 0.6, Skull 1.1
            new DamageProfile(24f, 0.6f, 0.8f, 1.1f));  // Animal_Damage 24, Leg 0.6, Spine 0.8, Skull 1.1
}
