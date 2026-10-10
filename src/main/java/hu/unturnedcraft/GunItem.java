package hu.unturnedcraft;

import java.util.Collections;
import java.util.Map;
import java.util.WeakHashMap;
import java.util.function.Consumer;
import java.util.function.Supplier;
import net.minecraft.ChatFormatting;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.ProjectileUtil;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.ItemUseAnimation;
import net.minecraft.world.item.ItemUtils;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.TooltipDisplay;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/**
 * Egy lőfegyver. Kezelése az Unturned mintájára:
 * <ul>
 *   <li>bal klikk: lövés ({@link #fire})</li>
 *   <li>jobb klikk nyomva tartva: célzás ({@link #use})</li>
 *   <li>R: újratöltés ({@link #reload})</li>
 * </ul>
 * Minden fegyver ugyanez az osztály; ami megkülönbözteti őket, az a {@link GunStats} (a számaik),
 * a hangjaik és a modelljük.
 *
 * <h2>Kliens és szerver</h2>
 * A Minecraftban a játék két félből áll, egyjátékos módban is: a kliens (amit látsz és irányítasz)
 * és a szerver (ahol a világ "valójában" van). Ami számít (találat, sebzés, töltényfogyás), az csak a
 * szerveren történhet, különben csalni lehetne, és többjátékos módban mindenki mást látna.
 *
 * A jobb klikket a Minecraft magától elküldi a szervernek (ezért a célzáshoz elég a use() metódus).
 * A bal klikk és az R gomb viszont a kliensen keletkezik, és a szerver nem tud róla; ezekhez saját
 * hálózati csomagot küldünk (lásd a network csomagot és a client.GunInputHandler osztályt).
 *
 * A fire() és a reload() ezért KÉTSZER fut le: egyszer a kliensen, rögtön a gombnyomáskor, és egyszer
 * a szerveren, amikor a csomag megérkezik. A kliens csak azt csinálja, aminek azonnal éreződnie kell
 * (hang, visszarúgás), minden mást a szerver. Ezt hívják kliensoldali jóslásnak (prediction).
 */
public class GunItem extends Item {
    /** Ennyi ideig nem lehet újra próbálkozni, ha üres fegyverrel próbálsz lőni. */
    private static final int EMPTY_CLICK_COOLDOWN_TICKS = 10;
    /** A tölténysáv színe a tárgy ikonja alatt (a tárak töltényeinek sárgaréz színe). */
    private static final int AMMO_BAR_COLOR = 0xE7C402;
    /** "Végtelen" ideig lehet célozni: a Minecraft tárgyhasználatának kötelező megadni egy hosszt (itt 1 óra). */
    private static final int MAX_AIM_TICKS = 72000;
    /**
     * A szerver ennyi tickkel engedékenyebb a tűzgyorsaságnál, mint a kliens. A két oldal órája
     * ugyanis nem jár tökéletesen együtt, és e nélkül egy gyors sorozatból a szerver időnként
     * eldobna egy-egy lövést, amit a kliens már "elsütött".
     */
    private static final int SERVER_FIRE_RATE_TOLERANCE_TICKS = 1;

    /**
     * Melyik játékos mikor lőtt utoljára (a saját tick-számlálója szerint; a szerveren egy korán
     * érkezett lövésnél az az időpont, amikor esedékes lett volna). A kliensoldali és a
     * szerveroldali játékos két külön objektum, ezért a két oldal nem keveredik. WeakHashMap:
     * ha a játékos objektuma megszűnik (kilép, újraéled), a bejegyzése magától eltűnik.
     */
    private static final Map<Player, Integer> LAST_SHOT_TICK = Collections.synchronizedMap(new WeakHashMap<>());

    private final GunStats stats;
    private final Supplier<MagazineItem> defaultMagazine;
    private final ModSounds.GunSounds sounds;

    public GunItem(Properties properties, GunStats stats, Supplier<MagazineItem> defaultMagazine,
            ModSounds.GunSounds sounds) {
        super(properties);
        this.stats = stats;
        this.defaultMagazine = defaultMagazine;
        this.sounds = sounds;
    }

    public GunStats stats() {
        return stats;
    }

    // ------------------------------------------------------------------------------------
    // Töltények és tár
    // ------------------------------------------------------------------------------------

    public static int getAmmo(ItemStack gun) {
        return gun.getOrDefault(ModDataComponents.AMMO.get(), 0);
    }

    public static void setAmmo(ItemStack gun, int ammo) {
        gun.set(ModDataComponents.AMMO.get(), Math.max(0, ammo));
    }

    /**
     * A fegyverben lévő tár számai. Egy fegyverbe többféle tár is illhet (pl. 30-as tár és 100-as
     * dobtár), ezért a fegyver megjegyzi, melyik van benne. Ha ez az adat hiányzik vagy már nem
     * létező tárra mutat, az alap tárral számolunk.
     */
    public MagazineStats loadedMagazine(ItemStack gun) {
        Identifier id = gun.get(ModDataComponents.LOADED_MAGAZINE.get());
        if (id != null && BuiltInRegistries.ITEM.getValue(id) instanceof MagazineItem magazine) {
            return magazine.stats();
        }
        return defaultMagazine.get().stats();
    }

    /** Hány töltény fér a fegyverbe a most benne lévő tárral. */
    public int capacity(ItemStack gun) {
        return loadedMagazine(gun).amount();
    }

    // ------------------------------------------------------------------------------------
    // Jobb klikk: célzás
    // ------------------------------------------------------------------------------------

    /**
     * A célzás a Minecraft beépített "tárgyhasználat" rendszerére épül, ugyanarra, amivel az íjat
     * felhúzod vagy a távcsőbe nézel: amíg nyomod a jobb gombot, a játékos "használja" a tárgyat.
     * Ezt az állapotot a játék magától szinkronizálja a szerverrel, így a szerver saját csomag nélkül
     * is tudja, hogy éppen célzol-e.
     */
    @Override
    public InteractionResult use(Level level, Player player, InteractionHand hand) {
        // A fegyver csak a fő kézben működik.
        if (hand != InteractionHand.MAIN_HAND) {
            return InteractionResult.PASS;
        }
        return ItemUtils.startUsingInstantly(level, player, hand);
    }

    @Override
    public int getUseDuration(ItemStack stack, LivingEntity entity) {
        return MAX_AIM_TICKS;
    }

    /** NONE: célzás közben a játék ne játsszon le saját animációt (pl. evést vagy íjfeszítést). */
    @Override
    public ItemUseAnimation getUseAnimation(ItemStack stack) {
        return ItemUseAnimation.NONE;
    }

    /** Igaz, ha a játékos ezzel a fegyverrel céloz, és már fel is emelte (letelt az Aim_In_Duration). */
    public boolean isAiming(Player player) {
        return player.isUsingItem()
                && player.getUseItem().getItem() == this
                && player.getTicksUsingItem() >= stats.aimInTicks();
    }

    // ------------------------------------------------------------------------------------
    // Bal klikk: lövés
    // ------------------------------------------------------------------------------------

    /**
     * Egy lövési kísérlet. Mindkét oldalon lefut (lásd az osztály leírását).
     *
     * @param pitch a nézés függőleges szöge a kattintás pillanatában (fok)
     * @param yaw   a nézés vízszintes szöge a kattintás pillanatában (fok)
     * @return igaz, ha történt valami (lövés vagy üres kattanás); hamis, ha a fegyver épp nem süthető el
     */
    public boolean fire(Level level, Player player, ItemStack gun, float pitch, float yaw) {
        // A "cooldown" itt az újratöltés (és az üres kattanás) ideje: amíg tart, a fegyver nem
        // süthető el. A szerver a saját cooldownját elküldi a kliensnek, és a hotbaron is látszik.
        if (player.getCooldowns().isOnCooldown(gun)) {
            return false;
        }
        // Kreatív módban nem fogy a töltény.
        boolean infiniteAmmo = player.hasInfiniteMaterials();

        if (getAmmo(gun) <= 0 && !infiniteAmmo) {
            // Üres: csak kattan egyet.
            playSound(level, player, sounds.empty().get(), 1.0f, 1.0f);
            player.getCooldowns().addCooldown(gun, EMPTY_CLICK_COOLDOWN_TICKS);
            if (!level.isClientSide()) {
                // A keybind(...) a kliensen arra a gombra cserélődik, amire az újratöltés be van állítva.
                player.sendOverlayMessage(Component.translatable("message.unturnedcraft.empty",
                        Component.keybind("key.unturnedcraft.reload")));
            }
            return true;
        }

        if (!fireRateAllows(level, player)) {
            return false;
        }

        // A 4.0 hangerő kb. 64 blokkos hallótávolságot jelent.
        playSound(level, player, sounds.shoot().get(), 4.0f, 0.95f + level.getRandom().nextFloat() * 0.1f);

        if (level instanceof ServerLevel serverLevel) {
            // Egy lövés több sörétet is kilőhet; mindegyik külön vonal, saját szórással.
            int pellets = loadedMagazine(gun).pellets();
            for (int i = 0; i < pellets; i++) {
                fireBullet(serverLevel, player, pitch, yaw);
            }
            // Füst a cső végénél.
            Vec3 muzzle = player.getEyePosition()
                    .add(Vec3.directionFromRotation(pitch, yaw).scale(0.8)).add(0.0, -0.15, 0.0);
            serverLevel.sendParticles(ParticleTypes.SMOKE, muzzle.x, muzzle.y, muzzle.z, 2, 0.02, 0.02, 0.02, 0.01);
            if (!infiniteAmmo) {
                setAmmo(gun, getAmmo(gun) - 1);
            }
        } else {
            applyRecoil(player);
        }
        return true;
    }

    /**
     * Tűzgyorsaság: eltelt-e elég idő a játékos előző lövése óta? Ha igen, a mostani lövést
     * rögtön fel is jegyzi.
     *
     * Ehhez szándékosan nem a Minecraft "cooldown" rendszerét használjuk: az a hotbaron is
     * megjelenik, és egy másodpercenként 10-20 lövést leadó fegyvernél folyamatosan villogna.
     *
     * A szerver egy kicsit engedékenyebb (lásd SERVER_FIRE_RATE_TOLERANCE_TICKS), de a korábban
     * érkezett lövést úgy könyveli el, mintha a "rendes" idejében jött volna. Így egy-egy csomag
     * érkezhet a vártnál hamarabb, a fegyver átlagos tűzgyorsaságát viszont egy átírt kliens sem
     * tudja túllépni: ami most korábban jött, az a következő lövés várakozási idejéből hiányzik.
     */
    private boolean fireRateAllows(Level level, Player player) {
        int now = player.tickCount;
        int tolerance = level.isClientSide() ? 0 : SERVER_FIRE_RATE_TOLERANCE_TICKS;
        Integer last = LAST_SHOT_TICK.get(player);
        if (last == null || now < last - tolerance) {
            // Még nem lőtt (vagy a számláló újraindult): nincs mihez viszonyítani.
            LAST_SHOT_TICK.put(player, now);
            return true;
        }
        int due = last + stats.fireCooldownTicks();
        if (now < due - tolerance) {
            return false;
        }
        // Korai lövésnél az esedékes időpontot jegyezzük fel, nem a tényleges érkezést.
        LAST_SHOT_TICK.put(player, Math.max(now, due));
        return true;
    }

    // ------------------------------------------------------------------------------------
    // R: újratöltés
    // ------------------------------------------------------------------------------------

    /** Egy újratöltési kísérlet. Mindkét oldalon lefut (lásd az osztály leírását). */
    public void reload(Level level, Player player, ItemStack gun) {
        if (player.getCooldowns().isOnCooldown(gun) || getAmmo(gun) >= capacity(gun)) {
            return;
        }
        boolean infiniteAmmo = player.hasInfiniteMaterials();
        int slot = findMagazineSlot(player);

        if (slot < 0 && !infiniteAmmo) {
            if (!level.isClientSide()) {
                player.sendOverlayMessage(Component.translatable("message.unturnedcraft.no_magazine"));
            }
            return;
        }

        // Újratöltés közben nem lehet célozni, és amíg a cooldown tart, lőni sem.
        player.stopUsingItem();
        playSound(level, player, sounds.reload().get(), 1.0f, 1.0f);
        player.getCooldowns().addCooldown(gun, stats.reloadTicks());
        if (!level.isClientSide()) {
            if (slot >= 0) {
                // A talált tár kerül a fegyverbe: innentől az ő befogadóképessége és sörétszáma számít.
                MagazineItem magazine = (MagazineItem) player.getInventory().getItem(slot).getItem();
                gun.set(ModDataComponents.LOADED_MAGAZINE.get(), BuiltInRegistries.ITEM.getKey(magazine));
                if (!infiniteAmmo) {
                    player.getInventory().removeItem(slot, 1);
                }
            }
            setAmmo(gun, capacity(gun));
        }
    }

    /**
     * Megkeresi az első olyan helyet a játékosnál (a hotbartól kezdve), ahol ebbe a fegyverbe illő
     * tár van. -1, ha nincs. Hogy mi illik bele, azt a kaliber dönti el.
     */
    private int findMagazineSlot(Player player) {
        Inventory inventory = player.getInventory();
        for (int slot = 0; slot < inventory.getContainerSize(); slot++) {
            if (inventory.getItem(slot).getItem() instanceof MagazineItem magazine
                    && magazine.stats().fits(stats.calibers())) {
                return slot;
            }
        }
        return -1;
    }

    /**
     * Hang lejátszása a játékos szeménél. Ha a playSound első paramétere a játékos, akkor a kliens
     * azonnal lejátssza neki, a szerver pedig mindenki másnak küldi el; így senki sem hallja kétszer.
     */
    private static void playSound(Level level, Player player, SoundEvent sound, float volume, float pitch) {
        level.playSound(player, player.getX(), player.getEyeY(), player.getZ(), sound, SoundSource.PLAYERS, volume, pitch);
    }

    // ------------------------------------------------------------------------------------
    // A lövés maga (csak a szerveren fut)
    // ------------------------------------------------------------------------------------

    /**
     * Az Unturned fegyverei nem lövedéket repítenek, hanem egy egyenes vonal mentén azonnal
     * találnak ("hitscan"). Itt ugyanezt csináljuk: a szemtől húzunk egy vonalat a lőtávolságig,
     * és megnézzük, mit ér el először.
     */
    private void fireBullet(ServerLevel level, Player shooter, float pitch, float yaw) {
        Vec3 from = shooter.getEyePosition();
        Vec3 direction = spreadDirection(shooter, pitch, yaw);
        Vec3 end = from.add(direction.scale(stats.range()));

        // 1. Az első blokk, ami a vonal útjába esik (a folyadékokon átmegy a golyó).
        BlockHitResult blockHit = level.clip(new ClipContext(
                from, end, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, shooter));
        Vec3 to = blockHit.getType() == HitResult.Type.MISS ? end : blockHit.getLocation();

        // 2. Van-e élőlény (vagy más eltalálható dolog) a blokkig tartó szakaszon?
        EntityHitResult entityHit = ProjectileUtil.getEntityHitResult(
                shooter, from, to, new AABB(from, to).inflate(1.0),
                target -> !target.isSpectator() && target.isPickable() && target.isAlive(),
                from.distanceToSqr(to));

        if (entityHit != null) {
            Entity target = entityHit.getEntity();
            Vec3 hitPos = entityHit.getLocation();
            // A sebzés "forrása" mondja meg a játéknak, ki és mivel sebzett (halálüzenet, páncél...).
            DamageSource source = new DamageSource(
                    level.registryAccess().lookupOrThrow(Registries.DAMAGE_TYPE).getOrThrow(ModDamageTypes.BULLET),
                    shooter);
            target.hurtServer(level, source, damageFor(target, hitPos));
            level.sendParticles(ParticleTypes.CRIT, hitPos.x, hitPos.y, hitPos.z, 4, 0.05, 0.05, 0.05, 0.1);
        } else if (blockHit.getType() == HitResult.Type.BLOCK) {
            // Blokkot ért: a blokk anyagából pattan le pár szilánk, és megszólal a blokk "ütés" hangja.
            BlockState state = level.getBlockState(blockHit.getBlockPos());
            Vec3 hitPos = blockHit.getLocation();
            level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, state),
                    hitPos.x, hitPos.y, hitPos.z, 6, 0.05, 0.05, 0.05, 0.0);
            level.playSound(null, blockHit.getBlockPos(),
                    state.getSoundType(level, blockHit.getBlockPos(), shooter).getHitSound(),
                    SoundSource.BLOCKS, 0.6f, 1.2f);
        }
    }

    /**
     * A nézés iránya, véletlenszerűen eltérítve a fegyver szórásán belül.
     * Csípőből a teljes szórás él (Spread_Angle_Degrees), célozva ennek a Spread_Aim-szerese.
     */
    private Vec3 spreadDirection(Player shooter, float pitch, float yaw) {
        RandomSource random = shooter.getRandom();
        float halfAngle = stats.spreadDegrees() / 2f;
        if (isAiming(shooter)) {
            halfAngle *= stats.aimSpreadMultiplier();
        }
        // Véletlen pont egy körlapon: a szög tetszőleges, a távolság gyöke adja az egyenletes eloszlást.
        float distance = halfAngle * Mth.sqrt(random.nextFloat());
        float angle = random.nextFloat() * Mth.TWO_PI;
        return Vec3.directionFromRotation(pitch + distance * Mth.sin(angle), yaw + distance * Mth.cos(angle));
    }

    /** Sebzés az Unturned szabályai szerint: célpont típusa szerinti alapérték, szorozva a testrész szorzójával. */
    private float damageFor(Entity target, Vec3 hitPos) {
        GunStats.DamageProfile profile;
        if (target instanceof Player) {
            profile = stats.againstPlayers();
        } else if (target instanceof Enemy) {
            // Enemy = minden ellenséges lény (zombi, csontváz, creeper...). Rájuk a zombi-sebzés megy.
            profile = stats.againstZombies();
        } else {
            profile = stats.againstAnimals();
        }

        // A Minecraft lényeinek nincsenek külön eltalálható testrészei, ezért abból számolunk,
        // hogy a találat a lény magasságának hányad részénél érte: felső negyed = fej, alsó 40% = láb.
        double relativeHeight = (hitPos.y - target.getY()) / Math.max(0.01, target.getBbHeight());
        float multiplier;
        if (relativeHeight >= 0.75) {
            multiplier = profile.skullMultiplier();
        } else if (relativeHeight < 0.4) {
            multiplier = profile.legMultiplier();
        } else {
            multiplier = profile.spineMultiplier();
        }
        return profile.damage() * multiplier * GunStats.HEALTH_SCALE;
    }

    // ------------------------------------------------------------------------------------
    // Csak a kliensen: visszarúgás
    // ------------------------------------------------------------------------------------

    /** Felrántja egy kicsit a kamerát. A nézés irányát a kliens kezeli, ezért elég itt átállítani. */
    private void applyRecoil(Player player) {
        RandomSource random = player.getRandom();
        float up = Mth.lerp(random.nextFloat(), stats.recoilMinDegrees(), stats.recoilMaxDegrees());
        float sideways = (random.nextFloat() - 0.5f) * 0.6f;
        player.setXRot(Mth.clamp(player.getXRot() - up, -90f, 90f));
        player.setYRot(player.getYRot() + sideways);
    }

    // ------------------------------------------------------------------------------------
    // Megjelenítés
    // ------------------------------------------------------------------------------------

    /** A tárgy ikonja alatti sáv (amit a szerszámok a kopás jelzésére használnak) itt a töltényeket mutatja. */
    @Override
    public boolean isBarVisible(ItemStack stack) {
        return true;
    }

    @Override
    public int getBarWidth(ItemStack stack) {
        // A sáv teljes szélessége 13 képpont.
        int capacity = Math.max(1, capacity(stack));
        return Math.round(13f * Math.min(getAmmo(stack), capacity) / capacity);
    }

    @Override
    public int getBarColor(ItemStack stack) {
        return AMMO_BAR_COLOR;
    }

    // A Mojang "elavultnak" jelöli ezt a metódust, de saját tárgyhoz továbbra is ez a szokásos módja
    // annak, hogy plusz sort írjunk a tárgy leírásába (amit az egér fölé vitelekor látsz).
    @SuppressWarnings("deprecation")
    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay display,
            Consumer<Component> tooltip, TooltipFlag flag) {
        tooltip.accept(Component.translatable("tooltip.unturnedcraft.ammo", getAmmo(stack), capacity(stack))
                .withStyle(ChatFormatting.GRAY));
        Identifier magazine = stack.get(ModDataComponents.LOADED_MAGAZINE.get());
        if (magazine != null) {
            tooltip.accept(Component.translatable("tooltip.unturnedcraft.magazine",
                    Component.translatable(BuiltInRegistries.ITEM.getValue(magazine).getDescriptionId()))
                    .withStyle(ChatFormatting.GRAY));
        }
        // A keybind(...) mindig az éppen beállított gomb nevét írja ki, akkor is, ha átállítod.
        tooltip.accept(Component.translatable("tooltip.unturnedcraft.controls",
                Component.keybind("key.attack"), Component.keybind("key.use"),
                Component.keybind("key.unturnedcraft.reload")).withStyle(ChatFormatting.DARK_GRAY));
    }

    /**
     * Alapból a játék lejátssza a "kézbe vétel" animációt (a tárgy lesüllyed, majd visszajön),
     * valahányszor a kézben tartott tárgy adata megváltozik. Nálunk minden lövés megváltoztatja
     * a töltényszámot, ezért ezt kikapcsoljuk, kivéve ha tényleg másik tárgyra váltasz.
     */
    @Override
    public boolean shouldCauseReequipAnimation(ItemStack oldStack, ItemStack newStack, boolean slotChanged) {
        return slotChanged || !newStack.is(oldStack.getItem());
    }
}
