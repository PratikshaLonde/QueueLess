import wave
import math
import struct


# =========================================
# NOTIFICATION SOUND SETTINGS
# =========================================

filename = "notification.wav"

sample_rate = 44100
duration = 0.8


# =========================================
# CREATE SOUND
# =========================================

samples = []

for i in range(
    int(sample_rate * duration)
):

    t = i / sample_rate

    # Two-tone notification
    if t < 0.25:

        frequency = 880

    elif t < 0.5:

        frequency = 1175

    else:

        frequency = 880


    # Smooth volume envelope
    fade_in = min(
        1,
        t / 0.03
    )

    fade_out = min(
        1,
        (duration - t) / 0.08
    )

    volume = (
        0.45 *
        fade_in *
        fade_out
    )


    value = int(
        32767 *
        volume *
        math.sin(
            2 *
            math.pi *
            frequency *
            t
        )
    )


    samples.append(
        struct.pack(
            "<h",
            value
        )
    )


# =========================================
# SAVE WAV FILE
# =========================================

with wave.open(
    filename,
    "wb"
) as wav:

    wav.setnchannels(1)

    wav.setsampwidth(2)

    wav.setframerate(
        sample_rate
    )

    wav.writeframes(
        b"".join(samples)
    )


print(
    "Notification sound created successfully:"
)

print(
    filename
)