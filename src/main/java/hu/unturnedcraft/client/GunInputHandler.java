package hu.unturnedcraft.client;

import com.mojang.blaze3d.platform.InputConstants;
import hu.unturnedcraft.GunItem;
import hu.unturnedcraft.UnturnedCraft;
import hu.unturnedcraft.network.FireGunPayload;
import hu.unturnedcraft.network.ReloadGunPayload;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.neoforged.neoforge.client.event.CalculatePlayerTurnEvent;
import net.neoforged.neoforge.client.event.ClientTickEvent;
import net.neoforged.neoforge.client.event.ComputeFovModifierEvent;
import net.neoforged.neoforge.client.event.InputEvent;
import net.neoforged.neoforge.client.event.RegisterKeyMappingsEvent;
import net.neoforged.neoforge.client.network.ClientPacketDistributor;
import net.neoforged.neoforge.common.util.Lazy;

/**
 * A fegyverek kezelése a kliensen: figyeli a gombokat, és szól a szervernek.
 *
 * Miért kell ez egyáltalán? A bal klikk a Minecraftban ütést és blokktörést jelent, az R gombot pedig
 * a játék nem is ismeri. Ha fegyver van a kezedben, ezeket itt "térítjük el": a bal klikkből lövés
 * lesz, az R-ből újratöltés. Mindkettőnél elküldünk egy csomagot a szervernek (hogy a dolog tényleg
 * megtörténjen), és helyben is lefuttatjuk ugyanazt (hogy a hang és a visszarúgás ne késsen).
 */
public final class GunInputHandler {
    /** Saját csoport a játék billentyűbeállításai között. */
    private static final KeyMapping.Category KEY_CATEGORY = new KeyMapping.Category(UnturnedCraft.id("main"));

    /**
     * Az újratöltés gombja. Az R csak az alapérték, a játék beállításaiban átállítható.
     *
     * Lazy = "lusta": a KeyMapping objektum nem a játék indulásakor jön létre, hanem akkor, amikor
     * először elkérjük (a get() hívásakor), vagyis a regisztráció pillanatában. A NeoForge
     * dokumentációja ezt írja elő, mert korábban a játék billentyűrendszere még nincs készen.
     */
    public static final Lazy<KeyMapping> RELOAD_KEY = Lazy.of(
            () -> new KeyMapping("key.unturnedcraft.reload", InputConstants.KEY_R, KEY_CATEGORY));

    /** A játék indulásakor egyszer fut le: bejelentjük a saját csoportunkat és gombunkat. */
    static void registerKeys(RegisterKeyMappingsEvent event) {
        event.registerCategory(KEY_CATEGORY);
        event.register(RELOAD_KEY.get());
    }

    /**
     * Másodpercenként 20-szor fut le, minden kliens-tick ELEJÉN, még mielőtt a Minecraft a saját
     * gombjait feldolgozná. Ez a sorrend fontos: így mi "fogyasztjuk el" a bal klikkeket, és a
     * játék már nem lát belőlük ütést.
     */
    static void onClientTick(ClientTickEvent.Pre event) {
        Minecraft minecraft = Minecraft.getInstance();
        LocalPlayer player = minecraft.player;
        // isMouseGrabbed: az egér a játékot irányítja, vagyis nincs nyitva menü, inventory vagy chat.
        if (player == null || !minecraft.mouseHandler.isMouseGrabbed()) {
            return;
        }

        ItemStack held = player.getMainHandItem();
        if (!(held.getItem() instanceof GunItem gun) || player.isSpectator()) {
            // Nincs fegyver a kézben: a bal klikk maradjon a játéké, az R lenyomásait pedig eldobjuk,
            // hogy ne "ragadjanak be", és ne töltsön újra magától, amikor később fegyvert veszel elő.
            while (RELOAD_KEY.get().consumeClick()) {
                // szándékosan üres
            }
            return;
        }

        // --- Lövés ---
        // A consumeClick() annyiszor ad igazat, ahányszor a gombot az előző tick óta LENYOMTÁK. Ettől
        // félautomata egy fegyver: egy lenyomás = egy lövés, akármeddig tartod utána a gombot.
        boolean clicked = false;
        while (minecraft.options.keyAttack.consumeClick()) {
            clicked = true;
        }
        // Automata fegyvernél az is elég, ha a gomb éppen le van nyomva; a tempót a tűzgyorsaság adja.
        boolean triggerPulled = clicked || (gun.stats().automatic() && minecraft.options.keyAttack.isDown());

        if (triggerPulled) {
            // A szögeket még a lövés ELŐTT jegyezzük fel, mert a helyi lövés visszarúgása elmozdítja a kamerát.
            float pitch = player.getXRot();
            float yaw = player.getYRot();
            // 1. Helyben lefuttatjuk: hang és visszarúgás azonnal, nem a szerver válaszára várva.
            //    Hamisat ad, ha a fegyver épp nem süthető el (pl. még nem telt le a két lövés közti idő).
            if (gun.fire(player.level(), player, held, pitch, yaw)) {
                // 2. Szólunk a szervernek: ő dönti el, van-e találat, és ő veszi le a töltényt.
                ClientPacketDistributor.sendToServer(new FireGunPayload(pitch, yaw));
            }
        }

        // --- Újratöltés ---
        while (RELOAD_KEY.get().consumeClick()) {
            ClientPacketDistributor.sendToServer(ReloadGunPayload.INSTANCE);
            gun.reload(player.level(), player, held);
        }
    }

    /**
     * A játék ezt az eseményt küldi, mielőtt egy bal/jobb/középső klikket végrehajtana. Ha fegyver
     * van a kézben, a bal klikket visszavonjuk: ne üssön, ne törjön blokkot, és a kar se lendüljön.
     * (Az egyszeri kattintásokat már az onClientTick elfogyasztja; ez arra az esetre kell, amikor a
     * gombot egy blokkra nézve nyomva tartod, mert a játék a folyamatos blokktörést külön kezeli.)
     */
    static void onInteractionKey(InputEvent.InteractionKeyMappingTriggered event) {
        LocalPlayer player = Minecraft.getInstance().player;
        if (event.isAttack() && player != null && player.getMainHandItem().getItem() instanceof GunItem) {
            event.setSwingHand(false);
            event.setCanceled(true);
        }
    }

    /** A fegyver, amivel a játékos éppen céloz, vagy null. */
    private static GunItem aimedGun(Player player) {
        if (player != null && player.isUsingItem() && player.getUseItem().getItem() instanceof GunItem gun) {
            return gun;
        }
        return null;
    }

    /**
     * Látószög (FOV) számítása: a játék itt kérdezi meg, kell-e módosítani (így zoomol pl. az íj
     * felhúzáskor). Ha a játékos fegyverrel céloz, szűkítjük a látószöget: sima irányzéknál kicsit,
     * távcsőnél a nagyításának megfelelően. A váltást a játék magától simítja, ezért nem ugrik a kép.
     */
    static void onComputeFov(ComputeFovModifierEvent event) {
        GunItem gun = aimedGun(event.getPlayer());
        if (gun != null) {
            event.setNewFovModifier(event.getNewFovModifier() * gun.stats().aimFovMultiplier());
        }
    }

    /**
     * Egérérzékenység. Ha a kép kétszeresére nagyít, ugyanaz az egérmozdulat kétszer akkorát
     * mozdítana a célponton, ezért célzás közben a nagyítás arányában lassítjuk az egeret.
     *
     * A játék az érzékenység csúszkájának értékéből (s) így számol sebességet: (0.6 * s + 0.2)^3.
     * Ahhoz, hogy a SEBESSÉG legyen a kért arányú, a csúszka értékét ennek megfelelően kell
     * visszaszámolni; ezt csinálja a képlet.
     */
    static void onCalculateTurn(CalculatePlayerTurnEvent event) {
        GunItem gun = aimedGun(Minecraft.getInstance().player);
        if (gun != null) {
            double speedRoot = 0.6 * event.getMouseSensitivity() + 0.2;
            double scaledRoot = speedRoot * Math.cbrt(gun.stats().aimFovMultiplier());
            event.setMouseSensitivity((scaledRoot - 0.2) / 0.6);
        }
    }

    private GunInputHandler() {}
}
