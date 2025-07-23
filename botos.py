import discord
from discord import app_commands, ui
import random
import datetime
import os
import aiohttp
from dotenv import load_dotenv


# Konštanty
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
GUILD_ID = 617112204063539229  # ID tvojho Discord servera
# Predstavte si, že toto je ID vášho hláškového kanála.
# Nahraďte ho skutočným ID kanála, kde chcete, aby bot pracoval.
HLASKOVY_KANAL_ID =  1121507916374085632
ADRIAN_LOG_KANAL_ID = 1396295485094105148

# Známi ľudia na serveri, ktorý majú vlastné prezývky
ZNAMI_LUDIA = {
    343823564493029376: ["Tomáš"], 
    106740016364937216: ["Jakub"],
    431438944232669184: ["Matej"],
    415894338438955008: ["Adrian", 'boss-in-this-gym.mp3'],
    212945990221692928: ["Daimes", 'daimesentry.mp3'],
}

# Adrianove ID pre kontextové menu
ADRIAN_ID = 415894338438955008  # ID používateľa,

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
    print(f'Prihlásený ako {client.user}')
    await tree.sync()  # Synchronizácia všetkých príkazov
    print("Príkazy synchronizované!")

# --- Kontextové menu pre ukladanie hlášok ---

@tree.context_menu(name="Uložiť hlášku")
async def save_hlaska(interaction: discord.Interaction, message: discord.Message):
    """
    Uloží vybranú správu ako hlášku do špecifikovaného kanála
    a pridá informácie o autorovi.
    """
    hlaskovy_kanal = client.get_channel(HLASKOVY_KANAL_ID)

    if not hlaskovy_kanal:
        await interaction.response.send_message(
            f"Chyba: Kanál s ID {HLASKOVY_KANAL_ID} sa nenašiel. Skontrolujte ID.",
            ephemeral=True
        )
        return

    # Formátovanie hlášky
    if message.author.id in ZNAMI_LUDIA:
        # Ak je autor známy, použijeme jeho prezývku
        author_name = ZNAMI_LUDIA[message.author.id][0]
    else:
        # Inak použijeme štandardné meno autora
        author_name = message.author.display_name
    hlaska_text = f"\"{message.content}\" - {author_name}"

    # Odoslanie do hláškového kanála
    try:
        await hlaskovy_kanal.send(hlaska_text)
        await interaction.response.send_message("Hláška úspešne uložená!", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message(
            "Nemám oprávnenie písať do hláškového kanála. Skontrolujte povolenia.",
            ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(
            f"Nastala chyba pri ukladaní hlášky: {e}",
            ephemeral=True
        )


# --- Slash príkaz pre náhodnú hlášku ---

@tree.command(name="nahodna", description="Vyberie náhodnú správu z hláškového kanála.")
async def nahodna_hlaska(interaction: discord.Interaction):
    """
    Vyberie a pošle náhodnú správu z preddefinovaného hláškového kanála.
    """
    hlaskovy_kanal = client.get_channel(HLASKOVY_KANAL_ID)

    if not hlaskovy_kanal:
        await interaction.response.send_message(
            f"Chyba: Kanál s ID {HLASKOVY_KANAL_ID} sa nenašiel. Skontrolujte ID.",
            ephemeral=True
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
                "V hláškovom kanáli nie sú žiadne správy na výber.",
                ephemeral=True
            )
            return

        random_message = random.choice(messages)
        await interaction.response.send_message(f"> {random_message}")

    except discord.Forbidden:
        await interaction.response.send_message(
            "Nemám oprávnenie čítať históriu správ v hláškovom kanáli. Skontrolujte povolenia.",
            ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(
            f"Nastala chyba pri načítavaní hlášok: {e}",
            ephemeral=True
        )

@client.event
async def on_voice_state_update(member, before, after):
    """
    Sleduje zmeny voice channel stavu a pripojí bota k používateľovi Adrianovi,
    ak sa pripojí do hlasového kanála.
    """
    # Kontrola, či sa jedná o správneho používateľa
    try:
        subor = ZNAMI_LUDIA[member.id][1]

    except Exception as e:
        print(f"Človek nemá svoj entrance {e}")
        return
        
    
    # Kontrola, či sa používateľ pripojil do hlasového kanála
    if before.channel is None and after.channel is not None:
        voice_channel = after.channel
        
        try:
            # Pripojenie bota do hlasového kanála
            voice_client = await voice_channel.connect()
            
            # Počkajte, chvíľu, nech každý má čas sa pripojiť
            await discord.utils.sleep_until(discord.utils.utcnow() + datetime.timedelta(seconds=0.2))

            # Prehranie súboru boss-in-this-gym.mp3
            voice_client.play(discord.FFmpegPCMAudio(subor))
            
            # Čakanie, kým sa súbor neprehráva
            while voice_client.is_playing():
                await discord.utils.sleep_until(discord.utils.utcnow())
            
            # Odpojenie po prehratí
            await voice_client.disconnect()
            
        except Exception as e:
            print(f"Chyba pri pripájaní alebo prehrávaní: {e}")
    
    # Odpojenie bota ak sa používateľ odpojí
    elif before.channel is not None and after.channel is None:
        for voice_client in client.voice_clients:
            if voice_client.guild == member.guild:
                await voice_client.disconnect()
                
@client.event
async def on_message(message):
    """
    Sleduje správy od používateľa Adrian a preposiela ich do špecifikovaného kanála,
    ak nie sú linky alebo obrázky.
    """
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
    if content.startswith(('http://', 'https://', 'www.')):
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
        await target_channel.send(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {content}")
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
    image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.webp']
    images = [f for f in os.listdir(reactions_folder) 
                if any(f.lower().endswith(ext) for ext in image_extensions)]
    
    if not images:
        print(f"Žiadne obrázky v zložke {reactions_folder}.")
        return
    
    # Výber náhodného obrázka
    random_image = random.choice(images)
    image_path = os.path.join(reactions_folder, random_image)
    
    try:
        with open(image_path, 'rb') as f:
            picture = discord.File(f, random_image)
            await channel.send(file=picture)
    except Exception as e:
        print(f"Chyba pri posielaní obrázka: {e}")

# Spustenie bota
# Nahraďte "VÁŠ_TOKEN_BOTA" skutočným tokenom vášho Discord bota
client.run(TOKEN)
