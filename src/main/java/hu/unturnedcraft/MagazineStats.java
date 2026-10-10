package hu.unturnedcraft;

import java.util.List;

/**
 * Egy tár számai az Unturned .dat fájljából (pl. Bundles/Items/Magazines/Military_30/Military_30.dat).
 *
 * @param calibers milyen kaliberű fegyverekbe illik (Calibers / Caliber_0, Caliber_1...). Az
 *                 Unturnedben a kaliber csak egy sorszám: egy tár akkor megy bele egy fegyverbe,
 *                 ha van közös számuk.
 * @param amount   hány lövés van benne (Amount)
 * @param pellets  hány sörétet lő ki egyetlen lövés (Pellets). A sima táraknál 1; a sörétes
 *                 puskák lőszerénél 6-8, de néhány géppuska "doboza" is 3-4-et szór lövésenként.
 */
public record MagazineStats(List<Integer> calibers, int amount, int pellets) {
    /** Igaz, ha ez a tár beleillik egy olyan fegyverbe, ami a megadott kalibereket fogadja. */
    public boolean fits(List<Integer> gunCalibers) {
        for (int caliber : calibers) {
            if (gunCalibers.contains(caliber)) {
                return true;
            }
        }
        return false;
    }
}
