import threading
import os
from web import run as run_web

threading.Thread(target=run_web).start()
import io
import math
import random

import discord
from discord import app_commands

import imageio.v2 as imageio
from PIL import Image, ImageDraw, ImageFont

TOKEN = os.environ.get("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN environment variable is not set")

PAYMENT_LINKTREE = "https://linktr.ee/FundingFern"

WHEEL_VALUES = [10, 15, 20, 25]

# Colours
PALE_PINK = (255, 105, 180)   # pink
PALE_BLUE = (100, 160, 255)    # blue
TEXT_DARK = (0, 0, 0)         # black text
BG = (230, 215, 245)          # lilac background


def _ease_out_cubic(t: float) -> float:
    return 1 - (1 - t) ** 3


def make_spin_gif(result_value: int, size: int = 420) -> bytes:
    frames = 140          # ~10 seconds
    frame_duration = 0.025

    idx = WHEEL_VALUES.index(result_value)
    n = len(WHEEL_VALUES)
    seg_angle = 360 / n

    pointer_angle = -90
    chosen_center = (idx + 0.5) * seg_angle
    final_rotation = pointer_angle - chosen_center

    extra_turns = 4 * 360
    start_rotation = final_rotation + extra_turns + random.randint(0, 359)

    radius = size // 2 - 20
    center = (size // 2, size // 2)

    try:
        font = ImageFont.truetype("Arial.ttf", 28)
    except Exception:
        font = ImageFont.load_default()

    images = []

    for f in range(frames):
        t = f / (frames - 1)
        rot = start_rotation + (final_rotation - start_rotation) * _ease_out_cubic(t)

        im = Image.new("RGB", (size, size), BG)
        draw = ImageDraw.Draw(im)

        bbox = [
            center[0] - radius,
            center[1] - radius,
            center[0] + radius,
            center[1] + radius,
        ]

        for i, val in enumerate(WHEEL_VALUES):
            color = PALE_PINK if i % 2 == 0 else PALE_BLUE
            a0 = rot + i * seg_angle
            a1 = rot + (i + 1) * seg_angle
            draw.pieslice(bbox, start=a0, end=a1, fill=color, outline=(230, 230, 230), width=3)

            mid = math.radians((a0 + a1) / 2)
            tx = center[0] + int(math.cos(mid) * (radius * 0.62))
            ty = center[1] + int(math.sin(mid) * (radius * 0.62))
            label = str(val)
            tw, th = draw.textbbox((0, 0), label, font=font)[2:]
            draw.text((tx - tw / 2, ty - th / 2), label, fill=TEXT_DARK, font=font)

        draw.ellipse(
            [center[0]-28, center[1]-28, center[0]+28, center[1]+28],
            fill=(0, 0, 0),
            outline=(220, 220, 220),
            width=3,
        )

        px, py = center[0], center[1] - radius - 4
        pointer = [(px, py), (px - 16, py + 34), (px + 16, py + 34)]
        draw.polygon(pointer, fill=(0, 0, 0), outline=(0, 0, 0))

        images.append(im)

    buf = io.BytesIO()
    imageio.mimsave(buf, images, format="GIF", duration=frame_duration)
    return buf.getvalue()


class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()


client = MyClient()

@client.tree.command(name="spin", description="Spin the wheel 🎡")
async def spin(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)

    result = random.choice(WHEEL_VALUES)
    gif_bytes = make_spin_gif(result)

    file = discord.File(fp=io.BytesIO(gif_bytes), filename="spin.gif")

    # 1) Send the spinning wheel first (no amount revealed)
    await interaction.followup.send(
        content="🎡 **Spinning...**",
        file=file,
    )

    import asyncio
    await asyncio.sleep(8)

    # 2) Reveal the amount after the wheel stops
    await interaction.followup.send(
        content=(
            f"✅ **Landed on: {result}**\n"
            f"🎁 Optional gift link: {PAYMENT_LINKTREE}"
        )
    )

client.run(TOKEN)

