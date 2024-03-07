# gamercon-async
 `gamercon-async` is an asynchronous Python rcon client tailored for managing and interacting with game servers such as Minecraft, Ark, and Palworld. This tool provides developers and server administrators with a powerful, non-blocking way to execute commands and handle server communications effectively.

## Version
> v1.0.6

## Protocols
 - GameRCON: This feature offers an asynchronous RCON protocol designed to connect to multiple servers simultaneously, enhancing the ability to manage and interact with game servers efficiently.
 - EvrimaRCON: Specifically tailored for The Isle: Evrima, EvrimaRCON is an asynchronous RCON protocol that provides specialized support for the unique needs of this game, facilitating better server management and player interaction.
 - GameRCONBase64: An advanced version of the GameRCON feature, GameRCONBase64 employs an asynchronous Base64-encoded RCON protocol. This allows for secure and efficient connections to any number of servers, ensuring a robust method for server management and communication.

## Supported Games
 - Ark: Survival Ascended
 - The Isle: Evrima
 - Source Engine Games
 - Palworld
 - Path of Titans

Mostly any game that supports source rcon will work with this protocol.

## Installation

 Install `gamercon-async` using pip:

 ```bash
 pip install gamercon-async
 ```

## Requirements
 - Python 3.10+
 - asyncio

## Usage
 Quick example on how to use source games.

 ```python
import asyncio
from gamercon_async import GameRCON

async def main():
    client = GameRCON('host', 'port', 'password', timeout=10)
    async with client as pot_client:
        response = await pot_client.send('your_command')
        print(response)

asyncio.run(main())
```
Replace `host`, `port`, and `password` with your actual credentials and 'your_command' with the command you want to send.

Example with The Isle: Evrima
```python
import asyncio
from gamercon_async import EvrimaRCON

async def main():
   rcon = EvrimaRCON('host', port, 'password')
   await rcon.connect()
   
   save_response = await rcon.send_command(bytes('\x02', 'utf-8') + bytes('\x50', 'utf-8') + bytes('\x00', 'utf-8'))
   print(f"Save Server Response: {save_response}")
   
   announcement = "Hello, world!"
   announce_response = await rcon.send_command(bytes('\x02', 'utf-8') + bytes('\x10', 'utf-8') + announcement.encode() + bytes('\x00', 'utf-8'))
   print(f"Announcement Response: {announce_response}")

asyncio.run(main())
```