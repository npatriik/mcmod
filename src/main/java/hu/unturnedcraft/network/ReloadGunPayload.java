package hu.unturnedcraft.network;

import hu.unturnedcraft.UnturnedCraft;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/**
 * Kliens -> szerver üzenet: "megnyomtam az újratöltés gombot".
 * Nincs benne adat, maga az üzenet megérkezése a lényeg, ezért egyetlen példány (INSTANCE) elég belőle.
 */
public record ReloadGunPayload() implements CustomPacketPayload {
    public static final ReloadGunPayload INSTANCE = new ReloadGunPayload();
    public static final Type<ReloadGunPayload> TYPE = new Type<>(UnturnedCraft.id("reload_gun"));

    /** "unit" codec: nulla bájtot ír, olvasáskor pedig mindig az INSTANCE-t adja vissza. */
    public static final StreamCodec<ByteBuf, ReloadGunPayload> STREAM_CODEC = StreamCodec.unit(INSTANCE);

    @Override
    public Type<ReloadGunPayload> type() {
        return TYPE;
    }
}
