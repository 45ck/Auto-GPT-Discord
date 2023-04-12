import os
import discord
from discord.ext import commands
from discord import Intents
import socket
import threading
import asyncio
import json
import time
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()


# Load the environment variables from the .env file
load_dotenv()

intended_channel_id = 940734878327124039  # Replace with your target channel ID

intents = Intents.default()
intents.messages = True
intents.members = True

global s

import json

def get_categories_and_channels(guild):
    channels = guild.channels
    categories = {}
    for channel in channels:
        if channel.category:
            category = channel.category.name
            if category not in categories:
                categories[category] = []
            categories[category].append(channel.name)
        else:
            if "Uncategorized" not in categories:
                categories["Uncategorized"] = []
            categories["Uncategorized"].append(channel.name)

    result = []
    for category, channels in categories.items():
        category_dict = {}
        category_dict["Category"] = category
        category_dict["Channels"] = channels
        result.append(category_dict)

    return json.dumps(result)

import json

def get_all_roles(guild, user):
    roles = []
    for role in guild.roles[1:]:
        if role < user.top_role and not role.managed:
            roles.append(role)

    role_list = []
    for role in roles:
        role_dict = {}
        role_dict["Name"] = role.name
        role_dict["Color"] = str(role.color)
        role_dict["Permissions"] = int(role.permissions.value)
        role_dict["Hoist"] = role.hoist
        role_dict["Mentionable"] = role.mentionable
        role_list.append(role_dict)

    return json.dumps(role_list)


async def echo_message_in_channel(message: str):
    channel = bot.get_channel(intended_channel_id)
    if channel:
        await channel.send(message)

def start_socket_server():
    async def process_message(message: str):
        await bot.wait_until_ready()

        try:
            # Attempt to parse the message as JSON
            data = json.loads(message)
        except json.JSONDecodeError:
            # If the message cannot be parsed as JSON, assume it is a simple text message
            await echo_message_in_channel(message)
            return

        # Extract the command and parameters from the message
        command = data[0]
        params = data[1:]

        if command == "message":
            # Send a simple text message
            text = " ".join(params)
            await echo_message_in_channel(text)
        elif command == "command":
            # Execute a bot command
            cmd = " ".join(params)
            message = discord.Message(content=cmd)
            await bot.process_commands(message)
        elif command == "list_channels":
            try:
                categories_and_channels = get_categories_and_channels(bot.guilds[0])
                response = f"Channels and categories in server:\n{categories_and_channels}"
                conn.sendall(response.encode())
                print("Send Response: " + response)
            except (socket.error, asyncio.TimeoutError) as e:
                import traceback
                tb = traceback.format_exc()
                print(f"Error sending action: {str(e)}\n{tb}")
                conn.sendall(f"Error sending action: {str(e)}\n{tb}")
        elif command == "get_message_history":
            # Get the message history for a specific channel
            try:
                # Parse the channel ID and number of messages to retrieve from the arguments
                channel_name = params[0]
                channel = discord.utils.get(bot.guilds[0].channels, name=channel_name)

                # Get the message history for the channel
                messages = [] 
                async for message in channel.history(limit=min(int(params[1]), 10)):
                    messages.append(message)

                if (len(messages) == 0):
                    messages.append("There are no messages in this channel.")
                else:
                    messages.append("There where a total of " + len(messages) + " messages in #" + channel_name)

                # Create a response message with the message history
                message_history = "\n".join([f"{message.author.name}: {message.content}" for message in messages])
                response = f"Message history for channel {channel.name}:\n{message_history}"

                # Send the response back to the client
                conn.sendall(response.encode())
                print("Send Response: " + response)

            except (socket.error, asyncio.TimeoutError) as e:
                import traceback
                tb = traceback.format_exc()
                print(f"Error sending action: {str(e)}\n{tb}")
                conn.sendall((f"Error sending action: {str(e)}\n{tb}").encode())

        elif command.startswith("message_channel"):
            # Send a message to a specific channel
            channel_name = params[0]
            channel = discord.utils.get(bot.guilds[0].channels, name=channel_name)
            if channel:
                await channel.send(params[1])
                conn.sendall(f"Successfully sent message in '{channel_name}'")
            else:
                await conn.sendall(f"Channel '{channel_name}' not found.")
        elif command == "create_channel":
            # Create a new text channel
            channel_name = params[0]
            category_name = params[1] if len(params) > 1 else bot.guilds[0].name

            # Check if the category already exists
            category = discord.utils.get(bot.guilds[0].categories, name=category_name)

            # Create a new category if it doesn't exist
            if not category:
                category = await bot.guilds[0].create_category(category_name)

            await bot.guilds[0].create_text_channel(channel_name, category=category)

            response = f"Channel '{channel_name}' created."

            response += f"Now the server Channels are:\n{get_categories_and_channels(bot.guilds[0])}"
            conn.sendall(response.encode())
            print("Send Response: " + response)


        elif command == "rename_channel":
            # Rename an existing channel
            channel_name = params[0]
            new_name = params[1]
            channel = discord.utils.get(bot.guilds[0].channels, name=channel_name)
            if channel:
                await channel.edit(name=new_name)
                await conn.sendall((f"Channel '{channel_name}' renamed to '{new_name}'.").encode())
            else:
                await conn.sendall((f"Channel '{channel_name}' not found.").encode())
        elif command == "delete_channel":
            # Delete an existing channel
            channel_name = params[0]
            channel = discord.utils.get(bot.guilds[0].channels, name=channel_name)
            if channel:
                await channel.delete()
                await conn.sendall((f"Channel '{channel_name}' deleted.").encode())
            else:
                await conn.sendall((f"Channel '{channel_name}' not found.").encode())
        elif command == "create_role":
            # Create a new role with the given name
            roles = []
            for role_params in params[0]:
                role_name = role_params.get("role_name")
                color = role_params.get("color", "default")
                permissions_str = role_params.get("permissions", "").lower()
                hoist = role_params.get("hoist", False)
                mentionable = role_params.get("mentionable", False)

                # Convert color and permissions strings to their respective values
                color_value = discord.Color.default() if color == "default" else discord.Color(int(color[1:], 16))
                permissions_value = discord.Permissions()
                for permission in permissions_str.split(','):
                    permission = permission.strip()
                    setattr(permissions_value, permission, True)

                guild = bot.guilds[0]
                role = await guild.create_role(name=role_name, color=color_value, permissions=permissions_value, hoist=hoist, mentionable=mentionable)
                roles.append(role)

            # Get a list of all roles in the server
            guild = bot.guilds[0]
            response = get_all_roles(guild)

            conn.sendall(response.encode())

            
        elif command == "list_all_roles":
            try:
                # Get a list of all roles in the server
                guild = bot.guilds[0]
                roles = guild.roles[1:]  # exclude @everyone role
                role_names = []

                for role in roles:
                    if role.managed or role.is_default():
                        # Skip roles owned by bots or that can't be modified
                        continue
                    role_names.append(role.name)

                response = f"Roles in server: {', '.join(role_names)}"

                conn.sendall(response.encode())
                print("Send Response: " + response)

            except (socket.error, asyncio.TimeoutError) as e:
                import traceback
                tb = traceback.format_exc()
                print(f"Error sending action: {str(e)}\n{tb}")
                conn.sendall((f"Error sending action: {str(e)}\n{tb}").encode())

        elif command == "update_role":
            # Update the name of a role with the given ID
            role_name = params[0]
            new_name = params[1]
            guild = bot.guilds[0]
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                await role.edit(name=new_name)
                print(f"Role '{role_name}' updated to '{new_name}'.")
                await conn.sendall((f"Role '{role_name}' updated to '{new_name}'.").encode())
            else:
                print(f"Role '{role_name}' not found.")
                await conn.sendall((f"Role '{role_name}' not found.").encode())

        elif command == "delete_role":
            # Delete a role with the given ID
            roles = []
            
            for role_params in params[0]:
                role_name = role_params.get("role_name")
                guild = bot.guilds[0]
                role = discord.utils.get(guild.roles, name=role_name)
                if role:
                    await role.delete()
                    print(f"Role '{role_name}' deleted.")
                    roles.append(role)
                else:
                    print(f"Role '{role_name}' not found.")
                    
            if roles:
                await conn.sendall((f"Roles '{', '.join(role.name for role in roles)}' deleted.").encode())
            else:
                await conn.sendall((f"roles '{', '.join(role.name for role in roles)}' where not found to delete.").encode())


        elif command == "change_role_permission":
            # Grant a permission to a role
            role_names = params[0]  # list of role names
            permission_names = params[1:]  # list of permission names
            
            guild = bot.guilds[0]
            result_message = ""
            for role_name in role_names:
                role = discord.utils.get(guild.roles, name=role_name)
                if role:
                    for permission_name in permission_names:
                        try:
                            permission = getattr(discord.Permissions, permission_name)
                            perms = role.permissions
                            perms.update(**{permission_name: True})
                            await role.edit(permissions=perms)
                            print(f"Permission '{permission_name}' granted to role '{role_name}'.")
                            result_message += (f"Permission '{permission_name}' granted to role '{role_name}'.\n")
                        except AttributeError:
                            print(f"Invalid permission name: '{permission_name}'")
                            result_message += (f"Invalid permission name: '{permission_name}'.\n")
                else:
                    print(f"Role '{role_name}' not found.")
                    result_message += (f"Role '{role_name}' not found.\n")
            await conn.sendall(result_message.encode())

        elif command == "revoke_role_permission":
            # Revoke a permission from a role
            role_names = params[0]  # list of role names
            permission_names = params[1:]  # list of permission names
            guild = bot.guilds[0]
            result_message = ""
            for role_name in role_names:
                role = discord.utils.get(guild.roles, name=role_name)
                if role:
                    for permission_name in permission_names:
                        try:
                            permission = getattr(discord.Permissions, permission_name)
                            perms = role.permissions
                            perms.update(**{permission_name: False})
                            await role.edit(permissions=perms)
                            print(f"Permission '{permission_name}' revoked from role '{role_name}'.")
                            result_message += (f"Permission '{permission_name}' revoked from role '{role_name}'.\n")
                        except AttributeError:
                            print(f"Invalid permission name: '{permission_name}'")
                            result_message += (f"Invalid permission name: '{permission_name}'.\n")
                else:
                    print(f"Role '{role_name}' not found.")
                    result_message += (f"Role '{role_name}' not found.\n")
            await conn.sendall(result_message.encode())
        elif command == "create_new_discord_invite":
            invite_channel = params[0]

            # Create a new invite for the given channel
            channel = discord.utils.get(bot.guilds[0].channels, name=invite_channel)
            invite = await channel.create_invite()

            # Send the invite URL back to the client
            invite_code_url = invite.url
            result_message = invite_code_url
            await conn.sendall(result_message.encode())

        elif command == "private_msg_users":
            users = params[0] #array of user ids
            message = params[1] 

            # Send a private message to the specified users
            for user_id in users:
                user = await bot.fetch_user(int(user_id))
                await user.send(message)

            # Send a response indicating that the messages were sent successfully
            result_message = "Private messages sent successfully"
            await conn.sendall(result_message.encode())

        elif command == "send_image_channel":
            channel = params[0]
            images = params[1] # array of urls to images

            # Send the images to the specified channel
            target_channel = discord.utils.get(bot.guilds[0].channels, name=channel)
            for image_url in images:
                await target_channel.send(file=discord.File(image_url))

            # Send a response indicating that the images were sent successfully
            result_message = "Images sent successfully"
            await conn.sendall(result_message.encode())

        elif command == "get_user_list":
            # Get a list of all users in the Discord server (IDs and usernames)
            guild = bot.guilds[0]
            members = guild.members
            user_list = "\n".join([f"{member.id}: {member.name}" for member in members])

            # Send the user list back to the client
            await conn.sendall(user_list.encode())

        elif command == "set_channel_access":
            channel = params[0]
            roles = params[1] #list of roles who have access to the channel

            # Set the channel to only be accessible by the specified roles
            target_channel = discord.utils.get(bot.guilds[0].channels, name=channel)
            overwrites = target_channel.overwrites
            for role_name in roles:
                role = discord.utils.get(target_channel.guild.roles, name=role_name)
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            await target_channel.edit(overwrites=overwrites)

            # Send a response indicating that the channel access was updated successfully
            result_message = f"Access to channel '{channel}' updated successfully"
            await conn.sendall(result_message.encode())



    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', 12345))
        s.listen(1)
        conn, addr = s.accept()
        with conn:
            print('Connected by', addr)
            while True:
                data = conn.recv(4096)
                if not data:
                    break
                message = data.decode()
                print("Received:", message)
                asyncio.run_coroutine_threadsafe(process_message(message), bot.loop)

socket_server_thread = threading.Thread(target=start_socket_server)
socket_server_thread.start()

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print("Bot is ready.")

@bot.command()
async def hello(ctx):
    await ctx.send("Hello!")

bot.run(os.getenv("DISCORD_TOKEN"))
