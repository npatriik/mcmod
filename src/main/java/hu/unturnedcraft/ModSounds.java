package hu.unturnedcraft;

import net.minecraft.core.registries.Registries;
import net.minecraft.sounds.SoundEvent;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

/**
 * Hangesemények. Itt csak a nevüket regisztráljuk; azt, hogy melyik névhez melyik .ogg fájl
 * tartozik, az assets/unturnedcraft/sounds.json mondja meg.
 */
public final class ModSounds {
    public static final DeferredRegister<SoundEvent> SOUNDS =
            DeferredRegister.create(Registries.SOUND_EVENT, UnturnedCraft.MODID);

    public static final DeferredHolder<SoundEvent, SoundEvent> COLT_SHOOT = register("item.colt.shoot");
    public static final DeferredHolder<SoundEvent, SoundEvent> COLT_RELOAD = register("item.colt.reload");
    public static final DeferredHolder<SoundEvent, SoundEvent> COLT_EMPTY = register("item.colt.empty");

    private static DeferredHolder<SoundEvent, SoundEvent> register(String name) {
        // "VariableRange": a hang hallótávolsága a lejátszáskor megadott hangerőtől függ.
        return SOUNDS.register(name, SoundEvent::createVariableRangeEvent);
    }

    private ModSounds() {}
}
