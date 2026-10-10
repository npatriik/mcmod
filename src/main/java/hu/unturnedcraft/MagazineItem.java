package hu.unturnedcraft;

import java.util.function.Consumer;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.TooltipDisplay;

/**
 * Egy tár (vagy töltőléc, lőszeres doboz, sörétes lőszer). Saját viselkedése nincs: a fegyver
 * "eszi meg" újratöltéskor ({@link GunItem#reload}), és a számaiból tudja, hány lövést kap.
 */
public class MagazineItem extends Item {
    private final MagazineStats stats;

    public MagazineItem(Properties properties, MagazineStats stats) {
        super(properties);
        this.stats = stats;
    }

    public MagazineStats stats() {
        return stats;
    }

    // Lásd a GunItem.appendHoverText megjegyzését az "elavult" jelölésről.
    @SuppressWarnings("deprecation")
    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay display,
            Consumer<Component> tooltip, TooltipFlag flag) {
        tooltip.accept(Component.translatable("tooltip.unturnedcraft.rounds", stats.amount())
                .withStyle(ChatFormatting.GRAY));
        if (stats.pellets() > 1) {
            tooltip.accept(Component.translatable("tooltip.unturnedcraft.pellets", stats.pellets())
                    .withStyle(ChatFormatting.GRAY));
        }
    }
}
