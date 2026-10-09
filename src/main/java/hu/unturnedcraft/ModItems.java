package hu.unturnedcraft;

import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.CreativeModeTabs;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.component.UseEffects;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;

/** A mod tárgyai és a kreatív menü füle. */
public final class ModItems {
    public static final DeferredRegister.Items ITEMS = DeferredRegister.createItems(UnturnedCraft.MODID);
    public static final DeferredRegister<CreativeModeTab> CREATIVE_TABS =
            DeferredRegister.create(Registries.CREATIVE_MODE_TAB, UnturnedCraft.MODID);

    /** 1911 tár. Sima tárgy, nincs saját viselkedése: a fegyver "eszi meg" újratöltéskor. */
    public static final DeferredItem<Item> COLT_MAGAZINE = ITEMS.registerSimpleItem("colt_magazine",
            properties -> properties.stacksTo(16).rarity(Rarity.UNCOMMON));

    /**
     * Mi történik a játékossal, amíg céloz (vagyis "használja" a fegyvert): nem tud sprintelni, a
     * célzás nem kelt rezgést (a sculk érzékelők nem figyelnek fel rá), és a szokásos sebesség
     * 75%-ával mozog. Alapból a Minecraft tárgyhasználat közben 20%-ra lassít (mint evésnél),
     * az célzáshoz túl lassú lenne. A 75% saját választás, nem az Unturnedből jön.
     */
    private static final UseEffects AIMING_EFFECTS = new UseEffects(false, false, 0.75f);

    /** 1911 pisztoly. Új példány tele tárral jön létre (ezt állítja be az AMMO komponens). */
    public static final DeferredItem<GunItem> COLT = ITEMS.registerItem("colt",
            properties -> new GunItem(properties, GunStats.COLT, COLT_MAGAZINE,
                    ModSounds.COLT_SHOOT, ModSounds.COLT_RELOAD, ModSounds.COLT_EMPTY),
            properties -> properties.stacksTo(1).rarity(Rarity.UNCOMMON)
                    .component(ModDataComponents.AMMO.get(), GunStats.COLT.magazineSize())
                    .component(DataComponents.USE_EFFECTS, AIMING_EFFECTS));

    /** Saját fül a kreatív menüben, hogy könnyű legyen megtalálni a mod tárgyait. */
    public static final DeferredHolder<CreativeModeTab, CreativeModeTab> MAIN_TAB = CREATIVE_TABS.register("main",
            () -> CreativeModeTab.builder()
                    .title(Component.translatable("itemGroup.unturnedcraft"))
                    .withTabsBefore(CreativeModeTabs.COMBAT)
                    .icon(() -> new ItemStack(COLT.get()))
                    .displayItems((parameters, output) -> {
                        output.accept(COLT.get());
                        output.accept(COLT_MAGAZINE.get());
                    })
                    .build());

    private ModItems() {}
}
