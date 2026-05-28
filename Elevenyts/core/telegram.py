# telegram.py - Telegram Media Download Handler

import asyncio
import os
import time
import logging

from pyrogram import types

from Elevenyts import config
from Elevenyts.helpers import Media, buttons, utils

logger = logging.getLogger(__name__)


class Telegram:
    def __init__(self):
        """Initialize the Telegram download handler."""
        self.active = []
        self.events = {}
        self.last_edit = {}
        self.active_tasks = {}
        self.sleep = 5
        
        # ✅ 2GB limit for userbot (2048 MB)
        self.MAX_FILE_SIZE_BYTES = 2048 * 1024 * 1024  # 2GB
        logger.info(f"📁 Telegram file size limit: {self.MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB")

    def get_media(self, msg: types.Message) -> bool:
        return any([msg.audio, msg.document, msg.voice, msg.video])

    async def download(self, msg: types.Message, sent: types.Message) -> Media | None:
        msg_id = sent.id
        event = asyncio.Event()
        self.events[msg_id] = event
        self.last_edit[msg_id] = 0
        start_time = time.time()

        media = msg.audio or msg.voice or msg.video or msg.document
        is_video = bool(msg.video) or (msg.document and getattr(msg.document, "mime_type", "").startswith("video/"))
        file_id = getattr(media, "file_unique_id", None)
        file_ext = getattr(media, "file_name", "").split(".")[-1] if getattr(media, "file_name", "") else "mp4"
        file_size = getattr(media, "file_size", 0)
        file_title = getattr(media, "title", "Telegram File") or "Telegram File"
        duration = getattr(media, "duration", 0)

        if duration > config.DURATION_LIMIT:
            try:
                await sent.edit_text(sent.lang["play_duration_limit"].format(config.DURATION_LIMIT // 60))
            except Exception:
                pass
            return await sent.stop_propagation()

        # ✅ FIX: 2GB limit (2048 MB) - Userbot can handle this
        limit_mb = self.MAX_FILE_SIZE_BYTES // (1024 * 1024)
        if file_size > self.MAX_FILE_SIZE_BYTES:
            error_text = (
                f"<blockquote>❌ <b>File too large!</b>\n\n"
                f"📁 File size: <code>{utils.format_size(file_size)}</code>\n"
                f"📊 Maximum allowed: <code>{limit_mb} MB ({limit_mb // 1024}GB)</code>\n\n"
                f"💡 <i>Tip: Assistant (userbot) can handle up to {limit_mb // 1024}GB files.</i></blockquote>"
            )
            try:
                await sent.edit_text(error_text)
            except Exception:
                pass
            return await sent.stop_propagation()

        async def progress(current, total):
            if event.is_set():
                return

            now = time.time()
            if now - self.last_edit[msg_id] < self.sleep:
                return

            self.last_edit[msg_id] = now
            percent = current * 100 / total
            speed = current / (now - start_time or 1e-6)
            eta = utils.format_eta(int((total - current) / speed))
            text = sent.lang["dl_progress"].format(
                utils.format_size(current),
                utils.format_size(total),
                percent,
                utils.format_size(speed),
                eta,
            )

            try:
                await sent.edit_text(text, reply_markup=buttons.cancel_dl(sent.lang["cancel"]))
            except Exception:
                pass

        try:
            os.makedirs("downloads", exist_ok=True)
            
            file_path = f"downloads/{file_id}.{file_ext}"
            if not os.path.exists(file_path):
                if file_id in self.active:
                    try:
                        await sent.edit_text(sent.lang["dl_active"])
                    except Exception:
                        pass
                    return await sent.stop_propagation()

                self.active.append(file_id)
                task = asyncio.create_task(msg.download(file_name=file_path, progress=progress))
                self.active_tasks[msg_id] = task
                await task
                self.active.remove(file_id)
                self.active_tasks.pop(msg_id, None)
                
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"Download failed: {file_path}")
                    
                try:
                    await sent.edit_text(sent.lang["dl_complete"].format(round(time.time() - start_time, 2)))
                except Exception:
                    pass

            if duration >= 3600:
                duration_str = time.strftime("%H:%M:%S", time.gmtime(duration))
            else:
                duration_str = time.strftime("%M:%S", time.gmtime(duration))

            return Media(
                id=file_id,
                duration=duration_str,
                duration_sec=duration,
                file_path=file_path,
                message_id=sent.id,
                url=msg.link,
                title=file_title[:25],
                video=is_video,
            )
        except asyncio.CancelledError:
            return await sent.stop_propagation()
        except Exception as e:
            logger.error(f"Download error: {e}")
            try:
                await sent.edit_text(f"❌ Download failed: {str(e)[:100]}")
            except Exception:
                pass
            return None
        finally:
            self.events.pop(msg_id, None)
            self.last_edit.pop(msg_id, None)
            self.active = [f for f in self.active if f != file_id]

    async def cancel(self, query: types.CallbackQuery):
        event = self.events.get(query.message.id)
        task = self.active_tasks.pop(query.message.id, None)
        if event:
            event.set()

        if task and not task.done():
            task.cancel()
        if event or task:
            await query.edit_message_text(query.lang["dl_cancel"].format(query.from_user.mention))
        else:
            await query.answer(query.lang["dl_not_found"], show_alert=True)
