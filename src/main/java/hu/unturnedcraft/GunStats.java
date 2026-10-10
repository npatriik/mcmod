package hu.unturnedcraft;

import com.google.gson.JsonObject;
import java.util.List;

/**
 * Egy fegyver számai. Az értékek az Unturned .dat fájljaiból származnak
 * (pl. Unturned/Bundles/Items/Guns/Colt/Colt.dat); zárójelben az a kulcs áll, amelyikből jönnek.
 *
 * Az adatokat nem kézzel írjuk be: a tools/extract_unturned_assets.py kiolvassa őket a .dat
 * fájlokból, és nyersen (Unturned-egységekben) beírja az unturnedcraft_guns.json fájlba. Ez az
 * osztály olvassa vissza, és itt történik az átváltás Minecraft-egységekre ({@link #fromJson}).
 *
 * @param calibers            milyen kaliberű tárakat fogad (Caliber, Magazine_Calibers)
 * @param defaultMagazine     az alap tár azonosítója; új fegyver ezzel megtöltve jön létre (Magazine)
 * @param range               lőtávolság blokkban; az Unturned méterben számol, 1 méter = 1 blokk (Range)
 * @param automatic           true: nyomva tartott gombra folyamatosan lő (Auto); false: kattintásonként egyet
 * @param fireCooldownTicks   két lövés közti minimális idő Minecraft-tickben (Firerate)
 * @param reloadTicks         az újratöltés ideje tickben (Reload_Time, vagy a Reload hang hossza)
 * @param spreadDegrees       a szórás kúpjának teljes nyílásszöge fokban, csípőből lőve (Spread_Angle_Degrees)
 * @param aimSpreadMultiplier célzáskor ennyivel szorzódik a szórás (Spread_Aim)
 * @param aimInTicks          ennyi tick, mire a fegyver célzásra emelkedik; addig még a csípőszórás él (Aim_In_Duration)
 * @param aimFovMultiplier    célzáskor ennyiszeresére szűkül a látószög; távcsőnél 1 / nagyítás (az irányzék Zoom sora)
 * @param recoilMinDegrees    lövésenként legalább ennyi fokkal rúgja fel a kamerát (Recoil_Min_Y)
 * @param recoilMaxDegrees    lövésenként legfeljebb ennyi fokkal rúgja fel a kamerát (Recoil_Max_Y)
 * @param againstPlayers      sebzés játékosok ellen (Player_Damage, Player_*_Multiplier)
 * @param againstZombies      sebzés zombik ellen (Zombie_Damage, Zombie_*_Multiplier)
 * @param againstAnimals      sebzés állatok ellen (Animal_Damage, Animal_*_Multiplier)
 */
public record GunStats(
        List<Integer> calibers,
        String defaultMagazine,
        double range,
        boolean automatic,
        int fireCooldownTicks,
        int reloadTicks,
        float spreadDegrees,
        float aimSpreadMultiplier,
        int aimInTicks,
        float aimFovMultiplier,
        float recoilMinDegrees,
        float recoilMaxDegrees,
        DamageProfile againstPlayers,
        DamageProfile againstZombies,
        DamageProfile againstAnimals) {

    /** Alapsebzés egy célponttípus ellen (az Unturned 100-as életerő-skáláján), testrészenkénti szorzókkal. */
    public record DamageProfile(float damage, float legMultiplier, float spineMultiplier, float skullMultiplier) {
        static DamageProfile fromJson(JsonObject json) {
            return new DamageProfile(json.get("damage").getAsFloat(), json.get("leg").getAsFloat(),
                    json.get("spine").getAsFloat(), json.get("skull").getAsFloat());
        }
    }

    // ------------------------------------------------------------------------------------
    // Átváltás Unturned-egységekről Minecraft-egységekre
    // ------------------------------------------------------------------------------------

    /** Az Unturnedben mindenkinek 100 életereje van, Minecraftban egy játékosnak 20 (10 szív). */
    public static final float HEALTH_SCALE = 20f / 100f;

    /**
     * Az Unturned a visszarúgás nagy részét magától visszaállítja (Recover_X/Y 0.7 körül).
     * Itt ilyen visszaállás még nincs, ezért csak a negyedét alkalmazzuk.
     */
    public static final float RECOIL_SCALE = 0.25f;

    /** Irányzék nélkül vagy sima (nem nagyító) irányzékkal célozva ennyiszeresére szűkül a látószög. Saját választás. */
    public static final float DEFAULT_AIM_FOV_MULTIPLIER = 0.8f;

    /** Az Unturned másodpercenként 50-szer léptet, a Minecraft 20-szor. */
    public static int unturnedTicksToMinecraft(int unturnedTicks) {
        return Math.max(1, Math.round(unturnedTicks * 20f / 50f));
    }

    /** Másodpercből Minecraft-tick (1 másodperc = 20 tick). */
    public static int secondsToTicks(float seconds) {
        return Math.max(1, Math.round(seconds * 20f));
    }

    /** Egy fegyver beolvasása az unturnedcraft_guns.json egyik bejegyzéséből. */
    public static GunStats fromJson(JsonObject json) {
        float zoom = json.get("sightZoom").getAsFloat();
        return new GunStats(
                GunDefinitions.intList(json.getAsJsonArray("calibers")),
                json.get("defaultMagazine").getAsString(),
                json.get("range").getAsDouble(),
                json.get("automatic").getAsBoolean(),
                unturnedTicksToMinecraft(json.get("firerate").getAsInt()),
                secondsToTicks(json.get("reloadSeconds").getAsFloat()),
                json.get("spreadAngleDegrees").getAsFloat(),
                json.get("spreadAim").getAsFloat(),
                secondsToTicks(json.get("aimInSeconds").getAsFloat()),
                zoom > 1f ? 1f / zoom : DEFAULT_AIM_FOV_MULTIPLIER,
                json.get("recoilMinY").getAsFloat() * RECOIL_SCALE,
                json.get("recoilMaxY").getAsFloat() * RECOIL_SCALE,
                DamageProfile.fromJson(json.getAsJsonObject("players")),
                DamageProfile.fromJson(json.getAsJsonObject("zombies")),
                DamageProfile.fromJson(json.getAsJsonObject("animals")));
    }
}
