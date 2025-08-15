from aiogram.fsm.state import State, StatesGroup

# Состояния для рассылки
class MailingStates(StatesGroup):
    waiting_for_text = State()
    waiting_for_photo = State()
    mailing_text = State()
    mailing_photo = State()

# Состояния для управления пользователями
class UserManagementStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_action = State()

# Состояния для экспорта данных
class ExportStates(StatesGroup):
    waiting_for_format = State()
    waiting_for_confirmation = State()

# Состояния для массовых операций
class MassOperationsStates(StatesGroup):
    waiting_for_confirmation = State()
    processing = State()

# Состояния для настроек админа
class AdminSettingsStates(StatesGroup):
    waiting_for_min_stars = State()

# Состояния для системы чеков
class CheckSystemStates(StatesGroup):
    waiting_for_stars_amount = State()
    waiting_for_check_description = State()
    waiting_for_check_id_to_delete = State() 