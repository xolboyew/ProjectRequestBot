from aiogram.fsm.state import State, StatesGroup


class Reg(StatesGroup):
    first_name = State()
    last_name = State()
    phone = State()
    location = State()


class OrderFlow(StatesGroup):
    question = State()
    confirm = State()


class ProfileEdit(StatesGroup):
    name = State()
    phone = State()
    location = State()


class Contact(StatesGroup):
    write = State()


class AdminWrite(StatesGroup):
    message = State()


class Broadcast(StatesGroup):
    content = State()
    confirm = State()


class UIEdit(StatesGroup):
    emoji = State()
    text = State()
    wizard = State()


class SubAdd(StatesGroup):
    channel = State()


class TextEdit(StatesGroup):
    value = State()
