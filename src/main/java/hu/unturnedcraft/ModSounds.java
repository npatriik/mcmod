package hu.unturnedcraft;

import java.util.HashMap;
import java.util.Map;
import net.minecraft.core.registries.Registries;
import net.minecraft.sounds.SoundEvent;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

/**
 * Hangesemények. Itt csak a nevüket regisztráljuk; azt, hogy melyik névhez melyik .ogg fájl
 * tartozik, a (generált) assets/unturnedcraft/sounds.json mondja meg.
 *
 * Minden fegyver három hangot kap: item.<fegyver>.shoot, .reload és .empty.
 */
public final class ModSounds {
    public static final DeferredRegister<SoundEvent> SOUNDS =
            DeferredRegister.create(Registries.SOUND_EVENT, UnturnedCraft.MODID);

    /** Egy fegyver három hangja. */
    public record GunSounds(
            DeferredHolder<SoundEvent, SoundEvent> shoot,
            DeferredHolder<SoundEvent, SoundEvent> reload,
            DeferredHolder<SoundEvent, SoundEvent> empty) {}

    private static final Map<String, GunSounds> BY_GUN = new HashMap<>();

    static {
        for (String gun : GunDefinitions.GUNS.keySet()) {
            BY_GUN.put(gun, new GunSounds(
                    register("item." + gun + ".shoot"),
                    register("item." + gun + ".reload"),
                    register("item." + gun + ".empty")));
        }
    }

    public static GunSounds forGun(String gunId) {
        return BY_GUN.get(gunId);
    }

    private static DeferredHolder<SoundEvent, SoundEvent> register(String name) {
        // "VariableRange": a hang hallótávolsága a lejátszáskor megadott hangerőtől függ.
        return SOUNDS.register(name, SoundEvent::createVariableRangeEvent);
    }

    private ModSounds() {}
}
