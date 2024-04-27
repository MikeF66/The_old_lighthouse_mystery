import pygame
import sys
from pygame.locals import *
import sqlite3

# Создаем подключение к базе данных
conn = sqlite3.connect('game_database.db')
c = conn.cursor()

# Создаем таблицу "Персонажи"
c.execute('''CREATE TABLE IF NOT EXISTS Characters (
             id INTEGER PRIMARY KEY,
             name TEXT NOT NULL,
             image ImagePath,
             location INTEGER,
             FOREIGN KEY(location) REFERENCES Locations(id)
             )''')

# Создаем таблицу "Локации"
c.execute('''CREATE TABLE IF NOT EXISTS Locations (
             id INTEGER PRIMARY KEY,
             index INTEGER,
             name TEXT NOT NULL,
             description TEXT,
             background_image ImagePath,
             music ClipPath,
             artefact INTEGER,
             FOREIGN KEY(artefact) REFERENCES Artefacts(id)
             )''')

# Создаем таблицу "Артефакты"
c.execute('''CREATE TABLE IF NOT EXISTS Artefacts (
             id INTEGER PRIMARY KEY,
             name TEXT NOT NULL,
             description TEXT,
             status Boolean
             )''')

# Создаем таблицу "Диалоги"
c.execute('''CREATE TABLE IF NOT EXISTS Dialogs (
             id INTEGER PRIMARY KEY,
             speaker TEXT NOT NULL,
             text TEXT,
             voice_clip AudioClipPath,
             location INTEGER,
             FOREIGN KEY(location) REFERENCES Locations(id)
             )''')

# Загружаем персонажей из SQLite

# Сохраняем изменения
conn.commit()

conn.close()

pygame.init()  # инициализация pygame

# Функция для получения данных из баззы данных
def get_data(tablename):
    conn = sqlite3.connect('game_database.db')
    c = conn.cursor()
    c.execute(f"SELECT * FROM {tablename}")
    data = c.fetchall()
    conn.close()
    return data

SCREEN_WIDTH = 1024  # размеры окна выбрал такими, потому что картинки 1024 х 512,
SCREEN_HEIGHT = 512  # можно обрезать картинки (или заново сгенерить) если нужен другой размер окна

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))  # создаем окно игры

class Location:    # класс локации, все атрибуты можно хранить и загружать из SQLite
    def __init__(self, background_image_path, music_path, options=None):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.background = pygame.image.load(background_image_path)
        self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.font = pygame.font.Font(None, 24)
        self.clock = pygame.time.Clock()
        pygame.display.set_caption("Тайна старого маяка")
        self.music_path = music_path
        self.dialog = []
        self.next_locations = []
        self.options = options if options else []
        self.character_images = {}  # словарь для хранения изображений персонажей
        self.voice_clips = {}  # словарь для хранения звуковых файлов диалогов

    def load_character_image(self, character_name, image_path):
        image = pygame.image.load(image_path)
        self.character_images[character_name] = pygame.transform.scale(image, (1024, 512))

    def load_voice_clip(self, dialog_id, clip_path):
        self.voice_clips[dialog_id] = pygame.mixer.Sound(clip_path)

    def play_voice_clip(self, dialog_id):
        if dialog_id in self.voice_clips:
            # Приглушение фоновой музыки во время диалога
            pygame.mixer.music.set_volume(0.2)
            self.voice_clips[dialog_id].play()
            # Ожидание окончания воспроизведения звукового файла
            while pygame.mixer.get_busy():
                pygame.time.delay(100)

            # Восстановление громкости фоновой музыки
            pygame.mixer.music.set_volume(1.0)

    def run_dialog(self):  # функция диалогов
        index = 0
        last_index = -1  # переменная для отслеживания последнего воспроизведённого индекса
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()  # выход из игры
                    sys.exit()
                elif event.type == KEYDOWN:
                    if event.key == K_SPACE:  # листаем фразы диалога клавишей Пробела
                        if index < len(self.dialog) - 1:
                            index += 1
                        else:
                            running = False  # выход из диалога
                    elif event.key == K_BACKSPACE:
                        pygame.quit()
                        sys.exit()

            self.screen.blit(self.background, (0, 0))
            speaker, text = self.dialog[index]
            if speaker in self.character_images:
                character_image = self.character_images[speaker]
                self.screen.blit(character_image, (0, 0))  # Позиция изображения персонажа
            self.draw_text(f"{speaker}: {text}", (100, 450))  # Рисуем текст поверх изображения персонажа
            pygame.display.update()

            if last_index != index:  # проверяем, изменился ли индекс
                last_index = index  # обновляем последний индекс
                self.play_voice_clip(index)  # воспроизведение звукового файла для текущей реплики по индексу

            self.clock.tick(60)


    def start_music(self):                            # запускает звуковой файл
        pygame.mixer.music.load(self.music_path)
        pygame.mixer.music.play(-1,0.0)                   # бесконечное воспроизведение звука

    def draw_text(self, text, position, font_size=24, max_width=850):
        font = pygame.font.Font(None, font_size)  # Создаем шрифт заданного размера
        words = text.split(' ')  # Разбиваем текст на слова
        x, y = position
        space = font.size(' ')[0]  # Ширина пробела
        current_line = []
        current_width = 0

        for word in words:
            word_surface = font.render(word, True, (255, 255, 255))
            word_width, word_height = word_surface.get_size()
            if max_width is not None and current_width + word_width >= max_width:
                # Если добавление слова превышает максимальную ширину, выводим текущую строку
                line_surface = font.render(' '.join(current_line), True, (255, 255, 255))
                self.screen.blit(line_surface, (x, y))
                y += word_height  # Перемещаемся на следующую строку
                current_line = [word]  # Начинаем новую строку с текущего слова
                current_width = word_width + space
            else:
                # Добавляем слово в текущую строку
                current_line.append(word)
                current_width += word_width + space

        # Вывод последней строки
        line_surface = font.render(' '.join(current_line), True, (255, 255, 255))
        self.screen.blit(line_surface, (x, y))

    def choose_action(self):  # выбор перехода к следующей локации
        opt = None            # opt - переменная сделанного выбора
        while opt is None:
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == KEYDOWN:
                    if event.key == K_1 and len(self.options) >= 1:    # выбор из двух вариантов
                        opt = 0                                        # можно сделать больше при большом желании,
                    elif event.key == K_2 and len(self.options) >= 2:  # но я думаю нам двух достаточно
                        opt = 1
                    if opt is not None:                                # когда выбор сделан, opt is not None, - остановка воспроизведения звука
                        pygame.mixer.music.stop()
            self.screen.blit(self.background, (0, 0))
            for i, option in enumerate(self.options):
                self.draw_text(f"{i + 1}. {option}", (100, 50 + 30 * i), font_size=22) # вывод надписей для выбора следующей локации
            pygame.display.update()
            self.clock.tick(60)
        return opt



    def run(self):  # запуск всех методов локации

        self.start_music()
        self.run_dialog()
        opt = self.choose_action()
        if opt is not None and opt < len(self.next_locations):
            next_location = self.next_locations[opt]
            if next_location:
                next_location.run()
        else:
            pygame.quit()

class Menu:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 24)
        self.menu_items = ["Продолжить игру", "Начать новую игру", "Сохранить игру", "Загрузить игру", "Настройки", "Выход"]
        self.selected_item = 0
        self.active = False

    def draw_menu(self):
        dark_overlay = pygame.Surface(self.screen.get_size())
        dark_overlay.set_alpha(200)
        dark_overlay.fill((0, 0, 0))
        self.screen.blit(dark_overlay, (0, 0))

        blur_surface = pygame.transform.scale(self.screen, (SCREEN_WIDTH // 10, SCREEN_HEIGHT // 10))
        blur_surface = pygame.transform.scale(blur_surface, (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.screen.blit(blur_surface, (0, 0))

        for i, item in enumerate(self.menu_items):
            color = (255, 255, 255) if i == self.selected_item else (150, 150, 150)
            text = self.font.render(item, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + i * 30))
            self.screen.blit(text, text_rect)

    def move_selection(self, direction):
        self.selected_item = (self.selected_item + direction) % len(self.menu_items)

    def toggle_menu(self):
        self.active = not self.active
        if self.active:
            self.selected_item = 0

    def run_menu(self):
        while self.active:
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == KEYDOWN:
                    if event.key == K_UP:
                        self.move_selection(-1)
                    elif event.key == K_DOWN:
                        self.move_selection(1)
                    elif event.key == K_RETURN:
                        if self.selected_item == 0:  # выбор "Продолжить игру"
                            self.active = False
                        elif self.selected_item == 1:  # выбор "Начать новую игру"
                            # Логика для начала новой игры (очистка базы данных и переход к первой локации)
                            self.clear_game_data()
                            self.active = False
                        elif self.selected_item == 2:  # выбор "Сохранить игру"
                            # Логика для сохранения игры
                            self.save_game()
                            self.active = False
                        elif self.selected_item == 3:  # выбор "Загрузить игру"
                            self.toggle_menu()
                        elif self.selected_item == 4:  # выбор "Настройки"
                            # Логика для открытия меню настроек
                            # (необходимо реализовать отдельный класс для меню настроек)
                            pass
                        elif self.selected_item == 5:  # выбор "Выход"
                            pygame.quit()
                            sys.exit()

    def clear_game_data(self):
        # Логика для очистки базы данных (начало новой игры)
        pass

    def save_game(self):
        # Логика для сохранения игры
        pass

class Notebook:
    def __init__(self, screen):
        self.screen = screen  # Экран для отображения записной книжки
        self.active = False  # Флаг активации записной книжки
        self.notebook_data = []  # Данные для отображения в таблице SQL

    def open_notebook(self):
        self.active = True
        # Реализация открытия и отображения записной книжки (можно использовать SQL-запросы для отображения данных)

    def close_notebook(self):
        self.active = False
        # Реализация закрытия записной книжки и возвращения к игре

    def display_notebook(self):
        # Реализация отображения таблицы SQL с подсказками и артефактами
        if self.notebook_data:
            for row in self.notebook_data:
                self.screen.blit(row[0], row[1])
        else:
            self.screen.blit(self.font.render("Записная книжка пуста", True, (255, 255, 255)), (10, 10))



notebook = Notebook(screen)

# Код для обработки событий
while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == KEYDOWN:
            if event.key == K_TAB:  # При нажатии клавиши Tab
                notebook.open_notebook()  # Открываем записную книжку
            else:
                notebook.close_notebook()  # Закрываем записную книжку

                # Получаем данные из таблиц и выводим их на экран "Записной книжки игрока"
            # character_data = get_data("Characters")
            # location_data = get_data("Locations")
            # artefact_data = get_data("Artefacts")
            # # Вывод данных на экран "Записной книжки игрока"
            # for row in character_data:
            #     print(row)
            # for row in location_data:
            #     print(row)
            # for row in artefact_data:
            #     print(row)



menu = Menu(screen)  # Создаём экземпляр меню

# Загрузка фона
background = pygame.Surface(screen.get_size())
background.fill((50, 50, 50))  # Заполняем фон серым цветом для примера

while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                menu.toggle_menu()

    screen.blit(background, (0, 0))

    if menu.active:
        menu.draw_menu()

    pygame.display.update()









if __name__ == '__main__':
    loc01 = Location('Location01_Prolog/loc01_Pab.jpg', 'Location01_Prolog/plesk-voln.mp3', ["Посетить местный паб", "Вариант 2"])

    loc1_1 = Location('loc1_1.jpg', 'loc1_1.mp3', ["Изучить записку", "Расспросить посетителей бара"]) # создание локаций: loc1 - первая локация, _1 - первая сцена
    loc1_2 = Location('loc1_2.jpg', 'loc1_2.mp3', ["Дом сторожа маяка", "Вариант 2"])                  # локация: loc1_2 - первая локация, вторая сцена
    loc1_3 = Location('loc1_3.jpg', 'loc1_3.mp3', ["Дом сторожа маяка", "Вариант 2"])
    loc2_1 = Location('loc2_1.jpg', 'loc2_1.mp3', ["Прибрежный лес", "Вариант 2"])
    loc3_1 = Location('loc3_1.jpg', 'loc3_1.mp3', ["Старый маяк", "Вариант 2"])
    loc4_1 = Location('loc4_1.jpg', 'loc4_1.mp3', ["Призрак старого хозяина маяка", "Вариант 2"])       # локация: loc4_1 - четвертая локация, первая сцена
    loc4_2 = Location('loc4_2.jpg', 'loc4_2.mp3', ["Вариант 1", "Вариант 2"])

    loc01.next_locations = [loc1_1,loc1_3]
    loc1_1.next_locations = [loc1_2, loc1_3] # Выбор варианта следующей локации: либо loc1_2, либо loc1_3
    loc1_2.next_locations = [loc2_1, loc1_1] # Поскольку еще нет ветвления сюжета, при выборе второго варианта
    loc1_3.next_locations = [loc2_1, loc1_1] # во всех локациях кроме первой записан переход на loc1_1
    loc2_1.next_locations = [loc3_1, loc1_1]
    loc3_1.next_locations = [loc4_1, loc1_1]
    loc4_1.next_locations = [loc4_2, loc1_1]
    loc4_2.next_locations = [loc1_1, loc1_1]

    loc01.dialog = [("Диктор", "Диктор: Молодой журналист Кирилл приезжает в небольшой прибрежный городок, "
                               "чтобы написать статью о старом маяке, окруженном мрачными легендами и тайнами. "
                               "По прибытии, Кирилл узнает о недавнем исчезновении местного сторожа маяка "
                               "и решает начать собственное расследование.")]

    loc1_1.dialog = [("Кирилл", "Здравствуйте, я Кирилл, новенький здесь."),         # диалоги: loc1_1.dialog - диалог первой локации первой сцены
                     ("Бармен", "Приветствую, Кирилл! Что вам налить?"),
                     ("Кирилл",
                      "Кофе, пожалуйста! Я слышал, что вы можете рассказать много интересного о старом маяке."),
                     ("Бармен", "Да, маяк... Он уже много лет беспокоит умы местных."),
                     ("Кирилл", "Я весь во внимании, Расскажите."),
                     ("Бармен", " Странности начались, когда последний сторож исчез без вести."),
                     ("Бармен",
                      "А недавно кто-то видел странные огни там. Кстати, вы не первый, кто интересуется маяком."),
                     ("Бармен", "Недавно тут был детектив, оставил записку, но так и не вернулся."),
                     ("Кирилл", "Записка? Можно мне её посмотреть?"),
                     ("Бармен", "Конечно, держите. Надеюсь, она поможет вам больше, чем тому бедняге.")]
    loc1_2.dialog = [("Персонаж 1", "Текст к локации: Записка с криптографической загадкой, оставленная предыдущим детективом."),
                     ("Персонаж 2", "Текст к локации."),
                     ("Персонаж 1", "Текст к локации."),
                     ("Персонаж 2", "Текст к локации.")]
    loc1_3.dialog = [("Персонаж 1", "Текст к локации: Диалог с посетителем бара."),
                     ("Персонаж 2", "Текст к локации."),
                     ("Персонаж 1", "Текст к локации."),
                     ("Персонаж 2", "Текст к локации.")]
    loc2_1.dialog = [("Персонаж 1", "Текст к локации: Дом сторожа маяка."),         # диалог loc2_1.dialog - диалог второй локации первой сцены
                     ("Персонаж 2", "Текст к локации."),
                     ("Персонаж 1", "Текст к локации."),
                     ("Персонаж 2", "Текст к локации.")]
    loc3_1.dialog = [("Персонаж 1", "Текст к локации: Прибрежный лес."),
                     ("Персонаж 2", "Текст к локации."),
                     ("Персонаж 1", "Текст к локации."),
                     ("Персонаж 2", "Текст к локации.")]
    loc4_1.dialog = [("Персонаж 1", "Текст к локации: Старый маяк."),
                     ("Персонаж 2", "Текст к локации."),
                     ("Персонаж 1", "Текст к локации."),
                     ("Персонаж 2", "Текст к локации.")]
    loc4_2.dialog = [("Персонаж 1", "Текст к локации: Призрак старого хозяина маяка."),
                     ("Персонаж 2", "Текст к локации."),
                     ("Персонаж 1", "Текст к локации."),
                     ("Персонаж 2", "Текст к локации.")]

    loc01.load_voice_clip(0, 'Location01_Prolog/Prolog.mp3')

    loc1_1.load_voice_clip(0, 'Location1_dialogs/loc1_1_01.mp3')
    loc1_1.load_voice_clip(1, 'Location1_dialogs/loc1_1_02b.mp3')
    loc1_1.load_voice_clip(2, 'Location1_dialogs/loc1_1_03.mp3')
    loc1_1.load_voice_clip(3, 'Location1_dialogs/loc1_1_04b.mp3')
    loc1_1.load_voice_clip(4, 'Location1_dialogs/loc1_1_05.mp3')
    loc1_1.load_voice_clip(5, 'Location1_dialogs/loc1_1_06b.mp3')
    loc1_1.load_voice_clip(6, 'Location1_dialogs/loc1_1_07b.mp3')
    loc1_1.load_voice_clip(7, 'Location1_dialogs/loc1_1_08b.mp3')
    loc1_1.load_voice_clip(8, 'Location1_dialogs/loc1_1_09.mp3')
    loc1_1.load_voice_clip(9, 'Location1_dialogs/loc1_1_10b.mp3')

    loc01.character_images['Диктор'] = pygame.image.load('Location01_Prolog/loc01_Pab.jpg')
    loc1_1.character_images['Кирилл'] = pygame.image.load('Location1_dialogs/Kirill.jpeg')
    loc1_1.character_images['Бармен'] = pygame.image.load('Location1_dialogs/Barmen.jpeg')




    loc01.run()  # запуск первой локации, первой сцены
