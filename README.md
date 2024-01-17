# gamercon-async
 `gamercon-async` is an asynchronous Python client designed for games like Minecraft, Ark and Path of Titans.

## Features
 - List the key features of your package.
 - Explain what makes your package stand out.

## Installation

 Install `gamercon-async` using pip:

 ```bash
 pip install gamercon-async
 ```

## Requirements
 - Python 3.10+
 - asyncio
 - struct

## Usage
 Quick example on how to use `GameRCON-async`.

 ```python
import asyncio
from gamercon_async import GameRCON

async def main():
    client = GameRCON('host', 'port', 'password')
    async with client as pot_client:
        response = await pot_client.send('your_command')
        print(response)

asyncio.run(main())
```
Replace `host`, `port`, and `password` with your actual credentials and 'your_command' with the command you want to send.