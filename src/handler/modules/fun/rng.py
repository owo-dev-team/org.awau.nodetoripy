#!/usr/bin/env python3

"""Commands that invoke random things. Coin flips, dice rolls, kemonomimi... wait."""

import json
import random
import re

from k3 import commands

REGEX_DND = "[0-9]+[dD][0-9]+"
REGEX_DND_SPLIT = "[dD]"
REGEX_OBJECT_DND = re.compile(REGEX_DND)

MAX_ROLLS = 20
MAX_ROLL_SIZE = 30
MAX_DIE_SIZE = 2000

URL_RANDOM_WORD_API = "http://setgetgo.com/randomword/get.php"
URL_RANDOM_DOG_API = "https://random.dog/woof.json"
URL_RANDOM_CAT_API = "https://random.cat/meow"
URL_RANDOM_BIRB = "https://random.birb.pw/img/{0}"
URL_RANDOM_BIRB_API = "https://random.birb.pw/tweet.json/"
URL_RANDOM_NEKO_API = "https://nekos.life/api/neko"
URL_FOX_SUBREDDIT_TOP_API = "https://www.reddit.com/r/foxes/top/.json"
URL_FOX_SUBREDDIT_NEW_API = "https://www.reddit.com/r/foxes/new/.json"

systemrandom = random.SystemRandom()


@commands.cooldown(6, 12)
@commands.command(aliases=["doge"])
async def dog(ctx):
    """Fetch a random dog."""
    async with ctx.bot.session.get(URL_RANDOM_DOG_API) as response:
        if response.status == 200:
            data = await response.text()
            doggo = json.loads(data)
            url = doggo["url"]
            await ctx.send(url)
        else:
            await ctx.send("Could not reach random.dog. :<")


@commands.cooldown(6, 12)
@commands.command(aliases=["feline"])
async def cat(ctx):
    """Fetch a random cat."""
    async with ctx.bot.session.get(URL_RANDOM_CAT_API) as response:
        if response.status == 200:
            data = await response.text()
            catto = json.loads(data)
            url = catto["file"]
            await ctx.send(url)
        else:
            await ctx.send("Could not reach random.cat. :<")


@commands.cooldown(6, 12)
@commands.command(aliases=["kemonomimi", "catgirl", "neko", "nekomimi",
                           "foxgirl" "kitsune", "kitsunemimi"])
async def kemono(ctx):
    """Fetch a random animal-eared person."""
    async with ctx.bot.session.get(URL_RANDOM_NEKO_API) as response:
        if response.status == 200:
            neko = await response.json()
            url = neko["neko"]
            await ctx.send(url)
        else:
            await ctx.send("Could not reach nekos.life. :<")


@commands.cooldown(6, 12)
@commands.command()
async def birb(ctx):
    """Fetch a random birb."""
    async with ctx.bot.session.get(URL_RANDOM_BIRB_API) as response:
        if response.status == 200:
            data = await response.text()
            borb = json.loads(data)
            url = URL_RANDOM_BIRB.format(borb["file"])
            await ctx.send(url)
        else:
            await ctx.send("Could not reach random.birb.pw. :<")


@commands.cooldown(6, 12)
@commands.command(aliases=["kitsune"])
async def fox(ctx):
    """Fetch a random cat."""
    base_url = systemrandom.choice((URL_FOX_SUBREDDIT_TOP_API, URL_FOX_SUBREDDIT_NEW_API))
    async with ctx.bot.session.get(base_url) as response:
        if response.status == 200:
            data = await response.json()
            data = data["data"]["children"]
            foxxo = systemrandom.choice(data)
            url = foxxo["data"]["url"]
            message = f"{url}\nPowered by Reddit"
            await ctx.send(message)
        else:
            await ctx.send("Could not reach Reddit. :<")


@commands.cooldown(6, 12)
@commands.command(aliases=["cflip", "coinflip"])
async def coin(ctx):
    """Flip a coin."""
    choice = systemrandom.choice(["Heads!", "Tails!"])
    await ctx.send(choice)


@commands.cooldown(6, 12)
@commands.command(aliases=["rword", "randword"])
async def rwg(ctx):
    """Randomly generate a word."""
    async with ctx.bot.session.get(URL_RANDOM_WORD_API) as response:
        if response.status == 200:
            word = await response.text()
            await ctx.send(word)
        else:
            await ctx.send("Could not reach API. x.x")


def generate_roll(die_count, die_size):
    """Generate a roll given a number of dice and the number of sides per die. Returns a `list`.
    
    * `die_count` - The number of dice to be rolled.
    * `die_size` - The number of sides per die.
    """
    roll_ = []
    for times in range(0, die_count):
        roll_.append(systemrandom.randint(1, die_size))
    return roll_


def parse_roll(expression):
    """Take a string and interpret it as a D&D style roll expression.
    
    Return a `tuple` where index 0 is an `int` representing the number of dice,
    and index 1 is an `int` representing the number of sides per die.
    """
    expression_parts = re.split(REGEX_DND_SPLIT, expression)
    roll_ = tuple(int(value) for value in expression_parts)
    return roll_


def trim_expressions(*expressions):
    """Take a list of D&D expressions and eliminate any that are not valid."""
    expressions = [e for e in expressions if REGEX_OBJECT_DND.fullmatch(e)]
    return expressions


def parse_rolls(*expressions, **kwargs):
    """Parse a list of D&D dice roll expressions, roll them, and return a list of
       human-readable trings.

    * `expressions` - A `list` of `str` representing D&D dice roll expressions.
    * `max_rolls` - An `int` representing the number of expressions to be rolled.
    * `max_roll_size` - An `int` representing the maximum number of dice allowed in a given roll.
    * `max_die_size` - An `int` representing the maximum number of sides allowed on a die.
    """

    max_rolls = kwargs["max_rolls"]
    max_roll_size = kwargs["max_roll_size"]
    max_die_size = kwargs["max_die_size"]

    rolls = []

    expressions = trim_expressions(*expressions)

    for expression in expressions[:max_rolls]:

        roll_ = parse_roll(expression)

        if roll_[0] > max_roll_size or roll_[1] > max_die_size:
            continue

        elif roll_[1] > 1 and roll_[0] >= 1:

            outcome = generate_roll(roll_[0], roll_[1])

            rolls.append(f"{expression}: {outcome} ({sum(outcome)})")

    return rolls


@commands.cooldown(6, 12)
@commands.command()
async def roll(ctx, *expressions):
    """Roll some dice, using D&D syntax.

    Examples:
    roll 5d6 - Roll five six sided dice.
    roll 1d20 2d8 - Roll one twenty sided die, and two eight sided dice.
    """

    rolls = parse_rolls(*expressions,
                        max_rolls=MAX_ROLLS,
                        max_roll_size=MAX_ROLL_SIZE,
                        max_die_size=MAX_DIE_SIZE)

    if rolls:
        await ctx.send(ctx.f.codeblock("\n".join(rolls)))

    else:
        await ctx.send(("No valid rolls supplied. "
                        f"Please use D&D format, e.g. 5d6.\n"
                        "Individual rolls cannot have more than "
                        f"{MAX_ROLL_SIZE} dice, and dice cannot have "
                        f"more than {MAX_DIE_SIZE} sides."))