# Boot message
print("Booting up...")

import os
from datetime import datetime, timezone
import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Modal, TextInput, Select, UserSelect
from discord import SelectOption
from flask import Flask
from threading import Thread
import re

# ------------------- Keep Alive Webserver -------------------
app = Flask('')

@app.route('/')
def home():
    return "✅ Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()


# ------------------- Config -------------------
GUILD_ID = 1358184251216105683

# <<< AANGEPAST >>>
# Voeg hier de rol-ID toe die de /changelog en /embed commando's mag gebruiken.
EMBED_ROLE_ID = 1411138999124234471 

# Moderation roles allowed
ALLOWED_ROLES = {
    1358184251471822947,
}

UNBAN_ROLES = {
    1358184251471822947,
}

LOG_CHANNELS = {
    "ban": 1409219483897299026,
    "kick": 1409219531842519080,
    "warn": 1409219557901729973,
    "unban": 1409219582568169512,
}

WELCOME_CHANNEL_ID = 1358184251476152658

# ------------------- Bot -------------------
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)
bot.role_embed_data = {}  # opslag voor role embeds


# ------------------- Events -------------------
@bot.event
async def on_ready():
    print(f"✅ Bot ingelogd als {bot.user}")
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"🌐 Slash commands gesynchroniseerd: {len(synced)}")
    except Exception as e:
        print(f"❌ Fout bij sync: {e}")

# <<< AANGEPAST >>>
# ------------------- Changelog Modal -------------------
class ChangelogModal(Modal, title="Maak een Changelog"):
    aanpassingen = TextInput(
        label="Wat zijn de aanpassingen?",
        style=discord.TextStyle.paragraph,
        placeholder="• Server geüpdatet naar de laatste versie.\n• Nieuwe feature toegevoegd.",
        required=True,
        max_length=2000
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Maak de embed aan met een blauwe kleur
        embed = discord.Embed(
            title="Changelog",
            description=f"Onderstaande aanpassingen zijn doorgevoerd :\n\n{self.aanpassingen.value}",
            color=discord.Color.blue() # Blauwe kleur
        )
        
        # Voeg de footer toe met de username en de servernaam
        embed.set_footer(text=f"Noorderveen Roleplay - Update by: {interaction.user.name}")
        
        # Voeg een timestamp toe (huidige tijd)
        embed.timestamp = datetime.now(timezone.utc)

        # Stuur de embed naar het kanaal waar het commando is gebruikt
        await interaction.channel.send(embed=embed)
        
        # Stuur een bevestiging naar de gebruiker
        await interaction.response.send_message("✅ Changelog succesvol geplaatst!", ephemeral=True)

# <<< AANGEPAST >>>
# ------------------- Changelog Command -------------------
@bot.tree.command(name="changelog", description="Maak een changelog embed", guild=discord.Object(id=GUILD_ID))
async def changelog_cmd(interaction: discord.Interaction):
    # Check of de gebruiker de vereiste rol heeft
    user_roles = [r.id for r in interaction.user.roles]
    if EMBED_ROLE_ID not in user_roles:
        await interaction.response.send_message("❌ Je hebt geen toegang tot dit commando.", ephemeral=True)
        return
    
    # Open de modal voor de gebruiker
    await interaction.response.send_modal(ChangelogModal())


# ------------------- Embed Modal -------------------
class EmbedModal(Modal, title="Maak een Embed"):
    titel = TextInput(label="Titel", style=discord.TextStyle.short, placeholder="Bijv. Mededeling", required=True, max_length=100)
    beschrijving = TextInput(label="Beschrijving", style=discord.TextStyle.paragraph, placeholder="Tekst die in de embed verschijnt", required=True, max_length=2000)
    kleur = TextInput(label="Kleur (hex of none)", style=discord.TextStyle.short, placeholder="#2ecc71", required=False, max_length=10)

    async def on_submit(self, interaction: discord.Interaction):
        kleur_input = self.kleur.value or "#2ecc71"
        if kleur_input.lower() == "none":
            color = discord.Color.default()
        else:
            try:
                color = discord.Color(int(kleur_input.strip("#"), 16))
            except:
                color = discord.Color.default()

        embed = discord.Embed(title=self.titel.value, description=self.beschrijving.value, color=color)
        embed.set_footer(text=f"Gemaakt door {interaction.user}")

        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("Kon guild niet vinden.", ephemeral=True)
            return

        options = [SelectOption(label=ch.name, value=str(ch.id)) for ch in guild.text_channels[:25]]

        class ChannelSelect(View):
            @discord.ui.select(placeholder="Kies een kanaal", options=options)
            async def select_callback(self, select_interaction: discord.Interaction, select: Select):
                kanaal_id = int(select.values[0])
                kanaal = guild.get_channel(kanaal_id)
                if kanaal is None:
                    await select_interaction.response.edit_message(content="Kanaal niet gevonden.", view=None)
                    return
                await kanaal.send(embed=embed)
                await select_interaction.response.edit_message(content=f"✅ Embed gestuurd naar {kanaal.mention}", view=None)

        await interaction.response.send_message("Kies een kanaal voor je embed:", view=ChannelSelect(), ephemeral=True)


@bot.tree.command(name="embed", description="Maak een embed via formulier", guild=discord.Object(id=GUILD_ID))
async def embed_cmd(interaction: discord.Interaction):
    user_roles = [r.id for r in interaction.user.roles]
    if EMBED_ROLE_ID not in user_roles:
        await interaction.response.send_message("❌ Je hebt geen toegang tot dit commando.", ephemeral=True)
        return
    await interaction.response.send_modal(EmbedModal())
  
class RoleEmbedModal(Modal, title="Maak een Role Embed"):
    titel = TextInput(
        label="Titel", style=discord.TextStyle.short,
        placeholder="Bijv. Kies je rol", required=True, max_length=100
    )
    beschrijving = TextInput(
        label="Beschrijving (embed tekst)", style=discord.TextStyle.paragraph,
        placeholder="Tekst die in de role-embed verschijnt", required=True, max_length=4000
    )
    mapping = TextInput(
        label="Mapping (emoji:role_id of emoji:RoleName)", style=discord.TextStyle.short,
        placeholder="Bijv: ✅:1402417593419305060, 🎮:Gamer", required=True, max_length=200
    )
    thumbnail = TextInput(
        label="Thumbnail (URL of 'serverlogo')", style=discord.TextStyle.short,
        placeholder="https://example.com/thumb.png of 'serverlogo'", required=False, max_length=200
    )
    kleur = TextInput(
        label="Kleur (hex of none)", style=discord.TextStyle.short,
        placeholder="#2ecc71", required=False, max_length=10
    )

    async def on_submit(self, interaction: discord.Interaction):
        # --- Kleur verwerken ---
        kleur_input = self.kleur.value or "#2ecc71"
        if kleur_input.lower() == "none":
            color = discord.Color.default()
        else:
            try:
                color = discord.Color(int(kleur_input.strip("#"), 16))
            except:
                color = discord.Color.default()

        # --- Embed maken ---
        embed = discord.Embed(title=self.titel.value, description=self.beschrijving.value, color=color)
        if self.thumbnail.value:
            if self.thumbnail.value.lower() == "serverlogo" and interaction.guild.icon:
                embed.set_thumbnail(url=interaction.guild.icon.url)
            else:
                embed.set_thumbnail(url=self.thumbnail.value)
        elif interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)

        if interaction.guild.icon:
            embed.set_footer(text=f"Gemaakt door {interaction.guild.name}", icon_url=interaction.guild.icon.url)
        else:
            embed.set_footer(text=f"Gemaakt door {interaction.guild.name}")

        # --- Emoji → Role mapping ---
        raw_map = {}
        for part in self.mapping.value.split(","):
            if ":" in part:
                emoji_text, role_part = part.split(":", 1)
                emoji_text = emoji_text.strip()
                role_part = role_part.strip()
                if emoji_text and role_part:
                    raw_map[emoji_text] = role_part

        if not raw_map:
            await interaction.response.send_message(
                "Geen geldige mapping gevonden. Gebruik format emoji:role_id of emoji:RoleName",
                ephemeral=True
            )
            return

        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("Kon guild niet vinden.", ephemeral=True)
            return

        # --- Kanaal selecteren ---
        options = [SelectOption(label=ch.name, value=str(ch.id)) for ch in guild.text_channels[:25]]

        class ChannelSelect(View):
            @discord.ui.select(placeholder="Kies een kanaal", options=options)
            async def select_callback(self, select_interaction: discord.Interaction, select: Select):
                kanaal_id = int(select.values[0])
                kanaal = guild.get_channel(kanaal_id)
                if kanaal is None:
                    await select_interaction.response.edit_message(content="Kanaal niet gevonden.", view=None)
                    return

                message = await kanaal.send(embed=embed)

                # --- Normaliseer mapping naar rol-ID's ---
                normalized_map = {}
                for emoji_text, role_part in raw_map.items():
                    role_id = None
                    # Als het een ID is
                    if role_part.isdigit():
                        try:
                            role_id = int(role_part)
                            role_obj = guild.get_role(role_id)
                            if role_obj is None:
                                try:
                                    role_obj = await guild.fetch_role(role_id)
                                except:
                                    role_obj = None
                            if role_obj is None:
                                role_id = None
                        except:
                            role_id = None
                    # Als het een naam is
                    else:
                        role_obj = discord.utils.get(guild.roles, name=role_part)
                        if role_obj:
                            role_id = role_obj.id

                    # Voeg emoji toe aan bericht
                    try:
                        await message.add_reaction(emoji_text)
                        if role_id:
                            normalized_map[str(emoji_text)] = role_id
                    except Exception as e:
                        print(f"Kon emoji niet toevoegen ({emoji_text}): {e}")

                bot.role_embed_data = getattr(bot, "role_embed_data", {})
                bot.role_embed_data[message.id] = normalized_map

                await select_interaction.response.edit_message(
                    content=f"✅ Role embed gestuurd naar {kanaal.mention}\nOpgeslagen mappings: {len(normalized_map)}",
                    view=None
                )

        await interaction.response.send_message("Kies een kanaal voor je role embed:", view=ChannelSelect(), ephemeral=True)

# ---------- ROLE EMBED COMMAND ----------
@bot.tree.command(
    name="roleembed",
    description="Maak een role embed (alleen bepaalde rollen mogen dit)",
    guild=discord.Object(id=GUILD_ID)
)
async def roleembed(interaction: discord.Interaction):
    user_roles = [r.id for r in interaction.user.roles]
    if EMBED_ROLE_ID not in user_roles:
        await interaction.response.send_message("❌ Je hebt geen toegang tot dit commando.", ephemeral=True)
        return

    await interaction.response.send_modal(RoleEmbedModal())

# ---------- REACTION → ROLES ----------
async def handle_reaction(payload: discord.RawReactionActionEvent, add=True):
    emoji_map = getattr(bot, "role_embed_data", {}).get(payload.message_id)
    if not emoji_map:
        return

    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        return

    member = guild.get_member(payload.user_id)
    if member is None:
        try:
            member = await guild.fetch_member(payload.user_id)
        except:
            return

    if member.bot:
        return

    role_id = emoji_map.get(str(payload.emoji))
    if role_id:
        role = guild.get_role(role_id)
        if role:
            try:
                if add:
                    await member.add_roles(role)
                else:
                    await member.remove_roles(role)
            except Exception as e:
                print(f"Kon rol niet {'toevoegen' if add else 'verwijderen'}: {e}")

@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    await handle_reaction(payload, add=True)

@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    await handle_reaction(payload, add=False)
# ------------------- Helpers -------------------
async def try_send_dm(user: discord.abc.Messageable, content: str):
    """Probeer een DM te sturen, maar faal stilletjes zonder te crashen."""
    try:
        await user.send(content)
        return True
    except Exception:
        return False

def make_action_dm(guild_name: str, actie: str, reden: str, moderator: str):
    """Return DM text voor acties."""
    return (
        f"Je bent **{actie}** in **{guild_name}**.\n"
        f"Reden: {reden}\n"
        f"Door: {moderator}\n"
        f"Tijd: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )

# ------------------- Moderatie modal (reden) -------------------
class ModeratieModal(Modal, title="Reden"):
    reden = TextInput(label="Reden", style=discord.TextStyle.paragraph, placeholder="Geef een reden", required=True)

    def __init__(self, view_ref):
        super().__init__()
        self.view_ref = view_ref

    async def on_submit(self, interaction: discord.Interaction):
        view = self.view_ref
        action = view.actie
        guild = interaction.guild
        moderator = interaction.user

        try:
            if action in {"ban", "kick", "warn"}:
                member: discord.Member = view.target_member
                if member is None:
                    await interaction.response.send_message("❌ Geen doelwit geselecteerd.", ephemeral=True)
                    return

                me = guild.me
                # permission & hierarchy checks
                if action == "ban" and not me.guild_permissions.ban_members:
                    await interaction.response.send_message("❌ Bot mist 'Ban Members' permissie.", ephemeral=True)
                    return
                if action == "kick" and not me.guild_permissions.kick_members:
                    await interaction.response.send_message("❌ Bot mist 'Kick Members' permissie.", ephemeral=True)
                    return
                if member == me:
                    await interaction.response.send_message("❌ Kan de bot niet modereren.", ephemeral=True)
                    return
                if member.top_role >= me.top_role:
                    await interaction.response.send_message("❌ Kan deze gebruiker niet modereren: hogere of gelijke rol dan de bot.", ephemeral=True)
                    return

                # Probeer DM te sturen vóór de actie (zodat ze het bericht ontvangen)
                dm_text = make_action_dm(guild.name if guild else "de server", action.upper(), self.reden.value, moderator.mention)
                dm_ok = await try_send_dm(member, dm_text)

                # Execute action
                if action == "ban":
                    await member.ban(reason=self.reden.value)
                elif action == "kick":
                    await member.kick(reason=self.reden.value)
                elif action == "warn":
                    # Placeholder: extend with persistent warn store if desired
                    # still send DM (done above)
                    pass

                # Logging to channel
                log_id = LOG_CHANNELS.get(action)
                if log_id:
                    log_chan = guild.get_channel(log_id)
                    if log_chan:
                        emb = discord.Embed(
                            title=f"{action.capitalize()} uitgevoerd",
                            description=(
                                f"**Gebruiker:** {member} (`{member.id}`)\n"
                                f"**Reden:** {self.reden.value}\n"
                                f"**Door:** {moderator.mention}\n"
                                f"**DM verzonden:** {'Ja' if dm_ok else 'Nee'}"
                            ),
                            color=discord.Color.red(),
                            timestamp=datetime.now(timezone.utc),
                        )
                        await log_chan.send(embed=emb)

                await interaction.response.send_message(f"✅ Actie `{action}` uitgevoerd op {member}.", ephemeral=True)

            else:
                await interaction.response.send_message("❌ Ongeldige actie.", ephemeral=True)

        except discord.Forbidden:
            await interaction.response.send_message("❌ Bot heeft onvoldoende permissies om deze actie uit te voeren.", ephemeral=True)
        except Exception as exc:
            await interaction.response.send_message(f"❌ Fout bij uitvoeren: {exc}", ephemeral=True)

# ------------------- Unban modal (top-level, executes unban directly) -------------------
class UnbanModal(Modal, title="Unban gebruiker (ID)"):
    user_id = TextInput(label="User ID", style=discord.TextStyle.short, placeholder="Bijv. 123456789012345678", required=True)
    reden = TextInput(label="Reden (optioneel)", style=discord.TextStyle.paragraph, placeholder="Reden (optioneel)", required=False)

    def __init__(self):
        super().__init__()

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        moderator = interaction.user
        if guild is None:
            await interaction.response.send_message("❌ Guild niet gevonden.", ephemeral=True)
            return

        # check permission
        if not guild.me.guild_permissions.ban_members:
            await interaction.response.send_message("❌ Bot mist 'Ban Members' permissie (nodig voor unban).", ephemeral=True)
            return

        # parse ID
        try:
            uid = int(self.user_id.value.strip())
        except Exception:
            await interaction.response.send_message("❌ Ongeldige User ID.", ephemeral=True)
            return

        reason_text = self.reden.value or "Geen reden opgegeven"

        # fetch bans (compatibel met multiple discord.py builds)
        try:
            bans = await guild.bans()
        except TypeError:
            bans = [b async for b in guild.bans()]

        ban_entry = next((b for b in bans if b.user.id == uid), None)
        if ban_entry is None:
            await interaction.response.send_message("❌ Deze user ID is niet geband (of niet gevonden).", ephemeral=True)
            return

        # try unban
        try:
            await guild.unban(ban_entry.user, reason=reason_text)
        except discord.Forbidden:
            await interaction.response.send_message("❌ Bot heeft geen permissie om te unbannen.", ephemeral=True)
            return
        except Exception as e:
            await interaction.response.send_message(f"❌ Unban faalde: {e}", ephemeral=True)
            return

        # Probeer DM naar gebruiker ná unban
        dm_text = make_action_dm(guild.name, "UNBAN", reason_text, moderator.mention)
        try_send = await try_send_dm(ban_entry.user, dm_text)

        # log to unban channel
        log_id = LOG_CHANNELS.get("unban")
        if log_id:
            log_channel = guild.get_channel(log_id)
            if log_channel:
                emb = discord.Embed(
                    title="Unban uitgevoerd",
                    description=(
                        f"**Gebruiker:** {ban_entry.user} (`{ban_entry.user.id}`)\n"
                        f"**Reden:** {reason_text}\n"
                        f"**Door:** {moderator.mention}\n"
                        f"**DM verzonden:** {'Ja' if try_send else 'Nee'}"
                    ),
                    color=discord.Color.green(),
                    timestamp=datetime.now(timezone.utc),
                )
                await log_channel.send(embed=emb)

        await interaction.response.send_message(f"✅ Unbanned: {ban_entry.user} (`{ban_entry.user.id}`)", ephemeral=True)

# ------------------- Moderatie View -------------------
class ModeratieView(View):
    def __init__(self, author: discord.Member):
        super().__init__(timeout=900.0)
        self.author = author
        self.target_member: discord.Member | None = None
        self.actie: str | None = None
        self.reden: str | None = None

        # user select
        user_select = UserSelect(placeholder="Kies een gebruiker", min_values=1, max_values=1)
        user_select.callback = self._user_selected
        self.add_item(user_select)

        # buttons
        for label, style, attr in [
            ("Ban", discord.ButtonStyle.danger, "ban"),
            ("Kick", discord.ButtonStyle.primary, "kick"),
            ("Warn", discord.ButtonStyle.secondary, "warn"),
            ("Unban", discord.ButtonStyle.success, "unban"),
        ]:
            btn = Button(label=label, style=style)
            btn.callback = self.make_callback(attr)
            self.add_item(btn)

    async def _user_selected(self, interaction: discord.Interaction):
        try:
            sel_vals = interaction.data.get("values", [])
            if sel_vals:
                selected_id = int(sel_vals[0])
                selected = interaction.guild.get_member(selected_id) or await interaction.guild.fetch_member(selected_id)
            else:
                selected = None
        except Exception:
            selected = None

        if selected is None:
            await interaction.response.send_message("❌ Kon gebruiker niet vinden.", ephemeral=True)
            return

        self.target_member = selected
        await interaction.response.send_message(f"✅ Gebruiker gekozen: {self.target_member.mention}", ephemeral=True)

    def make_callback(self, actie: str):
        async def callback(interaction: discord.Interaction):
            # permission sets
            permitted = UNBAN_ROLES if actie == "unban" else ALLOWED_ROLES
            if not any(r.id in permitted for r in interaction.user.roles):
                await interaction.response.send_message("❌ Je hebt hier geen toestemming voor.", ephemeral=True)
                return

    _a_          if actie == "unban":
                # open unban modal to collect ID + reason
                await interaction.response.send_modal(UnbanModal())
                return

            # for ban/kick/warn: need a selected member
            if self.target_member is None:
                await interaction.response.send_message("❌ Kies eerst een gebruiker.", ephemeral=True)
                return

            self.actie = actie
            await interaction.response.send_modal(ModeratieModal(self))

        return callback

# ------------------- Slash command to open menu -------------------
@bot.tree.command(name="moderatie", description="Open het moderatie UI menu", guild=discord.Object(id=GUILD_ID))
async def moderatie(interaction: discord.Interaction):
    if not any(r.id in (ALLOWED_ROLES | UNBAN_ROLES) for r in interaction.user.roles):
        await interaction.response.send_message("❌ Je hebt geen toegang tot dit menu.", ephemeral=True)
        return
    await interaction.response.send_message("Moderatie menu:", view=ModeratieView(interaction.user), ephemeral=True)


# ✅ Rol-IDs die mogen
# Deze staat nu bovenaan als EMBED_ROLE_ID, maar we laten deze hier voor de andere commando's
ALLOWED_ROLES_MOD = {
    1358184251471822947,
}

def has_allowed_role(interaction: discord.Interaction) -> bool:
    """Checkt of gebruiker minstens 1 van de toegestane rollen heeft."""
    return any(r.id in ALLOWED_ROLES_MOD for r in interaction.user.roles)

# Debug commands: checkban + listbans
@bot.tree.command(name="checkban", description="Check of een user ID geband is in deze server", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user_id="Discord user ID (alleen cijfers)")
async def checkban(interaction: discord.Interaction, user_id: str):
    if not has_allowed_role(interaction):
        await interaction.response.send_message("❌ Je hebt geen permissie om dit commando te gebruiken.", ephemeral=True)
        return

    try:
        uid = int(user_id.strip())
    except:
        await interaction.response.send_message("❌ Ongeldige ID — gebruik alleen cijfers.", ephemeral=True)
        return

    try:
        bans = await interaction.guild.bans()
    except TypeError:
        bans = [b async for b in interaction.guild.bans()]

    ban_entry = next((b for b in bans if b.user.id == uid), None)
    if ban_entry:
        reason = ban_entry.reason or "Geen reden opgegeven"
        emb = discord.Embed(
            title="User is geband",
            description=f"**Gebruiker:** {ban_entry.user} (`{ban_entry.user.id}`)\n**Reden:** {reason}",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=emb, ephemeral=True)
    else:
        await interaction.response.send_message("❌ Deze user ID is niet geband in deze server.", ephemeral=True)


@bot.tree.command(name="listbans", description="Laat de laatste N bans zien (debug)", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(limit="Hoeveel bans tonen (max 25)")
async def listbans(interaction: discord.Interaction, limit: int = 10):
    if not has_allowed_role(interaction):
        await interaction.response.send_message("❌ Je hebt geen permissie om dit commando te gebruiken.", ephemeral=True)
        return

    if limit < 1 or limit > 25:
        await interaction.response.send_message("❌ Limit tussen 1 en 25.", ephemeral=True)
        return

    try:
        bans = await interaction.guild.bans()
    except TypeError:
        bans = [b async for b in interaction.guild.bans()]

    if not bans:
        await interaction.response.send_message("🔎 Geen bans gevonden in deze server.", ephemeral=True)
        return

    lines = []
    for i, b in enumerate(bans[:limit], start=1):
        reason = b.reason or "Geen reden"
        lines.append(f"{i}. {b.user} — `{b.user.id}` — {reason}")

    emb = discord.Embed(
        title=f"Laatst {min(limit,len(bans))} bans",
        description="\n".join(lines),
        color=discord.Color.orange()
    )
    await interaction.response.send_message(embed=emb, ephemeral=True)

# --- CLEAR COMMAND ---
@bot.tree.command(name="clear", description="Verwijder berichten uit een kanaal", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(amount="Aantal berichten om te verwijderen (of 'all')")
async def clear(interaction: discord.Interaction, amount: str):
    ALLOWED_ROLES_CLEAR = {
        1358184251471822947, 
    }

    # Check of de gebruiker een van de rollen heeft
    if not any(r.id in ALLOWED_ROLES_CLEAR for r in interaction.user.roles):
        await interaction.response.send_message("❌ Je hebt geen toestemming om dit commando te gebruiken.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    channel = interaction.channel
    deleted = 0

    try:
        if amount.lower() == "all":
            # Verwijder ALLES in dit kanaal
            await channel.purge(limit=None)
            await interaction.followup.send("🧹 Alle berichten in dit kanaal zijn verwijderd!", ephemeral=True)
            return
        else:
            num = int(amount)
            if num < 1 or num > 1000:
                await interaction.followup.send("❌ Je kan alleen tussen 1 en 1000 berichten verwijderen.", ephemeral=True)
                return

            deleted_msgs = await channel.purge(limit=num)
            deleted = len(deleted_msgs)
            await interaction.followup.send(f"🧹 {deleted} berichten verwijderd.", ephemeral=True)

    except ValueError:
        await interaction.followup.send("❌ Ongeldig aantal, gebruik een getal of 'all'.", ephemeral=True)


@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel is None:
        return

    embed = discord.Embed(
        title=f"🎉 Welkom bij Noorderveen Roleplay, {member.name}! 🎉",
        description=(
            "De leukste roleplay-server van Nederland! 🌟\n\n"
            "📌 Lees eerst de regels /APV door zodat alles soepel verloopt.\n\n"
            "💬 We hopen dat je veel plezier hebt en nieuwe vrienden maakt! ✨"
        ),
        color=0x00AE86
    )
    embed.set_thumbnail(url=member.display_avatar.url)

    await channel.send(content=f"Welkom {member.mention}! 🎊", embed=embed)
  
# ------------------- Start Bot -------------------
keep_alive()
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    print("❌ Geen Discord TOKEN gevonden in environment variables!")
else:
    bot.run(TOKEN)
