import asyncio

from conf import token
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from aiogram.types import Message, CallbackQuery
import logging
import sqlite3

API_TOKEN = token
ADMIN = ''

conn = sqlite3.connect('db/db.db')
cur = conn.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS users(user_id INTEGER, user_money INTEGER, user_bet INTEGER ); """)
conn.commit()

kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
kb.add(types.InlineKeyboardButton(text="Узнать баланс пользователя"))
kb.add(types.InlineKeyboardButton(text="Добавить в ЧС"))
kb.add(types.InlineKeyboardButton(text="Убрать из ЧС"))
kb.add(types.InlineKeyboardButton(text="Статистика"))

ub = types.ReplyKeyboardMarkup(resize_keyboard=True)
ub.add(types.InlineKeyboardButton(text="Крутить"))
ub.add(types.InlineKeyboardButton(text="Баланс"))
ub.add(types.InlineKeyboardButton(text="Ставка"))

bk = types.ReplyKeyboardMarkup(resize_keyboard=True)
bk.add(types.InlineKeyboardButton(text='27'))
bk.add(types.InlineKeyboardButton(text='54'))
bk.add(types.InlineKeyboardButton(text='Своя ставка'))
bk.add(types.InlineKeyboardButton(text='Назад'))

logging.basicConfig(level=logging.INFO)
storage = MemoryStorage()
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)
win_dice = [1, 22, 43, 64]
stic = 'CAACAgIAAxkBAAEFQr1izri3u8l1l5lc5CJMYmMi43WXugACWR0AAhBSeUraB5i18F9KoykE'


class Stavka(StatesGroup):
    bet = State()


@dp.message_handler(commands=['start'])
async def start(message: Message):
    cur = conn.cursor()
    cur.execute(f"SELECT user_money FROM users WHERE user_id = {message.chat.id}")
    result = cur.fetchone()

    if message.from_user.id == ADMIN:
        await message.answer('Добро пожаловать в Админ-Панель! Выберите действие на клавиатуре', reply_markup=kb)


    else:
        if result is None:
            cur = conn.cursor()
            cur.execute(f'''SELECT * FROM users WHERE (user_id="{message.from_user.id}")''')
            entry = cur.fetchone()
            if entry is None:
                cur.execute(f'''INSERT INTO users VALUES ('{message.from_user.id}','1000','1')''')
                conn.commit()
                await message.answer_sticker(stic)
        else:
            await message.answer_sticker(stic)


@dp.message_handler(content_types=['text'], text="Ставка")
async def bet(message=types.Message):
    cur = conn.cursor()
    cur.execute(f"SELECT user_bet FROM users WHERE user_id = {message.chat.id}")
    result_bet = cur.fetchone()[0]

    await message.answer(f'Ваша ставка:{result_bet}\nВведите новую ставку:', reply_markup=ub)
    await Stavka.bet.set()


@dp.message_handler(state=Stavka.bet)
async def start(message: types.Message, state: FSMContext):
    cur = conn.cursor()
    cur.execute(f"SELECT user_money FROM users WHERE user_id = {message.chat.id}")
    result = cur.fetchone()
    res_ult = result[0]
    if message.text <= res_ult:

        async with state.proxy() as proxy:

            bet = message.text
            await state.finish()

        cur.execute(f"UPDATE users SET user_bet={bet} WHERE user_id={message.chat.id}")
        conn.commit()

        await message.answer(f"Ваша ставка:{bet}", reply_markup=ub)
    else:
        await message.answer("Введенная ставка больше баланса\nВведите ставку меньше!")


@dp.message_handler(content_types=['text'], text='Крутить')
async def cmd_dice(message: types.Message):
    cur = conn.cursor()
    cur.execute(f"SELECT user_money FROM users WHERE user_id = {message.chat.id}")
    result = cur.fetchone()

    x = int(result[0])
    if x > 0:

        value = await message.bot.send_dice(message.chat.id, emoji='🎰')
        result_dice = value.dice.value
        cur.execute(f"SELECT user_bet FROM users WHERE user_id = {message.chat.id}")
        user_bet = cur.fetchone()[0]
        if result_dice in win_dice:
            x += user_bet * 5
            cur.execute(f"UPDATE users SET user_money = {x}  WHERE user_id ={message.chat.id}")
            conn.commit()
            await asyncio.sleep(2)
            await message.answer(f"Вы выиграли!!!\nВаш баланс пополнен на {user_bet * 5}")
        else:
            x -= user_bet
            cur.execute(f"UPDATE users SET user_money = {x}  WHERE user_id ={message.chat.id}")
            conn.commit()
            await asyncio.sleep(2)
            await message.answer(f"Вы проиграли {user_bet}\nБаланс {x}")
    else:
        await message.answer("Пополните баланс")


@dp.message_handler(content_types=['text'], text="Баланс")
async def get_balance(message: types.Message):
    cur = conn.cursor()
    cur.execute(f"SELECT user_money FROM users WHERE user_id = {message.chat.id}")
    result = cur.fetchone()
    res = result[0]
    await message.answer(f'Ваш Баланс: {res}', reply_markup=ub)


@dp.message_handler(content_types=['text'], text='Статистика')
async def hfandler(message: types.Message):
    cur = conn.cursor()
    cur.execute('''select * from users''')
    results = cur.fetchall()
    await message.answer(f'Людей которые когда либо заходили в бота: {len(results)}')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
