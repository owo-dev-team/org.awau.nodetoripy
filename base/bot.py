"""
Copyright (C) 2017 ClaraIO

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Written by ClaraIO <chinodesuuu@gmail.com>, August 2017
"""

import importlib
import inspect
import traceback

from discord import Client

from .holders import CommandHolder
from .exceptions import FrameworkException
from .commands import command
from .ctx import Context


__all__ = ["Bot"]


class Bot(Client):
    """ Bot class
    ext.commands-like command parser.
    """
    def __init__(self, prefix=None, *args, **kwargs):
        self.prefix = prefix or "!"
        self._commands = CommandHolder()
        self.command_list = self._commands.commands
        self._cogs = {}
        super().__init__(*args, **kwargs)

    def command(self, **kwargs):
        """ Register a command directly """
        return command(bot=self, **kwargs)

    def load_cog(self, cog_name):
        """ Load a cog from a dotted file path """
        lib = importlib.import_module(cog_name)
        if not hasattr(lib, "setup"):
            del lib
            raise FrameworkException("File has no `setup` function")

        lib.setup(self)
        del lib

    def add_cog(self, cog):
        cog_name = cog.__class__.__name__

        if cog_name in self._cogs:
            raise FrameworkException("Cog already registered!")

        self._cogs[cog_name] = cog

    def unload_cog(self, cog_name):
        """ Unload a code from the cog classname """
        if cog_name in self._cogs:
            self._cogs[cog_name]._unload()
            del self._cogs[cog_name]

    def add_command(self, _command):
        """ Add a command dynamically """
        if _command.name in self._commands.commands:
            raise FrameworkException("Command already registered!")

        self._commands.add_command(_command)

    def remove_command(self, command_name):
        """ Remove a command dynamically """
        if command_name in self._commands.commands:
            self._commands.remove_command(command_name)

    async def on_message(self, message):
        """ Redirects on_message to process_commands
        If you decide to override this,
        make sure to call process_commands """
        await self.process_commands(message)

    async def process_commands(self, message):
        """ Does command parsing """
        if inspect.isfunction(self.prefix):
            prefix = self.prefix(self, message)

        else:
            prefix = self.prefix

        if inspect.isawaitable(prefix):
            prefix = await prefix

        if isinstance(prefix, str):
            prefix = [prefix]

        if not any(message.content.startswith(p) for p in prefix):
            return False

        for p in prefix:
            # Check for any prefix
            if message.content.startswith(p):
                content = message.content[len(p):]
                break

        else:
            return False

        # TODO: Custom parsing for quoted content
        args = [_ for _ in content.split(" ")]

        _command = self._commands.get_command(args[0])

        if _command is False:
            # Command not found
            return False

        # Build the context
        context = Context(
            message=message,
            author=message.author,
            guild=message.guild,
            channel=message.channel,
            command=_command,
            bot=self,
            invoker=args[0],
            args=args[1:],
            send=message.channel.send
        )

        try:
            await _command.invoke(context)

        except Exception as e:  # noqa pylint: disable=broad-except
            await self.command_error(context, e)

    async def command_error(self, ctx, e):  # pylint: disable=unused-argument
        await ctx.send("```py\n{}```".format(traceback.format_exc()))
