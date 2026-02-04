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
PALE_PINK = (255, 160, 200)   # soft glossy pink
PALE_BLUE = (215, 190, 235)   # soft mauve (less purple)
TEXT_DARK = (0, 0, 0)         # black text
BG = (190, 215, 200)   # slightly darker sage green

SPIN_SECONDS = 8
REVEAL_BUFFER = 0.5



def _ease_out_cubic(t: float) -> float:
    return 1 - (1 - t) ** 3

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

def make_spin_gif(values: list[int], result_value: int, size: int = 420) -> bytes:
    SPIN_SECONDS = 8
    frames = 120
    frame_duration = 0.058

    

    idx = values.index(result_value)
    n = len(values)
    seg_angle = 360 / n

    pointer_angle = -90
    chosen_center = (idx + 0.5) * seg_angle
    final_rotation = pointer_angle - chosen_center

    extra_turns = 4 * 360
    start_rotation = final_rotation + extra_turns


    radius = size // 2 - 20
    center = (size // 2, size // 2)

    # Auto font size: bigger for fewer segments, smaller for many segments
    font_size = 42 if len(values) <= 14 else 28
    try:
        # Works on most Linux servers (Render)
        font = ImageFont.truetype("DejaVuSans.ttf", font_size)
    except Exception:
        try:
            # Works on some Macs/Windows if available
            font = ImageFont.truetype("Arial.ttf", font_size)
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

        for i, val in enumerate(values):
            a0 = rot + i * seg_angle
            a1 = a0 + seg_angle

            draw.pieslice(
                bbox,
                start=a0,
                end=a1,
                fill=PALE_PINK if i % 2 == 0 else PALE_BLUE,
                outline=(255, 255, 255),
                width=3,
            )


           



            mid = math.radians((a0 + a1) / 2)
            tx = center[0] + int(math.cos(mid) * (radius * 0.62))
            ty = center[1] + int(math.sin(mid) * (radius * 0.62))
            label = str(val)
            tw, th = draw.textbbox((0, 0), label, font=font)[2:]
            draw.text((tx - tw / 2, ty - th / 2), label, fill=TEXT_DARK, font=font)
        # White border around the wheel
        
        draw.ellipse(
            bbox,
            outline=(255, 255, 255),
            width=4,
        )

        draw.ellipse(
            [center[0]-28, center[1]-28, center[0]+28, center[1]+28],
            fill=(0, 0, 0),
            outline=(220, 220, 220),
            width=3,
        )


        px, py = center[0], center[1] - radius - 4
        pointer = [(px, py), (px - 16, py + 34), (px + 16, py + 34)]
        draw.polygon(pointer, fill=(255, 255, 255))


        images.append(im)

    buf = io.BytesIO()
    imageio.mimsave(buf, images, format="GIF", duration=frame_duration)
    return buf.getvalue()

client = MyClient()

@client.tree.command(name="spin", description="Spin a number in fives between your min and max 🎡")
@app_commands.describe(min="Minimum (10–200, must be multiple of 5)", max="Maximum (10–200, must be multiple of 5)")
async def spin(interaction: discord.Interaction, min: int, max: int):


    await interaction.response.defer(thinking=True)

    # Validate inputs
    if min < 10:
        await interaction.followup.send("❌ Minimum must be at least 10.")
        return
    if max > 200:
        await interaction.followup.send("❌ Maximum must be 200 or less.")
        return
    if min >= max:
        await interaction.followup.send("❌ Minimum must be less than maximum.")
        return
    if (min % 5) != 0 or (max % 5) != 0:
        await interaction.followup.send("❌ Min and max must be multiples of 5 (e.g., 10, 15, 20…).")
        return

    # Pick a number in steps of 5
    values = list(range(min, max + 1, 5))
    result = random.choice(values)
    gif_bytes = make_spin_gif(values, result)

    file = discord.File(fp=io.BytesIO(gif_bytes), filename=f"spin_{min}_{max}_{result}.gif")


   
  
    

    


    # 1) Send the spinning wheel first (no amount revealed)
    await interaction.followup.send(
        content="🎡 **Spinning...**",
        file=file,
    )

    import asyncio
    await asyncio.sleep(10)


    # 2) Reveal the amount after the wheel stops
    await interaction.followup.send(
        content=(
            f"✅ **Landed on: {result}**\n"
            f"🎁 Optional gift link: {PAYMENT_LINKTREE}"
        )
    )

client.run(TOKEN)

