package hu.unturnedcraft;

import java.util.LinkedHashMap;
import java.util.Map;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.CreativeModeTabs;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.UseEffects;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;

/**
 * A mod tárgyai és a kreatív menü füle. A fegyverek és tárak nincsenek egyenként felsorolva:
 * a {@link GunDefinitions} adatfájljából jönnek, és itt egy-egy ciklus regisztrálja őket.
 */
public final class ModItems {
    public static final DeferredRegister.Items ITEMS = DeferredRegister.createItems(UnturnedCraft.MODID);
    public static final DeferredRegister<CreativeModeTab> CREATIVE_TABS =
            DeferredRegister.create(Registries.CREATIVE_MODE_TAB, UnturnedCraft.MODID);

    /** Az összes tár, azonosító szerint (pl. "military_30"). */
    public static final Map<String, DeferredItem<MagazineItem>> MAGAZINES = new LinkedHashMap<>();
    /** Az összes fegyver, azonosító szerint (pl. "eaglefire"). */
    public static final Map<String, DeferredItem<GunItem>> GUNS = new LinkedHashMap<>();

    /**
     * Mi történik a játékossal, amíg céloz (vagyis "használja" a fegyvert): nem tud sprintelni, a
     * célzás nem kelt rezgést (a sculk érzékelők nem figyelnek fel rá), és a szokásos sebesség
     * 75%-ával mozog. Alapból a Minecraft tárgyhasználat közben 20%-ra lassít (mint evésnél),
     * az célzáshoz túl lassú lenne. A 75% saját választás, nem az Unturnedből jön.
     */
    private static final UseEffects AIMING_EFFECTS = new UseEffects(false, false, 0.75f);

    static {
        for (GunDefinitions.Magazine magazine : GunDefinitions.MAGAZINES.values()) {
            MAGAZINES.put(magazine.id(), ITEMS.registerItem(magazine.id(),
                    properties -> new MagazineItem(properties, magazine.stats()),
                    properties -> properties.stacksTo(16).rarity(magazine.rarity())));
        }

        for (GunDefinitions.Gun gun : GunDefinitions.GUNS.values()) {
            GunStats stats = gun.stats();
            DeferredItem<MagazineItem> defaultMagazine = MAGAZINES.get(stats.defaultMagazine());
            int defaultAmmo = GunDefinitions.MAGAZINES.get(stats.defaultMagazine()).stats().amount();
            GUNS.put(gun.id(), ITEMS.registerItem(gun.id(),
                    properties -> new GunItem(properties, stats, defaultMagazine, ModSounds.forGun(gun.id())),
                    // Új példány az alap tárával, tele jön létre: ezt állítja be a két saját komponens.
                    properties -> properties.stacksTo(1).rarity(gun.rarity())
                            .component(ModDataComponents.AMMO.get(), defaultAmmo)
                            .component(ModDataComponents.LOADED_MAGAZINE.get(), defaultMagazine.getId())
                            .component(DataComponents.USE_EFFECTS, AIMING_EFFECTS)));
        }

        // A 0.2.0-ig az 1911 tárát "colt_magazine"-nek hívták. Az alias miatt a régi világokban
        // lévő tárak nem vesznek el: a játék az új néven (colt_7) tölti be őket.
        ITEMS.addAlias(UnturnedCraft.id("colt_magazine"), UnturnedCraft.id("colt_7"));
    }

    /** Saját fül a kreatív menüben: elöl a fegyverek, utánuk a tárak. */
    public static final DeferredHolder<CreativeModeTab, CreativeModeTab> MAIN_TAB = CREATIVE_TABS.register("main",
            () -> CreativeModeTab.builder()
                    .title(Component.translatable("itemGroup.unturnedcraft"))
                    .withTabsBefore(CreativeModeTabs.COMBAT)
                    .icon(() -> new ItemStack(GUNS.get("colt").get()))
                    .displayItems((parameters, output) -> {
                        GUNS.values().forEach(gun -> output.accept(gun.get()));
                        MAGAZINES.values().forEach(magazine -> output.accept(magazine.get()));
                    })
                    .build());

    private ModItems() {}
}
