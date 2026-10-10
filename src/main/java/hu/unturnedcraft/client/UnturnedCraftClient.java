package hu.unturnedcraft.client;

import hu.unturnedcraft.UnturnedCraft;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.common.NeoForge;

/**
 * A mod kliensoldali belépési pontja. A "dist = Dist.CLIENT" miatt ez az osztály csak a játék
 * kliensén töltődik be, dedikált szerveren soha.
 *
 * Erre azért van szükség, mert a hu.unturnedcraft.client csomag olyan osztályokat használ
 * (billentyűk, képernyő, kamera), amik a dedikált szerverben nincsenek is benne. Ha a közös kód
 * (pl. a GunItem) hivatkozna rájuk, a szerver összeomlana. Ezért a szabály: a client csomagból
 * bármit el lehet érni, de a client csomagon KÍVÜLről ide hivatkozni tilos.
 */
@Mod(value = UnturnedCraft.MODID, dist = Dist.CLIENT)
public class UnturnedCraftClient {
    public UnturnedCraftClient(IEventBus modEventBus) {
        // Két eseménybusz van. A mod busza (modEventBus) az induláskori, egyszeri dolgoké, pl. a
        // regisztrációké. A játék busza (NeoForge.EVENT_BUS) arra való, ami játék közben történik.
        modEventBus.addListener(GunInputHandler::registerKeys);

        NeoForge.EVENT_BUS.addListener(GunInputHandler::onClientTick);
        NeoForge.EVENT_BUS.addListener(GunInputHandler::onInteractionKey);
        NeoForge.EVENT_BUS.addListener(GunInputHandler::onComputeFov);
        NeoForge.EVENT_BUS.addListener(GunInputHandler::onCalculateTurn);
    }
}
