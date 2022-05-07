from asyncio import sleep

from discord import Embed
from discord.ext.commands import Cog, Bot
from discord_slash import SlashContext, cog_ext, SlashCommandOptionType
from discord_slash.utils.manage_commands import create_option

from const import get_const
from database import Database, DialectDatabase, PosDatabase
from database.felinkia import FelinkiaWord
from database.hemelvaarht import ThravelemehWord
from database.sesame import SesameWord
from database.zasok import ZasokeseWord, BerquamWord
from util import get_programwide
from util.simetasis import zasokese_to_simetasise

databases = {
    'zasokese': Database(ZasokeseWord, 'zasokese_database'),
    'thravelemeh': Database(ThravelemehWord, 'thravelemeh_database'),
    'berquam': Database(BerquamWord, 'zasokese_database', 1),
    'simetasispika': DialectDatabase(ZasokeseWord, 'zasokese_database', zasokese_to_simetasise),
    'felinkia': Database(FelinkiaWord, 'felinkia_database'),
    '4351': Database(SesameWord, '4351_database', 1),
    'semal': PosDatabase('semal_database'),
    'xei': PosDatabase('xei_database', 0, 0, 2, 3),
}

guild_ids = get_programwide('guild_ids')


async def handle_dictionary(ctx: SlashContext, database: Database, embed: Embed, query: str):
    message = await ctx.send(f'`{query}`에 대해 검색 중입니다…')

    words, duplicates, reloaded = database.search_rows(query)
    too_many = False
    if (word_count := len(words)) > 25:
        too_many = True
        words = list(map(lambda x: words[x], duplicates))
        duplicates = set()

    index_offset = 0
    while duplicates and words:
        word = words.pop(duplicates.pop() - index_offset)
        word.add_to_field(embed, True)
        index_offset += 1
    for word in words:
        word.add_to_field(embed)
    if not words and not index_offset:
        embed.add_field(name='검색 결과', value='검색 결과가 없습니다.')
    if too_many:
        embed.add_field(name='기타', value=f'단어나 뜻에 `{query}`가 들어가는 단어가 {word_count - tmp} 개 더 있습니다.')

    await message.edit(content='데이터베이스를 다시 불러왔습니다.' if reloaded else '', embed=embed)


class DictionaryCog(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @cog_ext.cog_slash(
        description='자소크어 단어를 검색합니다.',
        guild_ids=guild_ids,
        options=[
            create_option(
                name='query',
                description='검색할 단어',
                required=True,
                option_type=3
            )
        ]
    )
    async def zasok(self, ctx: SlashContext, query: str):
        await handle_dictionary(ctx, databases['zasokese'], Embed(
            title=f'`{query}`의 검색 결과',
            description='자소크어 단어를 검색합니다.',
            color=get_const('shtelo_sch_vanilla')
        ), query)

    @cog_ext.cog_slash(
        description='트라벨레메 단어를 검색합니다.',
        guild_ids=guild_ids,
        options=[
            create_option(
                name='query',
                description='검색할 단어',
                required=True,
                option_type=3
            )
        ]
    )
    async def th(self, ctx: SlashContext, query: str):
        await handle_dictionary(ctx, databases['thravelemeh'], Embed(
            title=f'`{query}`의 검색 결과',
            description='트라벨레메 단어를 검색합니다.',
            color=get_const('hemelvaarht_hx_nerhgh')
        ), query)

    @cog_ext.cog_slash(
        description='베르쿠암 단어를 검색합니다.',
        guild_ids=guild_ids,
        options=[
            create_option(
                name='query',
                description='검색할 단어',
                required=True,
                option_type=3
            )
        ]
    )
    async def berquam(self, ctx: SlashContext, query: str):
        await handle_dictionary(ctx, databases['berquam'], Embed(
            title=f'`{query}`의 검색 결과',
            description='베르쿠암 단어를 검색합니다.',
            color=get_const('berquam_color')
        ), query)

    @cog_ext.cog_slash(
        description='시메타시스 단어를 검색합니다.',
        guild_ids=guild_ids,
        options=[
            create_option(
                name='query',
                description='검색할 단어',
                required=True,
                option_type=3
            )
        ]
    )
    async def sts(self, ctx: SlashContext, query: str):
        await handle_dictionary(ctx, databases['simetasispika'], Embed(
            title=f'`{query}`의 검색 결과',
            description='시메타시스어 단어를 검색합니다.',
            color=get_const('simetasis_color')
        ), query)

    @cog_ext.cog_slash(
        description='펠라인카이아어 단어를 검색합니다.',
        guild_ids=guild_ids,
        options=[
            create_option(
                name='query',
                description='검색할 단어',
                required=True,
                option_type=3
            )
        ]
    )
    async def felinkia(self, ctx: SlashContext, query: str):
        await handle_dictionary(ctx, databases['felinkia'], Embed(
            title=f'`{query}`의 검색 결과',
            description='펠라인카이아어 단어를 검색합니다.',
            color=get_const('felinkia_color')
        ), query)

    @cog_ext.cog_slash(
        name='4351',
        description='4351 단어를 검색합니다.',
        guild_ids=guild_ids,
        options=[
            create_option(
                name='query',
                description='검색할 단어',
                required=True,
                option_type=3
            )
        ]
    )
    async def sesame(self, ctx: SlashContext, query: str):
        await handle_dictionary(ctx, databases['4351'], Embed(
            title=f'`{query}`의 검색 결과',
            description='4351의 단어를 검색합니다.',
            color=get_const('4351_color')
        ), query)

    @cog_ext.cog_slash(
        name='semal',
        description='새말 단어를 검색합니다.',
        guild_ids=guild_ids,
        options=[
            create_option(
                name='query',
                description='검색할 단어',
                required=True,
                option_type=3
            )
        ]
    )
    async def semal(self, ctx: SlashContext, query: str):
        await handle_dictionary(ctx, databases['semal'], Embed(
            title=f'`{query}`의 검색 결과',
            description='새말 단어를 검색합니다.',
            color=get_const('semal_color')
        ), query)

    @cog_ext.cog_slash(
        name='xei',
        description='헤이어 단어를 검색합니다.',
        guild_ids=guild_ids,
        options=[
            create_option(
                name='query',
                description='검색할 단어',
                required=True,
                option_type=SlashCommandOptionType.STRING
            )
        ]
    )
    async def xei(self, ctx: SlashContext, query: str):
        await handle_dictionary(ctx, databases['xei'], Embed(
            title=f'`{query}`의 검색 결과',
            description='헤이어 단어를 검색합니다.',
            color=get_const('xei_color')
        ), query)

    @cog_ext.cog_slash(
        description='데이터베이스를 다시 불러옵니다.',
        guild_ids=guild_ids,
        options=[
            create_option(
                name='language',
                description='데이터베이스를 불러올 언어를 설정합니다. 아무것도 입력하지 않으면 모든 언어의 데이터베이스를 다시 불러옵니다.',
                required=False,
                option_type=3,
                choices=list(databases.keys())
            )
        ]
    )
    async def reload(self, ctx: SlashContext, language: str = ''):
        message = await ctx.send('데이터베이스를 다시 불러옵니다…')
        if language:
            if language in databases:
                databases[language].reload()
            else:
                await message.edit(content='데이터베이스 이름을 확인해주세요!!')
        else:
            for database in databases.values():
                database.reload()
                await sleep(0)
        await message.edit(content=f'{f"`{language}` " if language else ""} 데이터베이스를 다시 불러왔습니다.')


def setup(bot: Bot):
    bot.add_cog(DictionaryCog(bot))
