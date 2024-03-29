import re
from asyncio import sleep
from copy import copy
from datetime import datetime
from json import load, JSONDecodeError
from random import choice, randint
from typing import Dict, List, Optional

from discord import Embed, TextChannel, VoiceChannel
from discord.ext import tasks
from discord.ext.commands import Cog, Bot
from discord_slash import cog_ext, SlashContext, SlashCommandOptionType
from discord_slash.utils.manage_commands import create_option
from http3 import AsyncClient
from sat_datetime import SatDatetime, SatTimedelta

from const import get_const, get_secret
from util import get_programwide, papago
from util.thravelemeh import WordGenerator, pool

TRANSLATABLE_TABLE = {
    'ko': ['en', 'ja', 'zh-CN', 'zh-TW', 'es', 'fr', 'ru', 'vi', 'th', 'id', 'de', 'it'],
    'zh-CN': ['zh-TW', 'ja'],
    'zh-TW': ['ja'],
    'en': ['ja', 'zh-CN', 'zh-TW', 'fr']
}
TO_LANGUAGES: List[str] = list()
for tls in TRANSLATABLE_TABLE.values():
    for tl in tls:
        if tl not in TO_LANGUAGES:
            TO_LANGUAGES.append(tl)

DICE_RE = re.compile(r'(\d+)?[dD](\d+) *([+\-]\d+)?')

guild_ids = get_programwide('guild_ids')


def create_pire_table():
    pipere_rome = 'ABCDEFGHIKLMNOPQRSTVUZ'
    pipere_gree = 'ΑΒΨΔΕΦΓΗΙΚΛΜΝΟΠϘΡΣΤѶΥΖ'

    result = {'OO': 'Ω', '-': '⳼'}
    result.update({r: g for r, g in zip(pipere_rome, pipere_gree)})
    for k, v in copy(result).items():
        result[k.lower()] = v.lower()

    result['q'] = 'ϟ'

    return result


def create_diac_table():
    with open('res/convert_table.json', 'r', encoding='utf-8') as file:
        data = load(file)
    return {k: v for k, v in sorted(data.items(), key=lambda x: len(x[0]), reverse=True)}


def lumiere_number(arabic):
    number_define = ['za', 'ho', 'san', 'ni', 'chi', 'la', 'pi', 'kan', 'kain', 'laio']
    result = ''

    for number in str(arabic):
        result += number_define[int(number)]

    return result


def merge_changes(change1, change2):
    original_oldid = int(change1[0])
    original_diff = int(change1[1])

    for creator in change2[2]:
        if creator not in change1[2]:
            change1[2].append(creator)

    return [
        min(original_oldid, change2[0]),
        max(original_diff, change2[1]),
        change1[2]
    ]


PIPERE_CONVERT_TABLE = create_pire_table()
DIAC_CONVERT_TABLE = create_diac_table()


class UtilityCog(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

        self.changes: Dict[str, List[int, int, str]] = dict()

        self.log_channel: Optional[TextChannel] = None

        self.update_zacalen_channel.start()

    def cog_unload(self):
        pass

    @Cog.listener()
    async def on_ready(self):
        while self.log_channel is None:
            await sleep(1)
            self.log_channel = self.bot.get_channel(get_const('changes_channel_id'))

        await self.log_channel.send(f':tools: {self.bot.user.mention}가 시작되었습니다. ({datetime.now()})')

        # zacalen channel
        await self.update_zacalen_channel()

    @tasks.loop(hours=1)
    async def update_zacalen_channel(self):
        channel: VoiceChannel = self.bot.get_channel(get_const('zacalen_channel_id'))

        if channel is None:
            await sleep(1)
            await self.update_zacalen_channel()
            return

        today = datetime.today()
        zacalen = SatDatetime.get_from_datetime(today)
        name = f'{today.year:04}-{today.month:02}-{today.day:02} ({"월화수목금토일"[today.weekday()]}): {zacalen.year}년'

        await channel.edit(name=name)

    @cog_ext.cog_slash(
        name='word',
        description='랜덤한 단어를 만들어줍니다.',
        options=[
            create_option(
                name='consonants',
                description='자음 목록 (콤마로 구분합니다.)',
                required=True,
                option_type=3
            ),
            create_option(
                name='vowels',
                description='모음 목록 (콤마로 구분합니다.)',
                required=True,
                option_type=3
            ),
            create_option(
                name='syllables',
                description='자음은 c, 모음은 v로 입력합니다. (대소문자 구분하지 않음, 콤마로 구분합니다.)',
                required=True,
                option_type=3
            ),
            create_option(
                name='count',
                description='만들 단어의 개수',
                required=False,
                option_type=4
            )
        ]
    )
    async def word(self, ctx: SlashContext, consonants: str, vowels: str, syllables: str, count: int = 10):
        syllables = syllables.lower()

        if syllables.replace('c', '').replace('v', '').replace(',', ''):
            await ctx.send('`syllables` 인자에는 `v`와 `c`만을 입력해주세요.')
            return

        syllables = syllables.split(',')

        message = await ctx.send('단어 생성중입니다...')

        consonants = consonants.split(',') if ',' in consonants else list(consonants)
        vowels = vowels.split(',') if ',' in vowels else list(vowels)

        words = list()
        for i in range(count):
            words.append(f'{i + 1}. ')
            syllable = choice(syllables)
            for character in syllable:
                words[-1] += choice(consonants) if character == 'c' else choice(vowels)

        embed = Embed(
            title='랜덤 생성 단어',
            description=', '.join(syllables),
            color=get_const('shtelo_sch_vanilla')
        )
        embed.add_field(name='단어 목록', value='\n'.join(words))

        await message.edit(embed=embed, content='')

    @cog_ext.cog_slash(
        name='thword',
        guild_ids=guild_ids,
        description='랜덤한 트라벨레메 단어를 만들어줍니다.'
    )
    async def thword(self, ctx: SlashContext):
        message = await ctx.send('단어 생성중입니다...')

        generator = WordGenerator()
        words = generator.generate_words()

        embed = Embed(
            title='랜덤 트라벨레메 단어',
            color=get_const('hemelvaarht_hx_nerhgh')
        )
        embed.add_field(name='단어 목록', value='\n'.join(words))

        await message.edit(embed=embed, content='')

    @cog_ext.cog_slash(
        name='thconverht',
        guild_ids=guild_ids,
        description='입력한 영단어를 트라벨레메식으로 변환합니다.',
        options=[
            create_option(
                name='word',
                description='변환할 영단어를 입력합니다.',
                option_type=SlashCommandOptionType.STRING,
                required=True
            ),
            create_option(
                name='countable',
                description='가산명사, 혹은 본동사인지 확인합니다.',
                option_type=SlashCommandOptionType.BOOLEAN,
                required=True
            )
        ]
    )
    async def thconverht(self, ctx: SlashContext, word: str, countable: bool = True):
        message = await ctx.send('단어 생성중입니다...')
        reversed_ = word[::-1]

        reversed_ = reversed_.replace('x', 'z')
        reversed_ = reversed_.replace('w', 'u')
        reversed_ = reversed_.replace('y', 'i')

        reversed_ = reversed_.replace('cc', 'c')
        reversed_ = reversed_.replace('dd', 'd')
        reversed_ = reversed_.replace('ll', 'l')
        reversed_ = reversed_.replace('oo', 'aa')
        reversed_ = reversed_.replace('rr', 'r')
        reversed_ = reversed_.replace('tt', 't')

        offset = 0
        for i, l in enumerate(reversed_):
            if l in pool.sons \
                    and i + offset + 1 < len(reversed_) \
                    and reversed_[i + offset + 1] not in pool.mothers \
                    and l not in pool.lmnhs:
                reversed_ = reversed_[:i + offset + 1] + 'h' + reversed_[i + offset + 1:]
                offset += 1

        if not countable:
            reversed_ += 'h'

        if reversed_[-1] == 'h' and reversed_[-2] in pool.mothers:
            reversed_ += 'h'

        if reversed_[-1] in pool.last_unlocatable:
            reversed_ += 'a'

        reversed_ = reversed_.replace('ia', 'ya')
        reversed_ = reversed_.replace('ie', 'ye')
        reversed_ = reversed_.replace('io', 'yo')
        reversed_ = reversed_.replace('iu', 'yu')

        reversed_ = reversed_.replace('ua', 'wa')
        reversed_ = reversed_.replace('ue', 'we')
        reversed_ = reversed_.replace('ui', 'wi')

        if reversed_[0] in pool.mothers_with_h:
            if len(reversed_) == 2:
                reversed_ = 'v' + reversed_
            if len(reversed_) == 4:
                reversed_ = 'j' + reversed_
            if len(reversed_) == 6:
                reversed_ = 'q' + reversed_

        embed = Embed(
            title='변환된 단어',
            color=get_const('hemelvaarht_hx_nerhgh')
        )
        embed.add_field(name=f'원래 단어: {word}', value=reversed_)

        await message.edit(embed=embed, content='')

    @cog_ext.cog_slash(
        description='주사위를 굴립니다.',
        options=[
            create_option(
                name='spec',
                description='굴림의 타입을 결정합니다. 기본값은 `1d6`입니다. (예시: `d6`, `2D20`, `6d10+4`)',
                option_type=3,
                required=False
            )
        ]
    )
    async def dice(self, ctx: SlashContext, spec: str = '1d6'):
        matching = DICE_RE.findall(spec)

        if len(matching) < 1:
            await ctx.send(
                '주사위 형태가 올바르지 않습니다! `{}` 형식을 만족하는 주사위만 사용할 수 있습니다. (예시: `d6`, `2D20`, `6d10+4`)'
                .format(r'`(\d+)?[dD](\d+) *([+\-]\d+)?`'))
            return

        dice = matching[0]
        count = int(dice[0]) if dice[0] else 1
        dice_type = int(dice[1]) if dice[1] else 6
        delta = int(dice[2]) if dice[2] else 0

        if count > 100:
            await ctx.send(f'주사위는 100개까지만 굴릴 수 있습니다. ({count}개 굴리기 시도함)')
            return

        numbers = list()
        sum_ = 0
        for _ in range(count):
            numbers.append(number := randint(1, dice_type))
            sum_ += number

        embed = Embed(title='주사위 굴림', description=spec)
        embed.add_field(name='굴린 주사위', value=', '.join(map(str, numbers)), inline=False)
        embed.add_field(name='눈 합', value=str(sum_))
        embed.add_field(name='델타', value=str(delta))
        embed.add_field(name='합계', value=f'**{sum_ + delta}**')

        await ctx.send(embed=embed)

    @cog_ext.cog_slash(
        description='계산 기능을 수행합니다.',
        options=[
            create_option(
                name='operation',
                description='수식을 입력합니다. (예: 1 + 2)',
                option_type=3,
                required=True
            )
        ]
    )
    async def calc(self, ctx: SlashContext, operation: str):
        for letter in operation:
            if letter not in '0123456789+-*/^(). =abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ,':
                await ctx.send('잘못된 수식입니다.')
                return

        if any(word in operation for word in ('help', 'exit', 'quit', 'ctx', 'dir', 'letter', 'operation', 'self')):
            await ctx.send('잘못된 수식입니다.')
            return

        # noinspection PyBroadException
        try:
            from math import sin, cos, tan, log, e, pi, factorial, sqrt, asin, acos, atan, sinh, cosh, tanh, asinh, \
                acosh, atanh, ceil, floor, exp, log10, log2, gcd, hypot, inf, nan
            result = eval(operation)
        except Exception:
            await ctx.send('잘못된 수식입니다.')
            return
        else:
            await ctx.send(f'`{operation} =` __{result}__')

    @cog_ext.cog_slash(
        description='자소크력을 계산합니다.',
        guild_ids=guild_ids,
        options=[
            create_option(
                name='year',
                description='자소크력을 계산할 년도를 입력합니다.',
                option_type=4,
                required=False
            ),
            create_option(
                name='month',
                description='자소크력을 계산할 월을 입력합니다.',
                option_type=4,
                required=False
            ),
            create_option(
                name='day',
                description='자소크력을 계산할 일을 입력합니다.',
                option_type=4,
                required=False
            ),
            create_option(
                name='hour',
                description='자소크력을 계산할 시간을 입력합니다.',
                option_type=4,
                required=False
            ),
            create_option(
                name='minute',
                description='자소크력을 계산할 분을 입력합니다.',
                option_type=4,
                required=False
            ),
            create_option(
                name='second',
                description='자소크력을 계산할 초를 입력합니다.',
                option_type=10,
                required=False
            ),
        ]
    )
    async def zacalen(self, ctx: SlashContext, year: int = -1, month: int = -1, day: int = -1,
                      hour: int = -1, minute: int = -1, second: float = -1.0):
        now = datetime.now()
        now = datetime(
            year if year != -1 else now.year,
            month if month != -1 else now.month,
            day if day != -1 else now.day,
            hour if hour != -1 else now.hour,
            minute if minute != -1 else now.minute,
            second if second != -1 else now.second
        )
        sat_datetime = SatDatetime.get_from_datetime(now)
        await ctx.send(f'> 서력 {now.year}년 {now.month}월 {now.day}일 {now.hour}시 {now.minute}분 {now.second}초 (UTC)는\n'
                       f'> 자소크력으로 __{sat_datetime.year}년 {sat_datetime.month}월 {sat_datetime.day}일 '
                       f'{sat_datetime.hour}시 {sat_datetime.minute}분 {sat_datetime.second:.1f}초 (ASN)__ 입니다.')

    @cog_ext.cog_slash(
        description='코르력을 계산합니다.',
        guild_ids=guild_ids,
        options=[
            create_option(
                name='year',
                description='코르력을 계산할 년도를 입력합니다.',
                option_type=4,
                required=False
            ),
            create_option(
                name='month',
                description='코르력을 계산할 월을 입력합니다.',
                option_type=4,
                required=False
            ),
            create_option(
                name='day',
                description='코르력을 계산할 일을 입력합니다.',
                option_type=4,
                required=False
            ),
            create_option(
                name='hour',
                description='코르력을 계산할 시간을 입력합니다.',
                option_type=4,
                required=False
            ),
            create_option(
                name='minute',
                description='코르력을 계산할 분을 입력합니다.',
                option_type=4,
                required=False
            ),
            create_option(
                name='second',
                description='코르력을 계산할 초를 입력합니다.',
                option_type=10,
                required=False
            ),
        ]
    )
    async def khorcalen(self, ctx: SlashContext, year: int = -1, month: int = -1, day: int = -1,
                        hour: int = -1, minute: int = -1, second: float = -1.0):
        now = datetime.now()
        now = datetime(
            year if year != -1 else now.year,
            month if month != -1 else now.month,
            day if day != -1 else now.day,
            hour if hour != -1 else now.hour,
            minute if minute != -1 else now.minute,
            second if second != -1 else now.second
        )
        sat_datetime = SatDatetime.get_from_datetime(now) - SatTimedelta(years=3276)
        await ctx.send(f'> 서력 {now.year}년 {now.month}월 {now.day}일 {now.hour}시 {now.minute}분 {now.second}초 (UTC)는\n'
                       f'> 코르력으로 __{sat_datetime.year}년 {sat_datetime.month}월 {sat_datetime.day}일 '
                       f'{sat_datetime.hour}시 {sat_datetime.minute}분 {sat_datetime.second:.1f}초 (ASN)__ 입니다.')

    @cog_ext.cog_slash(
        description='자소크력으로 서력 일자를 계산합니다.',
        guild_ids=guild_ids,
        options=[
            create_option(
                name='year',
                description='자소크력 년',
                option_type=SlashCommandOptionType.INTEGER,
                required=True
            ),
            create_option(
                name='month',
                description='자소크력 월',
                option_type=SlashCommandOptionType.INTEGER,
                required=False
            ),
            create_option(
                name='day',
                description='자소크력 일',
                option_type=SlashCommandOptionType.INTEGER,
                required=False
            )
        ]
    )
    async def inzacalen(self, ctx: SlashContext, year: int, month: int = 1, day: int = 1):
        sat_datetime = SatDatetime(year, month, day)
        christian_era = sat_datetime.to_datetime()
        await ctx.send(f'> 자소크력 {year}년 {month}월 {day}일 (ASN)은\n'
                       f'> 서력 __{christian_era.year}년 {christian_era.month}월 {christian_era.day}일 '
                       f'{christian_era.hour}시 {christian_era.minute}분 {christian_era.second:.1f}초 (UTC)__입니다.')

    @cog_ext.cog_slash(
        description='코르력으로 서력 일자를 계산합니다.',
        guild_ids=guild_ids,
        options=[
            create_option(
                name='year',
                description='코르력 년',
                option_type=SlashCommandOptionType.INTEGER,
                required=True
            ),
            create_option(
                name='month',
                description='코르력 월',
                option_type=SlashCommandOptionType.INTEGER,
                required=False
            ),
            create_option(
                name='day',
                description='코르력 일',
                option_type=SlashCommandOptionType.INTEGER,
                required=False
            )
        ]
    )
    async def inkhorcalen(self, ctx: SlashContext, year: int, month: int = 1, day: int = 1):
        sat_datetime = SatDatetime(year, month, day) + SatTimedelta(years=3276)
        christian_era = sat_datetime.to_datetime()
        await ctx.send(f'> 코르력 {year}년 {month}월 {day}일 (ASN)은\n'
                       f'> 서력 __{christian_era.year}년 {christian_era.month}월 {christian_era.day}일 '
                       f'{christian_era.hour}시 {christian_era.minute}분 {christian_era.second:.1f}초 (UTC)__입니다.')

    @cog_ext.cog_slash(
        description='광부위키 문서를 검색합니다.',
        guild_ids=guild_ids,
        options=[
            create_option(
                name='query',
                description='검색어를 입력합니다.',
                option_type=SlashCommandOptionType.STRING,
                required=True
            )
        ]
    )
    async def gwangbu(self, ctx: SlashContext, query: str):
        message = await ctx.send('광부위키 문서 검색 중...')

        client = AsyncClient()
        response = await client.get(
            f'http://wiki.shtelo.org/api.php?action=query&list=search&srsearch={query}&format=json')

        if response.status_code != 200:
            await message.edit(content='광부위키 문서 검색에 실패했습니다.')
            return

        data = response.json()
        if 'query' not in data or 'search' not in data['query']:
            await message.edit(content='광부위키 문서 검색에 실패했습니다.')
            return

        if not data['query']['search']:
            await message.edit(content='검색 결과가 없습니다.')
            return

        embed = Embed(title=f'`{query}` 광부위키 문서 검색 결과', color=get_const('sat_color'))
        for result in data['query']['search'][:25]:
            embed.add_field(
                name=result['title'],
                value=f'[보러 가기](http://wiki.shtelo.org/index.php/{result["title"].replace(" ", "_")})',
                inline=False)
        await message.edit(content=None, embed=embed)

    @cog_ext.cog_slash(
        description='여론조사를 실시합니다.',
        guild_ids=guild_ids,
        options=[
            create_option(
                name='title',
                description='여론조사 제목을 입력합니다.',
                option_type=SlashCommandOptionType.STRING,
                required=True
            ),
            create_option(
                name='content',
                description='여론조사 내용을 입력합니다.',
                option_type=SlashCommandOptionType.STRING,
                required=True
            ),
            create_option(
                name='answer_count',
                description='여론조사 정답의 개수를 입력합니다.',
                option_type=SlashCommandOptionType.INTEGER,
                required=True
            )
        ]
    )
    async def poll(self, ctx: SlashContext, title: str, content: str, answer_count: int):
        if answer_count < 2:
            await ctx.send('정답의 개수는 2개 이상이어야 합니다.')
            return
        elif answer_count > 20:
            await ctx.send('정답의 개수는 20개 이하이어야 합니다.')
            return

        message = await ctx.send(f'**{title}**\n> {content}')
        for i in range(answer_count):
            await message.add_reaction(chr(ord('🇦') + i))
            await sleep(0)

    @cog_ext.cog_slash(
        description='한국어 단어를 검색합니다.',
        guild_ids=guild_ids,
        options=[
            create_option(
                name='query',
                description='검색어를 입력합니다.',
                option_type=SlashCommandOptionType.STRING,
                required=True
            )
        ]
    )
    async def korean(self, ctx: SlashContext, query: str):
        message = await ctx.send(f'표준국어대사전에서 `{query}` 단어를 검색하는 중입니다…')

        client = AsyncClient()
        try:
            r = await client.get(
                'https://stdict.korean.go.kr/api/search.do',
                params={'key': get_secret('korean_dictionary_api_key'), 'q': query, 'req_type': 'json'},
                verify=False)
            j = r.json()
        except ConnectionResetError:
            await message.edit(content=f'`{query}`의 검색결과를 찾을 수 없습니다.')
            return
        except JSONDecodeError:
            await message.edit(content=f'`{query}`의 검색결과가 없습니다.')
            return
        else:
            words = j['channel']['item']

            embed = Embed(title=f'`{query}` 한국어 사전 검색 결과', color=get_const('korean_color'),
                          description='출처: 국립국어원 표준국어대사전')
            for word in words:
                embed.add_field(name=f"**{word['word']}** ({word['pos']})",
                                value=word['sense']['definition'] + f' [자세히 보기]({word["sense"]["link"]})',
                                inline=False)

            await message.edit(content=None, embed=embed)

    @cog_ext.cog_slash(
        description='피페레어 변환기를 실행합니다',
        guild_ids=guild_ids,
        options=[
            create_option(
                name='roman',
                description='로마자 문자열을 입력합니다.',
                option_type=SlashCommandOptionType.STRING,
                required=True
            )
        ]
    )
    async def pipeconv(self, ctx: SlashContext, roman: str):
        for k, v in PIPERE_CONVERT_TABLE.items():
            roman = roman.replace(k, v)

        await ctx.send(f'변환 결과:\n> {roman}')

    @cog_ext.cog_slash(
        description='뤼미에르 숫자로 변환합니다.',
        guild_ids=guild_ids,
        options=[
            create_option(
                name='arabic',
                description='아라비아 숫자를 입력합니다.',
                option_type=SlashCommandOptionType.INTEGER,
                required=True
            )
        ]
    )
    async def luminum(self, ctx: SlashContext, arabic: int):
        result = lumiere_number(arabic)
        await ctx.send(f'> **아라비아 숫자** : {arabic}\n> **뤼미에르 숫자** : {result}')

    @cog_ext.cog_slash(
        description='파파고 번역을 실행합니다.',
        guild_ids=guild_ids,
        options=[
            create_option(
                name='sentence',
                description='번역할 문장을 입력합니다.',
                option_type=SlashCommandOptionType.STRING,
                required=True
            ),
            create_option(
                name='from_language',
                description='출발 언어를 입력합니다.',
                option_type=SlashCommandOptionType.STRING,
                required=False,
                choices=list(TRANSLATABLE_TABLE.keys()),
            ),
            create_option(
                name='to_language',
                description='도착 언어를 입력합니다.',
                option_type=SlashCommandOptionType.STRING,
                required=False,
                choices=TO_LANGUAGES
            )
        ]
    )
    async def papago(self, ctx: SlashContext, sentence: str, from_language: str = 'ko', to_language: str = 'en'):
        if to_language not in TRANSLATABLE_TABLE[from_language]:
            languages = ', '.join(map(lambda x: f'`{x}`', TRANSLATABLE_TABLE[from_language]))
            await ctx.send(f'시작 언어가`{from_language}`인 경우에는 도착 언어로 다음만 선택할 수 있습니다!\n'
                           f'> {languages}')
            return

        result = papago.translate(sentence, from_language, to_language)
        await ctx.send(f'번역문\n> {sentence}\n번역 결과\n> {result}')

    @cog_ext.cog_slash(
        description='다이어크리틱을 포함한 문자열을 출력합니다.',
        guild_ids=guild_ids,
        options=[
            create_option(
                name='string',
                description='변환할 문자열을 입력합니다.',
                option_type=SlashCommandOptionType.STRING,
                required=True
            )
        ]
    )
    async def diac(self, ctx: SlashContext, string: str):
        for key, value in DIAC_CONVERT_TABLE.items():
            string = string.replace(key, value)
            if key.islower():
                string = string.replace(key.upper(), value.upper())
        await ctx.send(string)

    @cog_ext.cog_slash(
        description='디스코드 snowflake로 정보를 알아냅니다',
        guild_ids=guild_ids,
        options=[
            create_option(
                name='snowflake',
                description='snowflake를 입력합니다.',
                option_type=SlashCommandOptionType.STRING,
                required=True
            )
        ]
    )
    async def snow(self, ctx: SlashContext, snowflake: str):
        snowflake = int(snowflake)
        time = datetime.fromtimestamp(((snowflake >> 22) + 1420070400000) / 1000)
        worker_id = (snowflake >> 17) & 0x1F
        process_id = (snowflake >> 12) & 0x1F
        increment = snowflake & 0xFFF

        embed = Embed(title='Snowflake 정보', description=f'`{snowflake}`')
        embed.add_field(name='생성 시간', value=str(time), inline=False)
        embed.add_field(name='Worker ID', value=str(worker_id))
        embed.add_field(name='Process ID', value=str(process_id))
        embed.add_field(name='Increment', value=str(increment))

        await ctx.send(embed=embed)


def setup(bot: Bot):
    bot.add_cog(UtilityCog(bot))
