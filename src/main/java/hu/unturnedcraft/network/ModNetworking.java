package hu.unturnedcraft.network;

import hu.unturnedcraft.GunItem;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;
import net.neoforged.neoforge.network.handling.IPayloadContext;
import net.neoforged.neoforge.network.registration.PayloadRegistrar;

/**
 * A mod saját hálózati üzenetei. Itt mondjuk meg a NeoForge-nak, milyen csomagjaink vannak, és
 * mi történjen a szerveren, amikor megérkeznek.
 */
public final class ModNetworking {
    /**
     * A csomagok "protokollverziója". Ha egyszer megváltozik egy csomag tartalma, ezt növelni kell,
     * hogy egy régi kliens ne tudjon félreérthető üzenetet küldeni egy új szervernek.
     */
    private static final String PROTOCOL_VERSION = "1";

    public static void register(RegisterPayloadHandlersEvent event) {
        PayloadRegistrar registrar = event.registrar(PROTOCOL_VERSION);
        // playToServer: játék közben, a klienstől a szerver felé menő csomag.
        registrar.playToServer(FireGunPayload.TYPE, FireGunPayload.STREAM_CODEC, ModNetworking::handleFire);
        registrar.playToServer(ReloadGunPayload.TYPE, ReloadGunPayload.STREAM_CODEC, ModNetworking::handleReload);
    }

    // A kezelők a szerver fő szálán futnak (ez a NeoForge alapbeállítása), ezért szabadon
    // hozzányúlhatnak a világhoz és a játékoshoz.
    //
    // Szabály: a szerver soha nem bízik meg a kliensben. A csomag csak annyit mond, hogy a játékos
    // lőni/tölteni SZERETNE; hogy tényleg lehet-e (van-e a kezében fegyver, van-e töltény, lejárt-e a
    // cooldown), azt a szerver a saját adataiból ellenőrzi újra.

    private static void handleFire(FireGunPayload payload, IPayloadContext context) {
        Player player = context.player();
        ItemStack held = player.getMainHandItem();
        if (!canUseGun(player, held) || !Float.isFinite(payload.pitch()) || !Float.isFinite(payload.yaw())) {
            return;
        }
        GunItem gun = (GunItem) held.getItem();
        gun.fire(player.level(), player, held, Mth.clamp(payload.pitch(), -90f, 90f), payload.yaw());
    }

    private static void handleReload(ReloadGunPayload payload, IPayloadContext context) {
        Player player = context.player();
        ItemStack held = player.getMainHandItem();
        if (!canUseGun(player, held)) {
            return;
        }
        GunItem gun = (GunItem) held.getItem();
        gun.reload(player.level(), player, held);
    }

    private static boolean canUseGun(Player player, ItemStack held) {
        return player.isAlive() && !player.isSpectator() && held.getItem() instanceof GunItem;
    }

    private ModNetworking() {}
}
