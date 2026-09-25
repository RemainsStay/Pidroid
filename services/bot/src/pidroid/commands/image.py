import os
from io import BytesIO
from typing import final

import discord
from discord.ext import commands
from discord.ext.commands import BadArgument, Context
from PIL import Image, ImageSequence

from pidroid.client import Pidroid
from pidroid.models.categories import RandomCategory
from pidroid.utils import http, run_in_executor
from pidroid.utils.file import Resource

MAX_IMAGE_SIZE = 7 * 1024 * 1024  # 7 MiB

async def load_image_from_url(client: Pidroid, url: str) -> Image.Image:
    """Load an image from a URL and return it as a PIL Image object."""
    async with await http.get(client, url) as r:
        payload = await r.read()
    return Image.open(BytesIO(payload))

async def handle_attachment(ctx: Context[Pidroid]) -> tuple[discord.Attachment, str]:
    """Returns None or discord.Attachment after assuring it is safe to use."""
    attachments = ctx.message.attachments
    if len(attachments) < 1:
        raise BadArgument("I could not find any attachments!")

    attachment = attachments[0]

    filename = attachment.filename
    extension = os.path.splitext(filename)[1]
    if extension.lower() not in [".png", ".jpg", ".jpeg"]:
        raise BadArgument("Unsupported file extension. Only image files of .png, .jpg and .jpeg extensions are supported!")

    if attachment.size > MAX_IMAGE_SIZE:
        raise BadArgument("Your image is too big. Please upload an image that is at most 7 MiBs in size.")

    return attachment, extension

@final
class ImageManipulationCommandCog(commands.Cog):
    """Class responsible for implementing commands primarily used for image manipulation."""

    def __init__(self, client: Pidroid) -> None:
        super().__init__()
        self.client = client

    @commands.command(
        name="bonk",
        brief="Bonks the specified member.",
        usage="<member>",
        extras={
            "category": RandomCategory,
        },
    )
    @commands.bot_has_permissions(send_messages=True, attach_files=True)
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.user)
    @commands.max_concurrency(number=1, per=commands.BucketType.user)
    @commands.max_concurrency(number=10, per=commands.BucketType.guild)
    async def bonk_command(self, ctx: Context[Pidroid], member: discord.Member):
        if ctx.author.id == member.id:
            raise BadArgument("You cannot bonk yourself!")

        async with ctx.channel.typing():
            author_avatar = await load_image_from_url(self.client, ctx.author.display_avatar.with_size(128).url)
            member_avatar = await load_image_from_url(self.client, member.display_avatar.with_size(128).url)
            canvas_image = await run_in_executor(Image.open, fp=Resource('bonk.jpg'))

            canvas_image.paste(author_avatar, (215, 80))
            canvas_image.paste(member_avatar, (546, 290))
            author_avatar.close()
            member_avatar.close()

            output_stream = BytesIO()
            canvas_image.save(output_stream, format="jpeg")
            canvas_image.close()
            output_stream.seek(0)
            await ctx.reply(content=member.mention, file=discord.File(output_stream, filename='image.jpg'))

        # Close the streams
        output_stream.close()

    @commands.command(
        name="memefy",
        brief="Updates meme uploaded as attachment to comply within the German copyright regulations.",
        usage="[bool whether to retain ratio]",
        extras={
            "category": RandomCategory,
        },
    )
    @commands.bot_has_permissions(send_messages=True, attach_files=True)
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.user)
    @commands.max_concurrency(number=1, per=commands.BucketType.user)
    @commands.max_concurrency(number=10, per=commands.BucketType.guild)
    async def memefy_command(self, ctx: Context[Pidroid], retain_aspect_ratio: bool = False):
        async with ctx.channel.typing():
            attachment, extension = await handle_attachment(ctx)

            # Load the attachment
            attachment_image = await load_image_from_url(self.client, attachment.url)

            # Change the image size
            sizes = (128, 128)
            message = "Meme has been updated to comply with the German regulations"
            if retain_aspect_ratio:
                orig_w, orig_h = attachment_image.size
                ratio = 12800 / orig_w
                sizes = (128, round(ratio * orig_h / 100))
                message += "-ish..."
            attachment_image = attachment_image.resize(sizes, Image.LANCZOS)

            # Save the file
            output_file = BytesIO()
            attachment_image.save(output_file, format="png")
            attachment_image.close()

            # Send it
            output_file.seek(0)
            await ctx.reply(
                content=message,
                file=discord.File(output_file, filename=f'image{extension}')
            )
        output_file.close()

    @commands.command(
        name="jpeg",
        brief="Downscales an image to glorious JPEG quality.",
        usage="<quality(1-10)>",
        aliases=["hank"],
        extras={
            "category": RandomCategory,
        },
    )
    @commands.bot_has_permissions(send_messages=True, attach_files=True)
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.user)
    @commands.max_concurrency(number=1, per=commands.BucketType.user)
    @commands.max_concurrency(number=10, per=commands.BucketType.guild)
    async def jpeg_command(self, ctx: Context[Pidroid], quality: int = 1):
        if quality < 1 or quality > 10:
            raise BadArgument("Quality value must be a number between 1 and 10.")

        async with ctx.channel.typing():
            attachment, _ = await handle_attachment(ctx)

            attachment_image = await load_image_from_url(self.client, attachment.url)

            # Convert to RGB
            attachment_image = attachment_image.convert("RGB")

            # Save with the quality setting
            output_stream = BytesIO()
            attachment_image.save(output_stream, format="JPEG", quality=quality)
            attachment_image.close()
            output_stream.seek(0)
            await ctx.reply(content='Do I look like I know what a JPEG is?', file=discord.File(output_stream, filename='compression.jpg'))
        output_stream.close()

    @commands.command(
        name="headpat",
        brief="Headpats the specified member.",
        usage="<member>",
        extras={
            "category": RandomCategory,
        },
    )
    @commands.bot_has_permissions(send_messages=True, attach_files=True)
    @commands.cooldown(rate=1, per=25, type=commands.BucketType.user)
    @commands.max_concurrency(number=1, per=commands.BucketType.user)
    @commands.max_concurrency(number=5, per=commands.BucketType.guild)
    async def headpat_command(self, ctx: Context[Pidroid], member: discord.Member):
        if ctx.author.id == member.id:
            raise BadArgument("You cannot headpat yourself, ask someone else to be nice")

        async with ctx.channel.typing():
            member_avatar = await load_image_from_url(self.client, member.display_avatar.with_size(256).url)
            headpat_gif = await run_in_executor(Image.open, fp=Resource('pat.gif'))

            frames: list[Image.Image] = []
            for frame in ImageSequence.Iterator(headpat_gif):
                composite_frame = Image.new(member_avatar.mode, (256,356))
                rgba_frame = frame.convert("RGBA")
                composite_frame.paste(member_avatar, (0, 100))
                composite_frame.paste(rgba_frame, (0, 0), rgba_frame)
                composite_frame.info["disposal"] = 2
                frames.append(composite_frame)

            member_avatar.close()
            headpat_gif.close()

            output_stream = BytesIO()
            frames[0].save(
                output_stream,
                format="gif",
                save_all=True,
                append_images=frames[1:-1],
                duration=60,
                loop=0,
            )
            headpat_gif.close()
            output_stream.seek(0)
            await ctx.reply(content=member.mention, file=discord.File(output_stream, filename='headpat.gif'))

        # Close the streams
        output_stream.close()


async def setup(client: Pidroid) -> None:
    await client.add_cog(ImageManipulationCommandCog(client))
