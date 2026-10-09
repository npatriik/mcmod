package hu.unturnedcraft;

import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.damagesource.DamageType;

/**
 * Sebzéstípusok. Ezeket nem kódból regisztráljuk, hanem adatfájlból töltődnek be:
 * data/unturnedcraft/damage_type/bullet.json. Itt csak a hivatkozás (kulcs) van rá.
 */
public final class ModDamageTypes {
    public static final ResourceKey<DamageType> BULLET =
            ResourceKey.create(Registries.DAMAGE_TYPE, UnturnedCraft.id("bullet"));

    private ModDamageTypes() {}
}
