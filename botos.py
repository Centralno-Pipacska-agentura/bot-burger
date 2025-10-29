import discord
from discord import app_commands
import random
import datetime
import os
import asyncio  # Pridajte tento import
from dotenv import load_dotenv


# Konštanty
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
GUILD_ID = 617112204063539229  # ID tvojho Discord servera
# Predstavte si, že toto je ID vášho hláškového kanála.
# Nahraďte ho skutočným ID kanála, kde chcete, aby bot pracoval.
HLASKOVY_KANAL_ID = 1121507916374085632
ADRIAN_LOG_KANAL_ID = 1396295485094105148
HALLOWEEN = True  # Nastavte na True počas Halloween obdobia

# Známi ľudia na serveri, ktorý majú vlastné prezývky a súbory pre vstup do hlasového kanála.
ZNAMI_LUDIA = {
    343823564493029376: ["Tomáš", "jixaw-metal-pipe-falling-sound.mp3"],
    106740016364937216: ["Jakub", "hoooo-snoring.mp3"],
    431438944232669184: ["Matej", "cartoon.mp3"],
    415894338438955008: ["Adrian", "boss-in-this-gym.mp3"],
    212945990221692928: ["Daimes", "daimesentry.mp3"],
    533283601580687374: ["Dávid", "x-files-theme.mp3"],
    697847107675226213: ["Grín", "cartoon.mp3"],
}

# Adrianove ID pre kontextové menu
ADRIAN_ID = 415894338438955008  # ID používateľa Adrian

# Nastavenie Intents, aby bot mohol čítať správy a reagovať na interakcie
intents = discord.Intents.default()
intents.message_content = True  # Potrebné na čítanie obsahu správ
intents.messages = True
intents.guilds = True

# Vytvorenie inštancie bota
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@client.event
async def on_ready():
    """Potvrdí, že bot je prihlásený a synchronizuje príkazy."""
    print(f"Prihlásený ako {client.user}")
    await tree.sync()  # Synchronizácia všetkých príkazov
    print("Príkazy synchronizované!")


# --- Kontextové menu pre ukladanie hlášok ---


@tree.context_menu(name="Uložiť hlášku")
async def save_hlaska(interaction: discord.Interaction, message: discord.Message):
    """
    Uloží vybranú správu ako hlášku do špecifikovaného kanála
    a pridá informácie o autorovi.
    """
    if interaction.guild_id != GUILD_ID:
        await interaction.response.send_message(
            "Tento príkaz je možné použiť iba na správach z konkrétneho servera.",
            ephemeral=True,
        )
        return

    hlaskovy_kanal = client.get_channel(HLASKOVY_KANAL_ID)

    if not hlaskovy_kanal:
        await interaction.response.send_message(
            f"Chyba: Kanál s ID {HLASKOVY_KANAL_ID} sa nenašiel. Skontrolujte ID.",
            ephemeral=True,
        )
        return

    # Formátovanie hlášky
    if message.author.id in ZNAMI_LUDIA:
        # Ak je autor známy, použijeme jeho prezývku
        author_name = ZNAMI_LUDIA[message.author.id][0]
    else:
        # Inak použijeme štandardné meno autora
        author_name = message.author.display_name
    hlaska_text = f'"{message.content}" - {author_name}'

    # Odoslanie do hláškového kanála
    try:
        await hlaskovy_kanal.send(hlaska_text)
        await interaction.response.send_message(
            "Hláška úspešne uložená!", ephemeral=True
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            "Nemám oprávnenie písať do hláškového kanála. Skontrolujte povolenia.",
            ephemeral=True,
        )
    except Exception as e:
        await interaction.response.send_message(
            f"Nastala chyba pri ukladaní hlášky: {e}", ephemeral=True
        )


# --- Slash príkaz pre náhodnú hlášku ---


@tree.command(name="nahodna", description="Vyberie náhodnú správu z hláškového kanála.")
async def nahodna_hlaska(interaction: discord.Interaction):
    """
    Vyberie a pošle náhodnú správu z preddefinovaného hláškového kanála.
    """
    if interaction.guild_id != GUILD_ID:
        await interaction.response.send_message(
            "Tento príkaz je možné použiť iba na správach z konkrétneho servera.",
            ephemeral=True,
        )
        return

    hlaskovy_kanal = client.get_channel(HLASKOVY_KANAL_ID)

    if not hlaskovy_kanal:
        await interaction.response.send_message(
            f"Chyba: Kanál s ID {HLASKOVY_KANAL_ID} sa nenašiel. Skontrolujte ID.",
            ephemeral=True,
        )
        return

    messages = []
    try:
        # Načítanie posledných 200 správ z kanála (kvôli limitácii API)
        async for message in hlaskovy_kanal.history(limit=200):
            if not message.author.bot:  # Ignorujeme správy od botov, ak nechceme, aby sa hláškovali vlastné správy bota
                messages.append(message.content)

        if not messages:
            await interaction.response.send_message(
                "V hláškovom kanáli nie sú žiadne správy na výber.", ephemeral=True
            )
            return

        random_message = random.choice(messages)
        await interaction.response.send_message(f"> {random_message}")

    except discord.Forbidden:
        await interaction.response.send_message(
            "Nemám oprávnenie čítať históriu správ v hláškovom kanáli. Skontrolujte povolenia.",
            ephemeral=True,
        )
    except Exception as e:
        await interaction.response.send_message(
            f"Nastala chyba pri načítavaní hlášok: {e}", ephemeral=True
        )


@client.event
async def on_voice_state_update(member, before, after):
    """
    Sleduje zmeny voice channel stavu a pripojí bota k používateľovi,
    ak sa pripojí do hlasového kanála.
    """
    # Ak je to bot samotný, nerieš
    if member.id == 1396106093519966283:
        return

    # Ak sa bot už pripája alebo je pripojený v tomto guild, počkaj
    for voice_client in client.voice_clients:
        if voice_client.guild == member.guild:
            if voice_client.is_connected():
                return  # Bot je už pripojený

    print(f"Latency: {client.latency * 1000:.2f} ms")

    # Kontrola, či je používateľ známy a má priradený súbor
    if member.id in ZNAMI_LUDIA:
        if ZNAMI_LUDIA[member.id][1]:
            subor = os.path.join("entrance", ZNAMI_LUDIA[member.id][1] if not HALLOWEEN else "jumpscare.mp3")
            if not os.path.exists(subor):
                print(f"Súbor {subor} neexistuje.")
                return
        else:
            print(f"Človek {member.name} nemá priradený súbor pre vstup.")
            return
    else:
        print(f"Človek {member.name} nie je známy, nemá priradený súbor pre vstup.")
        return

    # Kontrola, či sa používateľ pripojil do hlasového kanála
    if before.channel is None and after.channel is not None:
        voice_channel = after.channel

        # Kontrola oprávnení
        if not voice_channel.permissions_for(member.guild.me).connect:
            print(f"Bot nemá oprávnenie pripojiť sa do kanála {voice_channel.name}")
            return

        voice_client = None
        try:
            print(f"Pripájanie pre {member.name}")

            # Pripojenie bota do hlasového kanála s timeoutom
            voice_client = await asyncio.wait_for(
                voice_channel.connect(timeout=30.0, reconnect=False), timeout=10.0
            )

            # Kratšie čakanie
            await asyncio.sleep(0.5)

            # Kontrola, či je voice_client stále pripojený
            if voice_client.is_connected():
                # Vytvorenie audio source s optimalizovanými možnosťami (bez duplicitných -ac a -ar)
                audio_source = discord.FFmpegPCMAudio(
                    subor,
                    options="-bufsize 256k -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                )

                voice_client.play(audio_source)

                # Čakanie s timeoutom, kým sa súbor neprehráva
                max_wait = 30  # maximálne 30 sekúnd
                waited = 0
                while voice_client.is_playing() and waited < max_wait:
                    await asyncio.sleep(0.5)
                    waited += 0.5

        except asyncio.TimeoutError:
            print(f"Timeout pri pripájaní do voice kanála pre {member.name}")
        except discord.errors.ConnectionClosed as e:
            print(f"Voice pripojenie zatvorené: {e.code}")
        except Exception as e:
            print(f"Chyba pri pripájaní alebo prehrávaní pre {member.name}: {e}")
        finally:
            # Bezpečné odpojenie
            if voice_client and voice_client.is_connected():
                try:
                    await voice_client.disconnect(force=True)
                except Exception as e:
                    print(f"Chyba pri odpájaní: {e}")

    # Odpojenie bota ak sa používateľ odpojí
    elif before.channel is not None and after.channel is None:
        for voice_client in client.voice_clients:
            if voice_client.guild == member.guild:
                try:
                    await voice_client.disconnect(force=True)
                except Exception as e:
                    print(f"Chyba pri odpájaní po odchode používateľa: {e}")


@client.event
async def on_message(message):
    """
    Sleduje správy od používateľa Adrian a preposiela ich do špecifikovaného kanála,
    ak nie sú linky alebo obrázky.
    """
    # Kontrola, či je interakcia na správnom serveri
    if not message.guild or message.guild.id != GUILD_ID:
        return

    # Ignorovať správy od botov
    if message.author.bot:
        return

    # Kontrola, či sa jedná o správneho používateľa
    if message.author.id != ADRIAN_ID:
        return

    # Kontrola, či správa obsahuje len text (nie je link alebo obrázok)
    content = message.content.strip()

    # Kontrola, či správa nie je prázdna
    if not content:
        return

    # Kontrola, či správa nie je link
    if content.startswith(("http://", "https://", "www.")):
        return

    # Kontrola, či správa obsahuje prílohy (obrázky, súbory)
    if message.attachments:
        return

    # Získanie cieľového kanála
    target_channel = client.get_channel(ADRIAN_LOG_KANAL_ID)

    if not target_channel:
        print(f"Chyba: Kanál s ID {ADRIAN_LOG_KANAL_ID} sa nenašiel.")
        return

    try:
        # Preposielanie správy do cieľového kanála
        await target_channel.send(
            f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {content}"
        )
    except Exception as e:
        print(f"Chyba pri preposielaní správy: {e}")


async def send_random_reaction_image(channel):
    """
    Vyberie náhodný obrázok zo zložky 'reakcie' a pošle ho do kanála.
    """
    reactions_folder = "reakcie"

    if not os.path.exists(reactions_folder):
        print(f"Zložka {reactions_folder} neexistuje.")
        return

    # Získanie všetkých súborov obrázkov zo zložky
    image_extensions = [".png", ".jpg", ".jpeg", ".gif", ".webp"]
    images = [
        f
        for f in os.listdir(reactions_folder)
        if any(f.lower().endswith(ext) for ext in image_extensions)
    ]

    if not images:
        print(f"Žiadne obrázky v zložke {reactions_folder}.")
        return

    # Výber náhodného obrázka
    random_image = random.choice(images)
    image_path = os.path.join(reactions_folder, random_image)

    try:
        with open(image_path, "rb") as f:
            picture = discord.File(f, random_image)
            await channel.send(file=picture)
    except Exception as e:
        print(f"Chyba pri posielaní obrázka: {e}")


# Spustenie bota
# Nahraďte "VÁŠ_TOKEN_BOTA" skutočným tokenom vášho Discord bota
if TOKEN:
    client.run(TOKEN)
else:
    print("Chyba: TOKEN nie je nastavený. Skontrolujte .env súbor.")
