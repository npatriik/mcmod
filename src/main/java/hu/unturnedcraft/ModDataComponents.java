package hu.unturnedcraft;

import com.mojang.serialization.Codec;
import net.minecraft.core.component.DataComponentType;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.codec.ByteBufCodecs;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

/**
 * "Adatkomponensek": plusz adatok, amiket egy-egy konkrét tárgy (ItemStack) magával hordoz.
 * Ilyen a vanilla játékban pl. a sérülés vagy az egyedi név. Nekünk a töltények száma kell.
 */
public final class ModDataComponents {
    public static final DeferredRegister.DataComponents DATA_COMPONENTS =
            DeferredRegister.createDataComponents(Registries.DATA_COMPONENT_TYPE, UnturnedCraft.MODID);

    /**
     * Hány töltény van éppen a fegyverben.
     * persistent = így mentődik el a világba; networkSynchronized = így jut el a klienshez.
     */
    public static final DeferredHolder<DataComponentType<?>, DataComponentType<Integer>> AMMO =
            DATA_COMPONENTS.registerComponentType("ammo",
                    builder -> builder.persistent(Codec.INT).networkSynchronized(ByteBufCodecs.VAR_INT));

    private ModDataComponents() {}
}
