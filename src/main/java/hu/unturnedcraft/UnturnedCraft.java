package hu.unturnedcraft;

import com.mojang.logging.LogUtils;
import hu.unturnedcraft.network.ModNetworking;
import net.minecraft.resources.Identifier;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.common.Mod;
import org.slf4j.Logger;

/**
 * A mod belépési pontja. A NeoForge a @Mod annotáció alapján találja meg, és a játék
 * indulásakor egyszer meghívja a konstruktorát.
 */
@Mod(UnturnedCraft.MODID)
public class UnturnedCraft {
    /** A mod azonosítója. Ugyanennek kell szerepelnie a gradle.properties mod_id sorában is. */
    public static final String MODID = "unturnedcraft";
    public static final Logger LOGGER = LogUtils.getLogger();

    public UnturnedCraft(IEventBus modEventBus) {
        // A Minecraftban minden új dolgot (tárgy, hang, ...) "regisztrálni" kell, különben a
        // játék nem tud róla. A listák a Mod* osztályokban vannak, itt csak bekötjük őket.
        ModDataComponents.DATA_COMPONENTS.register(modEventBus);
        ModSounds.SOUNDS.register(modEventBus);
        ModItems.ITEMS.register(modEventBus);
        ModItems.CREATIVE_TABS.register(modEventBus);

        // A saját hálózati csomagjaink (bal klikk = lövés, R = újratöltés) bejelentése.
        modEventBus.addListener(ModNetworking::register);
    }

    /** Rövidítés: id("colt") -> "unturnedcraft:colt". */
    public static Identifier id(String path) {
        return Identifier.fromNamespaceAndPath(MODID, path);
    }
}
