from asyncio import sleep, TimeoutError as AsyncTimeoutError

from discord import Embed
from discord.ext.commands import Cog, Bot
from discord_slash import SlashContext, cog_ext, SlashCommandOptionType
from discord_slash.utils.manage_commands import create_option

from const import get_const
from database import Database, DialectDatabase, PosDatabase, SimpleDatabase
from database.arteut import ArteutWord
from database.enjie import EnjieDatabase
from database.hemelvaarht import ThravelemehWord
from database.iremna import IremnaWord
from database.lazhon import LazhonWord
from database.mikhoros import MikhorosWord
from database.ropona import RoponaDatabase
from database.scheskatte import ScheskatteWord
from database.sesame import SesameWord
from database.slengeus import SlengeusWord
from database.zasok import ZasokeseWord, BerquamWord
from database.fsovm import FsovmWord
from database.pasel import PaselWord
from util import get_programwide
from util.simetasis import zasokese_to_simetasise

databases = {
    "zasokese": Database(ZasokeseWord, "zasokese_database"),
    "thravelemeh": Database(ThravelemehWord, "thravelemeh_database"),
    "berquam": Database(BerquamWord, "zasokese_database", 1),
    "simetasispika": DialectDatabase(
        ZasokeseWord, "zasokese_database", zasokese_to_simetasise
    ),
    "4351": Database(SesameWord, "4351_database", 0),
    "iremna": Database(IremnaWord, "iremna_database", 0),
    "arteut": Database(ArteutWord, "arteut_database", 0),
    "enjie": EnjieDatabase("enjie_database"),
    "mikhoros": Database(MikhorosWord, "mikhoros_database"),
    "pain": SimpleDatabase("liki_database"),
    "fsovm": Database(FsovmWord, "fsovm_database"),
    "chrisancthian": PosDatabase("chrisancthian_database", 0, 0, 2, 1, 3),
    "scheskatte": Database(ScheskatteWord, "scheskatte_database", 1),
    "ropona": RoponaDatabase("ropona_database"),
    "lazhon": Database(LazhonWord, "lazhon_database", 0),
    "slengeus": Database(SlengeusWord, "slengeus_database", 0),
    "pasel": Database(PaselWord, "pasel_database", 0),
}

guild_ids = get_programwide("guild_ids")


async def handle_dictionary(
    ctx: SlashContext, database: Database, embed: Embed, query: str
):
    """
    Handles the dictionary command.

    :param ctx:
    :param database:
    :param embed:
    :param query: 검색어
    """
    message = await ctx.send(f"`{query}`에 대해 검색 중입니다…")

    words, duplicates, reloaded = await database.search_rows(query)
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
        embed.add_field(name="검색 결과", value="검색 결과가 없습니다.")
    if too_many:
        embed.add_field(
            name="기타",
            value=f"단어나 뜻에 `{query}`가 들어가는 단어가 {word_count - index_offset} 개 더 있습니다.",
        )

    await message.edit(
        content="데이터베이스를 다시 불러왔습니다." if reloaded else "", embed=embed
    )


class DictionaryCog(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @cog_ext.cog_slash(
        description="자소크어 단어를 검색합니다.",
        guild_ids=guild_ids,
        options=[
            create_option(
                name="query", description="검색할 단어", required=True, option_type=3
            )
        ],
    )
    async def zasok(self, ctx: SlashContext, query: str):
        if len(query) > 5:
            if any(
                query.startswith(prefix)
                for prefix in ("mò", "mà", "nò", "nà", "hò", "hà", "sò", "sà")
            ):
                query = query[2:]
            for character in "àèìòù":
                if character in query:
                    index = query.index(character)
                    query = query[:index]

        await handle_dictionary(
            ctx,
            databases["zasokese"],
            Embed(
                title=f"`{query}`의 검색 결과",
                description="자소크어 단어를 검색합니다.",
                color=get_const("shtelo_sch_vanilla"),
            ),
            query,
        )

    @cog_ext.cog_slash(
        description="트라벨레메 단어를 검색합니다.",
        guild_ids=guild_ids,
        options=[
            create_option(
                name="query", description="검색할 단어", required=True, option_type=3
            )
        ],
    )
    async def th(self, ctx: SlashContext, query: str):
        await handle_dictionary(
            ctx,
            databases["thravelemeh"],
            Embed(
                title=f"`{query}`의 검색 결과",
                description="트라벨레메 단어를 검색합니다.",
                color=get_const("hemelvaarht_hx_nerhgh"),
            ),
            query,
        )

    @cog_ext.cog_slash(
        description="베르쿠암 단어를 검색합니다.",
        guild_ids=guild_ids,
        options=[
            create_option(
                name="query", description="검색할 단어", required=True, option_type=3
            )
        ],
    )
    async def berquam(self, ctx: SlashContext, query: str):
        await handle_dictionary(
            ctx,
            databases["berquam"],
            Embed(
                title=f"`{query}`의 검색 결과",
                description="베르쿠암 단어를 검색합니다.",
                color=get_const("berquam_color"),
            ),
            query,
        )

    @cog_ext.cog_slash(
        description="시메타시스 단어를 검색합니다.",
        guild_ids=guild_ids,
        options=[
            create_option(
                name="query", description="검색할 단어", required=True, option_type=3
            )
        ],
    )
    async def sts(self, ctx: SlashContext, query: str):
        await handle_dictionary(
            ctx,
            databases["simetasispika"],
            Embed(
                title=f"`{query}`의 검색 결과",
                description="시메타시스어 단어를 검색합니다.",
                color=get_const("simetasis_color"),
            ),
            query,
        )

    @cog_ext.cog_slash(
        name="4351",
        description="4351 단어를 검색합니다.",
        guild_ids=guild_ids,
        options=[
            create_option(
                name="query", description="검색할 단어", required=True, option_type=3
            )
        ],
    )
    async def sesame(self, ctx: SlashContext, query: str):
        await handle_dictionary(
            ctx,
            databases["4351"],
            Embed(
                title=f"`{query}`의 검색 결과",
                description="4351의 단어를 검색합니다.",
                color=get_const("4351_color"),
            ),
            query,
        )

    @cog_ext.cog_slash(
        name="iremna",
        description="이렘나어 단어를 검색합니다.",
        guild_ids=guild_ids,
        options=[
            create_option(
                name="query",
                description="검색할 단어",
                required=True,
                option_type=SlashCommandOptionType.STRING,
            )
        ],
    )
    async def iremna(self, ctx: SlashContext, query: str):
        await handle_dictionary(
            ctx,
            databases["iremna"],
            Embed(
                title=f"`{query}`의 검색 결과",
                description="이렘나어 단어를 검색합니다.",
                color=get_const("iremna_color"),
            ),
            query,
        )

    @cog_ext.cog_slash(
        description="아르토이트어 단어를 검색합니다.",
        guild_ids=guild_ids,
        options=[
            create_option(
                name="query",
                description="검색할 단어",
                required=True,
                option_type=SlashCommandOptionType.STRING,
            )
        ],
    )
    async def arteut(self, ctx: SlashContext, query: str):
        await handle_dictionary(
            ctx,
            databases["arteut"],
            Embed(
                title=f"`{query}`의 검색 결과",
                description="아르토이트어 단어를 검색합니다.",
                color=get_const("arteut_color"),
            ),
            query,
        )

    @cog_ext.cog_slash(
        description="연서어 단어를 검색합니다.",
        guild_ids=guild_ids,
        options=[
            create_option(
                name="query",
                description="검색할 단어",
                required=True,
                option_type=SlashCommandOptionType.STRING,
            )
        ],
    )
    async def enjie(self, ctx: SlashContext, query: str):
        await handle_dictionary(
            ctx,
            databases["enjie"],
            Embed(
                title=f"`{query}`의 검색 결과",
                description="연서어 단어를 검색합니다.",
                color=get_const("enjie_color"),
            ),
            query,
        )

    @cog_ext.cog_slash(
        description="미코로스 아케뒤어 단어를 검색합니다.",
        guild_ids=guild_ids,
        options=[
            create_option(
                name="query",
                description="검색할 단어",
                required=True,
                option_type=SlashCommandOptionType.STRING,
            )
        ],
    )
    async def mikhoros(self, ctx: SlashContext, query: str):
        await handle_dictionary(
            ctx,
            databases["mikhoros"],
            Embed(
                title=f"`{query}`의 검색 결과",
                description="미코로스 아케뒤 단어를 검색합니다.",
                color=get_const("mikhoros_color"),
            ),
            query,
        )

    @cog_ext.cog_slash(
        description="파인어 단어를 검색합니다.",
        guild_ids=guild_ids,
        options=[
            create_option(
                name="query",
                description="검색할 단어",
                required=True,
                option_type=SlashCommandOptionType.STRING,
            )
        ],
    )
    async def pain(self, ctx: SlashContext, query: str):
        await handle_dictionary(
            ctx,
            databases["pain"],
            Embed(
                title=f"`{query}`의 검색 결과",
                description="파인어 단어를 검색합니다.",
                color=get_const("fliosen_color"),
            ),
            query,
        )

    @cog_ext.cog_slash(
        description="프소븜어 단어를 검색합니다.",
        guild_ids=guild_ids,
        options=[
            create_option(
                name="query",
                description="검색할 단어",
                required=True,
                option_type=SlashCommandOptionType.STRING,
            )
        ],
    )
    async def fsovm(self, ctx: SlashContext, query: str):
        await handle_dictionary(
            ctx,
            databases["fsovm"],
            Embed(
                title=f"`{query}`의 검색 결과",
                description="프소븜어 단어를 검색합니다.",
                color=get_const("tinudanma_color"),
            ),
            query,
        )

    @cog_ext.cog_slash(
        description="크리상테스어 단어를 검색합니다.",
        guild_ids=guild_ids,
        options=[
            create_option(
                name="query",
                description="검색할 단어",
                required=True,
                option_type=SlashCommandOptionType.STRING,
            )
        ],
    )
    async def chris(self, ctx: SlashContext, query: str):
        await handle_dictionary(
            ctx,
            databases["chrisancthian"],
            Embed(
                title=f"`{query}`의 검색 결과",
                description="크리상테스어 단어를 검색합니다.",
                color=get_const("chrisancthian_color"),
            ),
            query,
        )

    @cog_ext.cog_slash(
        description="셰스카테어 단어를 검색합니다.",
        guild_ids=guild_ids,
        options=[
            create_option(
                name="query",
                description="검색할 단어",
                required=True,
                option_type=SlashCommandOptionType.STRING,
            )
        ],
    )
    async def sches(self, ctx: SlashContext, query: str):
        await handle_dictionary(
            ctx,
            databases["scheskatte"],
            Embed(
                title=f"`{query}`의 검색 결과",
                description="셰스카테어 단어를 검색합니다.",
                color=get_const("scheskatte_color"),
            ),
            query,
        )

    @cog_ext.cog_slash(
        description="로포나어 단어를 검색합니다.",
        guild_ids=guild_ids,
        options=[
            create_option(
                name="query",
                description="검색할 단어",
                required=True,
                option_type=SlashCommandOptionType.STRING,
            )
        ],
    )
    async def ropona(self, ctx: SlashContext, query: str):
        await handle_dictionary(
            ctx,
            databases["ropona"],
            Embed(
                title=f"`{query}`의 검색 결과",
                description="로포나어 단어를 검색합니다.",
                color=get_const("ropona_color"),
            ),
            query,
        )

    @cog_ext.cog_slash(
        description="라졔르베라어(라죤) 단어를 검색합니다.",
        guild_ids=guild_ids,
        options=[
            create_option(
                name="query",
                description="검색할 단어",
                required=True,
                option_type=SlashCommandOptionType.STRING,
            )
        ],
    )
    async def lazhon(self, ctx: SlashContext, query: str):
        await handle_dictionary(
            ctx,
            databases["lazhon"],
            Embed(
                title=f"`{query}`의 검색 결과",
                description="라졔르베라어(라죤) 단어를 검색합니다.",
                color=get_const("lazha_color"),
            ),
            query,
        )

    @cog_ext.cog_slash(
        description="규조어 단어를 검색합니다.",
        guild_ids=guild_ids,
        options=[
            create_option(
                name="query",
                description="검색할 단어",
                required=True,
                option_type=SlashCommandOptionType.STRING,
            )
        ],
    )
    async def slengeus(self, ctx: SlashContext, query: str):
        await handle_dictionary(
            ctx,
            databases["slengeus"],
            Embed(
                title=f"`{query}`의 검색 결과",
                description="규조어 단어를 검색합니다.",
                color=get_const("slengeus_color"),
            ),
            query,
        )

    @cog_ext.cog_slash(
        description="파셀어 단어를 검색합니다.",
        guild_ids=guild_ids,
        options=[
            create_option(
                name="query",
                description="검색할 단어",
                required=True,
                option_type=SlashCommandOptionType.STRING,
            )
        ],
    )
    async def pasel(self, ctx: SlashContext, query: str):
        await handle_dictionary(
            ctx,
            databases["pasel"],
            Embed(
                title=f"`{query}`의 검색 결과",
                description="파셀어 단어를 검색합니다.",
                color=get_const("pasel_color"),
            ),
            query,
        )

    @cog_ext.cog_slash(
        description="데이터베이스를 다시 불러옵니다.",
        guild_ids=guild_ids,
        options=[
            create_option(
                name="language",
                description="데이터베이스를 불러올 언어를 설정합니다. 아무것도 입력하지 않으면 모든 언어의 데이터베이스를 다시 불러옵니다.",
                required=False,
                option_type=3,
                choices=list(databases.keys()),
            )
        ],
    )
    async def reload(self, ctx: SlashContext, language: str = ""):
        message = await ctx.send("데이터베이스를 다시 불러옵니다…")
        if language:
            if language not in databases:
                await message.edit(content="데이터베이스 이름을 확인해주세요!!")
                return

            databases[language].reload()
        else:
            for database in databases.values():
                database.reload()
                await sleep(0)
        await message.edit(
            content=f'{f"`{language}` " if language else ""}데이터베이스를 다시 불러왔습니다.'
        )

    @cog_ext.cog_slash(
        description="사전 링크를 알려줍니다.",
        guild_ids=guild_ids,
        options=[
            create_option(
                name="language",
                description="데이터베이스 링크를 확인할 언어를 설정합니다.",
                required=True,
                option_type=SlashCommandOptionType.STRING,
                choices=list(databases.keys()),
            )
        ],
    )
    async def dictionary(self, ctx: SlashContext, language: str = ""):
        dictionary_id = get_const(databases[language].spreadsheet_key)
        link = f"https://docs.google.com/spreadsheets/d/{dictionary_id}/edit#gid=0"

        embed = Embed(title="사전 링크", color=get_const("shtelo_sch_vanilla"))
        embed.add_field(
            name=f"`{language}` 사전의 링크", value=f"[여기를 클릭]({link})"
        )

        await ctx.send(embed=embed)


def setup(bot: Bot):
    bot.add_cog(DictionaryCog(bot))
