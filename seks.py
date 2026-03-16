import os, asyncio, re, threading
from telethon import TelegramClient, events, types
from telethon.sessions import StringSession
from flask import Flask

# --- AYARLAR ---
API_ID = 33077604
API_HASH = '119992704d1dd27a6ebf9d3327189204'
STRING_SESSION = 'BAHMDn8AHs8rPUXaTCfTP6LEmzw6BXnQDWkaxHQsKbkZOB5OROG6FQx2lToH5Z2xN-TRX0GyJlAtxhHWF8NkcYoAIUQy6shKfsuHW1vGrhb0eRT-8FuI4FnMQSQjZgTMrwDOtyzyAh-W2MgSl13Ai4JX8vKIW3oyNnn_wQDrioFbCrqiivHzY95nTaeXoQDcqmaOjEL7uufxs1v2NsTyxzv3S3o5IqaOLJCRPoGpu0AO9Rx4zzQnvgu5ENxqEzmy6_b4bytzF8afsAILwwZGHcrr3V-HfzEzwCu8ibAYmkF00pdHxF1fAEo-oOt4BknJRuiHpxK7JwBH8CCclC2W-Bcfc6QcVAAAAAICU-dvAA'

SUPER_ADMIN = 6534222591
AUTHORIZED_USERS = [SUPER_ADMIN]

PHONE_PATTERN = r'(?:\+90|0)?\s*[5]\d{2}\s*\d{3}\s*\d{2}\s*\d{2}'
MENTION_PATTERN = r'@(\w+)'
LINK_PATTERN = r'(?:t\.me|telegram\.me)\/\w+'

group_modes = {}
client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
app = Flask(__name__)

@app.route('/')
def home(): return "Sistem Aktif"

@client.on(events.NewMessage)
async def handler(event):
    if not event.chat: return
    chat_id = event.chat_id
    sender_id = event.sender_id
    text_raw = event.raw_text or ""

    # 1. KANAL/ANONİM ENGELLE (Sessiz)
    if event.sender_id is None or isinstance(event.sender, types.Channel):
        try:
            await event.delete()
            return
        except: pass

    # 2. YETKİ YÖNETİMİ (Sadece SUPER_ADMIN)
    if sender_id == SUPER_ADMIN:
        if text_raw.startswith("/auth") and event.is_reply:
            reply = await event.get_reply_message()
            u_id = reply.sender_id
            if u_id not in AUTHORIZED_USERS:
                AUTHORIZED_USERS.append(u_id)
                return await event.respond(f"`{u_id}` sekse alındı")
        
        elif text_raw.startswith("/unauth") and event.is_reply:
            reply = await event.get_reply_message()
            u_id = reply.sender_id
            if u_id != SUPER_ADMIN and u_id in AUTHORIZED_USERS:
                AUTHORIZED_USERS.remove(u_id)
                return await event.respond(f"`{u_id}` seksten cıkartıldı")

    # 3. YÖNETİCİ KOMUTLARI
    if sender_id in AUTHORIZED_USERS:
        cmd = text_raw.lower().strip()
        if cmd == "/am":
            group_modes[chat_id] = "aktifmedya"
            return await event.respond("seksler aktif")
        elif cmd == "/dm":
            group_modes.pop(chat_id, None)
            return await event.respond("seksler pasif")
        elif cmd == "/ac":
            group_modes[chat_id] = "aktifchat"
            return await event.respond("seks kapandı")
        elif cmd == "/dc":
            group_modes.pop(chat_id, None)
            return await event.respond("seks açıldı")

    # 4. MUAFİYET (Adminler ve Botlar)
    sender = await event.get_sender()
    if sender_id in AUTHORIZED_USERS or (sender and hasattr(sender, 'bot') and sender.bot):
        return

    # 5. AKTİF CHAT KİLİDİ
    current_mode = group_modes.get(chat_id)
    if current_mode == "aktifchat":
        try: await event.delete()
        except: pass
        return

    # 6. REKLAM, NUMARA VE KANAL MENTION KONTROLÜ
    text_lower = text_raw.lower()
    is_phone = re.search(PHONE_PATTERN, text_lower)
    is_link = re.search(LINK_PATTERN, text_lower)
    mentions = re.findall(MENTION_PATTERN, text_raw)
    
    is_bad_mention = False
    if mentions:
        for m in mentions:
            try:
                entity = await client.get_entity(m)
                if isinstance(entity, (types.Channel, types.Chat)):
                    is_bad_mention = True
                    break
            except: continue

    # Eğer yasaklı içerik varsa
    if is_phone or is_link or is_bad_mention or event.fwd_from:
        try:
            await event.delete()
            # İstediğin o sert tepki
            rep = await event.respond("seks anani sikerim")
            await asyncio.sleep(3)
            await rep.delete()
        except: pass
        return

    # 7. MEDYA FİLTRESİ
    if event.media and current_mode == "aktifmedya":
        if not (event.voice or event.video_note):
            try: await event.delete()
            except: pass

async def start_bot():
    await client.start()
    await client.run_until_disconnected()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=port), daemon=True).start()
    asyncio.run(start_bot())