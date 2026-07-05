import discord
from discord import app_commands
import random
import datetime
import os
import asyncio  # Pridajte tento import
import json
import subprocess
from dotenv import load_dotenv


# Konštanty
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
GUILD_ID = 617112204063539229  # ID tvojho Discord servera
# Predstavte si, že toto je ID vášho hláškového kanála.
# Nahraďte ho skutočným ID kanála, kde chcete, aby bot pracoval.
HLASKOVY_KANAL_ID = 1121507916374085632
ADRIAN_LOG_KANAL_ID = 1396295485094105148
HALLOWEEN = False  # Nastavte na True počas Halloween obdobia

MAPPING_FILE = "entrance_mapping.json"

def load_entrance_mapping():
    if not os.path.exists(MAPPING_FILE):
        return {}
    try:
        with open(MAPPING_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Prevedenie textových kľúčov na integer pre ID používateľov
            return {int(k): v for k, v in data.items()}
    except Exception as e:
        print(f"Chyba pri načítaní mappingu: {e}")
        return {}

def save_entrance_mapping(mapping):
    try:
        # Prevedenie kľúčov na string pre uloženie do JSONu
        data = {str(k): v for k, v in mapping.items()}
        with open(MAPPING_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Chyba pri ukladaní mappingu: {e}")

def normalize_audio(input_path: str, output_path: str) -> bool:
    """Normalizuje hlasitosť pomocou ffmpeg filtra loudnorm (EBU R128)."""
    command = [
        "ffmpeg",
        "-i", input_path,
        "-filter:a", "loudnorm=I=-23:TP=-1.5:LRA=11",
        "-y",
        output_path
    ]
    try:
        subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Chyba pri normalizácii zvuku {input_path}: {e.stderr.decode('utf-8', errors='ignore')}")
        return False

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
    znami_ludia = load_entrance_mapping()
    if message.author.id in znami_ludia:
        # Ak je autor známy, použijeme jeho prezývku
        author_name = znami_ludia[message.author.id]["name"]
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


# --- Slash príkazy pre správu vstupných zvukov ---


@tree.command(name="nastav_vstup", description="Nastaví a normalizuje tvoj vlastný vstupný zvuk pri pripojení do voice kanála.")
@app_commands.describe(
    subor="Zvukový súbor (napr. MP3, WAV, OGG, M4A)",
    meno="Prezývka, ktorú bot použije pri tvojich hláškach (voliteľné)"
)
async def nastav_vstup(
    interaction: discord.Interaction,
    subor: discord.Attachment,
    meno: str = None
):
    # Kontrola typu súboru podľa koncovky alebo content_type
    ext = os.path.splitext(subor.filename.lower())[1]
    is_audio = (subor.content_type and subor.content_type.startswith("audio/")) or ext in ['.mp3', '.wav', '.ogg', '.m4a', '.aac', '.flac', '.webm']
    
    if not is_audio:
        await interaction.response.send_message(
            "Prosím, nahraj platný zvukový súbor (napr. MP3, WAV, OGG, M4A)!",
            ephemeral=True
        )
        return

    # Obmedzenie veľkosti súboru na 10MB
    if subor.size > 10 * 1024 * 1024:
        await interaction.response.send_message(
            "Súbor je príliš veľký! Maximálna veľkosť je 10MB.",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)

    temp_dir = os.path.join("entrance", "temp")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
        
    temp_filename = f"temp_{interaction.user.id}_{subor.filename}"
    temp_path = os.path.join(temp_dir, temp_filename)
    
    try:
        # Uloženie dočasného súboru
        await subor.save(temp_path)
        
        normalized_filename = f"user_{interaction.user.id}.mp3"
        normalized_path = os.path.join("entrance", normalized_filename)
        
        # Normalizácia
        success = normalize_audio(temp_path, normalized_path)
        
        if not success:
            await interaction.followup.send(
                "Nepodarilo sa normalizovať alebo spracovať zvukový súbor. Skontroluj, či nie je poškodený.",
                ephemeral=True
            )
            return
            
        # Aktualizácia mappingu
        znami_ludia = load_entrance_mapping()
        
        # Ak meno nie je špecifikované, použijeme existujúce meno alebo display name na Discorde
        display_name = meno or (znami_ludia.get(interaction.user.id, {}).get("name") or interaction.user.display_name)
        
        znami_ludia[interaction.user.id] = {
            "name": display_name,
            "sound_file": normalized_filename
        }
        save_entrance_mapping(znami_ludia)
        
        await interaction.followup.send(
            f"Tvoj vstupný zvuk bol úspešne uložený a normalizovaný! Prezývka: **{display_name}**.",
            ephemeral=True
        )
    except Exception as e:
        print(f"Chyba pri spracovaní nahraného zvuku: {e}")
        await interaction.followup.send(
            f"Nastala neočakávaná chyba pri spracovaní zvuku: {e}",
            ephemeral=True
        )
    finally:
        # Vyčistenie dočasného súboru
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                print(f"Chyba pri mazaní dočasného súboru: {e}")


@tree.command(name="odstran_vstup", description="Odstráni tvoj vstupný zvuk pre príchod do voice kanálu.")
async def odstran_vstup(interaction: discord.Interaction):
    znami_ludia = load_entrance_mapping()
    
    if interaction.user.id not in znami_ludia:
        await interaction.response.send_message(
            "Nemáš nastavený žiadny vstupný zvuk.",
            ephemeral=True
        )
        return
        
    await interaction.response.defer(ephemeral=True)
    
    user_info = znami_ludia.pop(interaction.user.id)
    sound_file = user_info.get("sound_file")
    
    if sound_file:
        file_path = os.path.join("entrance", sound_file)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Chyba pri mazaní súboru {file_path}: {e}")
                
    save_entrance_mapping(znami_ludia)
    await interaction.followup.send(
        "Tvoj vstupný zvuk a prezývka boli odstránené.",
        ephemeral=True
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

    znami_ludia = load_entrance_mapping()
    # Kontrola, či je používateľ známy a má priradený súbor
    if member.id in znami_ludia:
        sound_file = znami_ludia[member.id].get("sound_file")
        if sound_file:
            subor = os.path.join(
                "entrance",
                sound_file if not HALLOWEEN else "jumpscare.mp3",
            )
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
