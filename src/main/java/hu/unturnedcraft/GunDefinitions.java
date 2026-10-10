package hu.unturnedcraft;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import net.minecraft.world.item.Rarity;

/**
 * A fegyverek és tárak listája. Nem a kódban van felsorolva, hanem egy generált adatfájlból
 * (unturnedcraft_guns.json, a mod jarjának gyökerében) töltődik be a játék indulásakor.
 *
 * Ettől "adatvezérelt" a mod: új fegyverhez nem kell Java-kódot írni, elég újra lefuttatni a
 * generátort (tools/extract_unturned_assets.py), és a ModItems / ModSounds magától regisztrálja,
 * ami a fájlban van.
 */
public final class GunDefinitions {
    private static final String FILE = "/unturnedcraft_guns.json";

    /** Egy fegyver: a Minecraft-azonosítója (pl. "eaglefire"), a ritkasága és a számai. */
    public record Gun(String id, Rarity rarity, GunStats stats) {}

    /** Egy tár: a Minecraft-azonosítója (pl. "military_30"), a ritkasága és a számai. */
    public record Magazine(String id, Rarity rarity, MagazineStats stats) {}

    /** Tárak azonosító szerint, a fájl sorrendjében. */
    public static final Map<String, Magazine> MAGAZINES = new LinkedHashMap<>();
    /** Fegyverek azonosító szerint, a fájl sorrendjében. */
    public static final Map<String, Gun> GUNS = new LinkedHashMap<>();

    // A static blokk akkor fut le, amikor a Java először használja ezt az osztályt.
    static {
        JsonObject root = readFile();
        for (JsonElement element : root.getAsJsonArray("magazines")) {
            JsonObject json = element.getAsJsonObject();
            String id = json.get("id").getAsString();
            MagazineStats stats = new MagazineStats(intList(json.getAsJsonArray("calibers")),
                    json.get("amount").getAsInt(), json.get("pellets").getAsInt());
            MAGAZINES.put(id, new Magazine(id, rarity(json.get("rarity").getAsString()), stats));
        }
        for (JsonElement element : root.getAsJsonArray("guns")) {
            JsonObject json = element.getAsJsonObject();
            String id = json.get("id").getAsString();
            GunStats stats = GunStats.fromJson(json);
            if (!MAGAZINES.containsKey(stats.defaultMagazine())) {
                throw new IllegalStateException(FILE + ": a(z) " + id + " fegyver alap tára ("
                        + stats.defaultMagazine() + ") nincs a tárak között");
            }
            GUNS.put(id, new Gun(id, rarity(json.get("rarity").getAsString()), stats));
        }
        UnturnedCraft.LOGGER.info("{} fegyver és {} tár betöltve", GUNS.size(), MAGAZINES.size());
    }

    private static JsonObject readFile() {
        // getResourceAsStream: fájl olvasása a mod saját jarjából.
        try (InputStream stream = GunDefinitions.class.getResourceAsStream(FILE)) {
            if (stream == null) {
                throw new IllegalStateException("Hiányzik a mod jarjából: " + FILE
                        + " (futtasd le a tools/extract_unturned_assets.py scriptet)");
            }
            return JsonParser.parseReader(new InputStreamReader(stream, StandardCharsets.UTF_8)).getAsJsonObject();
        } catch (IOException e) {
            throw new IllegalStateException("Nem olvasható: " + FILE, e);
        }
    }

    static List<Integer> intList(JsonArray array) {
        List<Integer> list = new ArrayList<>();
        for (JsonElement element : array) {
            list.add(element.getAsInt());
        }
        return List.copyOf(list);
    }

    /**
     * Az Unturned hat ritkasági szintjét a Minecraft négy szintjére képezzük le
     * (ez adja a tárgy nevének színét).
     */
    private static Rarity rarity(String unturnedRarity) {
        return switch (unturnedRarity) {
            case "Uncommon" -> Rarity.UNCOMMON;
            case "Rare" -> Rarity.RARE;
            case "Epic", "Legendary", "Mythical" -> Rarity.EPIC;
            default -> Rarity.COMMON;
        };
    }

    private GunDefinitions() {}
}
