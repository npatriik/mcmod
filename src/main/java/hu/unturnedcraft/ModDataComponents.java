package hu.unturnedcraft;

import com.mojang.serialization.Codec;
import net.minecraft.core.component.DataComponentType;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.resources.Identifier;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

/**
 * "Adatkomponensek": plusz adatok, amiket egy-egy konkrét tárgy (ItemStack) magával hordoz.
 * Ilyen a vanilla játékban pl. a sérülés vagy az egyedi név. Nekünk a fegyver töltöttsége kell.
 *
 * Mindegyiknél kétféle "codec" kell: a persistent mondja meg, hogyan mentődik el a világba, a
 * networkSynchronized pedig azt, hogyan jut el a szerverről a klienshez.
 */
public final class ModDataComponents {
    public static final DeferredRegister.DataComponents DATA_COMPONENTS =
            DeferredRegister.createDataComponents(Registries.DATA_COMPONENT_TYPE, UnturnedCraft.MODID);

    /** Hány töltény van éppen a fegyverben. */
    public static final DeferredHolder<DataComponentType<?>, DataComponentType<Integer>> AMMO =
            DATA_COMPONENTS.registerComponentType("ammo",
                    builder -> builder.persistent(Codec.INT).networkSynchronized(ByteBufCodecs.VAR_INT));

    /**
     * Melyik fajta tár van éppen a fegyverben (a tár tárgyazonosítója, pl. unturnedcraft:military_30).
     * Ebből tudja a fegyver, hány lövés fér bele, és hány sörétet lő ki egyszerre.
     */
    public static final DeferredHolder<DataComponentType<?>, DataComponentType<Identifier>> LOADED_MAGAZINE =
            DATA_COMPONENTS.registerComponentType("loaded_magazine",
                    builder -> builder.persistent(Identifier.CODEC).networkSynchronized(Identifier.STREAM_CODEC));

    private ModDataComponents() {}
}
