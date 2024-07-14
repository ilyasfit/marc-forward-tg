import discord
from discord.ext import commands
from telethon import TelegramClient, events, types
import io
import asyncio
import os
from dotenv import load_dotenv

from openai import AsyncOpenAI

# Load environment variables
load_dotenv()

# Initialize openai client
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Discord bot setup
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DISCORD_CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))

# Telegram setup
TELEGRAM_API_ID = int(os.getenv('TELEGRAM_API_ID'))
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
TELEGRAM_PHONE = os.getenv('TELEGRAM_PHONE')
TELEGRAM_CHANNEL_USERNAME = os.getenv('TELEGRAM_CHANNEL_USERNAME')

# Initialize Discord bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

# Initialize Telegram client
tg_client = TelegramClient('telegram_session', TELEGRAM_API_ID, TELEGRAM_API_HASH)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')


async def reformat_message(message):
    # Remove the account tag
    news = message.split('\n')[0].strip()

    prompt = f"""
    Teile die Nachricht, die in den eckigen Klammern eingebettet ist. 
    Deine Mitteilung beinhaltet einen Witz oder eine lustige Bemerkung über deine Vorliebe zum Dressurreiten, erwähne das Dressurreiten jedoch maximal ein Mal! 
    Deine Mitteilungen sollten fachkundig und präzise sein, aber auch eine charmante Note haben, die deine Liebe zum Dressurreiten zeigt. 
    Hier sind einige Beispiele, wie du deine Mitteilungen gestalten kannst, um eine gute Verbindung zwischen aktuellen Ereignissen und Dressurreiten herzustellen: 

    Zuerst teilst du die Nachricht, dann machst du eine humorvolle Bemerkung / Kommentar (mit deinem Dressurreiter-Jargon) über die News im Kontext auf den Kryptomarkt.

    So sieht dein Nachrichtenformat aus:

    "## :rotating_light: **Aufgepasst Kameraden!** :rotating_light: \n\n > (hier fügst du die Nachricht ein, lasse das "JUST IN" oder "BREAKING" aus und übersetze sie auf deutsch) \n\n (hier fügst du deinen Kommentar ein)"
    In den Klammern ist die Anweisung, was du wo und wie einfügen sollst.
    
    Hier sind 3 Beispiele, wie du eine News gestalten kannst:

    "## :rotating_light: **Achtung Kameraden!** :rotating_light: \n\n
    > Elon Musk sagt, er unterstützt Präsident Donald Trump voll und ganz nach dem Angriff während der Kundgebung.\n\n

    Das ist ja fast so aufregend wie ein Dressurwettbewerb bei den Olympischen Spielen! Ob die Märkte jetzt einen eleganten Galopp oder eine wilde Buckelshow hinlegen?"

    "## :rotating_light: **Es gibt Neuigkeiten!** :rotating_light: \n\n
> Elon Musk sagt, er unterstützt Präsident Donald Trump voll und ganz nach dem Angriff während der Kundgebung.\n\n

Ah, das ist so klassisch wie eine Dressurkür! Wird der Kryptomarkt eine elegante Pirouette drehen oder über die Hürden stolpern?"

"## :rotating_light: **Sattelt auf Kameraden!** :rotating_light: \n\n
> Elon Musk sagt, er unterstützt Präsident Donald Trump voll und ganz nach dem Angriff während der Kundgebung. \n\n

Wie bei einem guten Dressurtraining ist es wichtig, auf Details zu achten. Wird der Kryptomarkt jetzt im Einklang traben oder aus dem Sattel geworfen werden?"

Achte darauf, dass dein Kommentar zum Kontext passt und humorvoll zu deinem Charakter passt!
    
    
    Bette die Mitteilung nicht in Anführungszeichen ein. Du teilst nur Nachrichten, die relevant und wichtig sind. Du machst die Anspielung (in Bezug auf das Reiten & Dressur) maximal ein Mal pro Mitteilung! 
    
    Die Nachricht: [{news}]
    """

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": "Formuliere die Nachricht um."}
        ],
        max_tokens=150
    )

    return response.choices[0].message.content


async def forward_messages():
    await bot.wait_until_ready()
    channel = bot.get_channel(DISCORD_CHANNEL_ID)

    @tg_client.on(events.NewMessage(chats=TELEGRAM_CHANNEL_USERNAME))
    async def telegram_handler(event):
        raw_message = event.message
        
        # Verarbeite zuerst den Textinhalt
        if raw_message.text:
            message = await reformat_message(raw_message.text)
            await channel.send(f"{message}")
        
        # Überprüfe, ob die Nachricht Medienanhänge hat
        if raw_message.media:
            # Lade die Mediendatei herunter
            file = await tg_client.download_media(raw_message.media, file=bytes)
            
            # Bestimme den Dateityp
            if isinstance(raw_message.media, (types.MessageMediaPhoto, types.MessageMediaDocument)):
                if isinstance(raw_message.media, types.MessageMediaPhoto):
                    filename = 'photo.jpg'
                else:
                    filename = raw_message.file.name or 'document'
                
                # Sende die Datei an Discord
                discord_file = discord.File(fp=io.BytesIO(file), filename=filename)
                await channel.send(file=discord_file)
            
            elif isinstance(raw_message.media, types.MessageMediaVideo):
                # Für Videos müssen wir möglicherweise zusätzliche Verarbeitung durchführen
                filename = 'video.mp4'
                discord_file = discord.File(fp=io.BytesIO(file), filename=filename)
                await channel.send(file=discord_file)

    await tg_client.start(phone=TELEGRAM_PHONE)
    print("Telegram client started")
    await tg_client.run_until_disconnected()

# Run both Discord bot and Telegram client
async def main():
    await asyncio.gather(
        bot.start(DISCORD_TOKEN),
        forward_messages()
    )

if __name__ == "__main__":
    asyncio.run(main())