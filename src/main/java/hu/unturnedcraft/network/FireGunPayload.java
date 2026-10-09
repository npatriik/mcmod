package hu.unturnedcraft.network;

import hu.unturnedcraft.UnturnedCraft;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/**
 * Kliens -> szerver üzenet: "meghúztam a ravaszt".
 *
 * A nézés irányát is elküldjük, mert a szerver a játékos forgásáról csak tickenként egyszer kap
 * hírt, a kattintás pedig két ilyen frissítés között is történhet. Így a golyó pontosan arra megy,
 * amerre a kattintás pillanatában néztél.
 *
 * @param pitch függőleges szög fokban (-90 = egyenesen fel, 90 = egyenesen le)
 * @param yaw   vízszintes szög fokban
 */
public record FireGunPayload(float pitch, float yaw) implements CustomPacketPayload {
    /** A csomag egyedi neve; ebből tudja a túloldal, milyen üzenet érkezett. */
    public static final Type<FireGunPayload> TYPE = new Type<>(UnturnedCraft.id("fire_gun"));

    /**
     * A "codec" írja le, hogyan lesz az objektumból bájtsorozat és vissza. Itt: két float egymás
     * után, először a pitch, aztán a yaw, visszafelé pedig ebből a kettőből készül új FireGunPayload.
     */
    public static final StreamCodec<ByteBuf, FireGunPayload> STREAM_CODEC = StreamCodec.composite(
            ByteBufCodecs.FLOAT, FireGunPayload::pitch,
            ByteBufCodecs.FLOAT, FireGunPayload::yaw,
            FireGunPayload::new);

    @Override
    public Type<FireGunPayload> type() {
        return TYPE;
    }
}
