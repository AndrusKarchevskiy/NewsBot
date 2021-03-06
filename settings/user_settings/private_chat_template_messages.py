welcome_message = "Ты написал(а) новостному боту🤖\n\n<b>По умолчанию, он будет отправлять " \
                  "погоду из Москвы и одну новость по одной из ключевых тем: " \
                  "<i>Россия, бизнес, экономика, игры, образование</i> в 8:00 по МСК</b>\n\n" \
                  "✔У тебя есть возможность настроить бота под себя. Чтобы понять, как это сделать, введи команду " \
                  "<b>/help</b>\n" \
                  "✔Ты можешь нажимать на кнопки, чтобы получить нужную информацию прямо сейчас\n\n" \
                  "<i>Обрати внимание, что бот временно может не работать, всвязи с добавлением и тестированием " \
                  "новой функциональности. " \
                  "Пожалуйста, сообщай в группу <b>@andrus_news_chat</b> обо всех ошибках, опечатках, предлагай " \
                  "идеи для развития бота. Сейчас это очень важно для меня и создателя!</i>\n\n"

information_message = '<b>Способы настройки бота:</b>\n' \
                      '✔Чтобы сменить время отправления, введи команду <b>/set_time</b>\n' \
                      '✔Чтобы сменить город, из которого хочешь получать сводку погоды, ' \
                      'введи команду <b>/set_city</b>\n' \
                      '✔Чтобы выбрать ключевые слова (фразы), по которым ты будешь ' \
                      'получать новости, введи команду <b>/set_news_topic</b>\n' \
                      '\n✔Чтобы изменить количество отправляемых новостей, ' \
                      'введи команду <b>/set_quantity_news</b>\n✔Если что-то пошло не так, ' \
                      'введи команду <b>/reset</b>, чтобы вернуть стандартные настройки\n' \
                      '✔Если ты хочешь посмотреть свои текущие настройки, введи команду <b>/check_params</b>\n' \
                      '✔Если ты хочешь отказаться от рассылки, введи команду <b>/set_status</b>\n\n' \
                      '<b>Полезная информация:</b>\n' \
                      'При изменении настройки, её прошлое состояние удаляется, так что надо действовать аккуратно.\n' \
                      'У бота есть чат: <b>@andrus_news_chat</b>, в котором ' \
                      'ты можешь задать вопрос, предложить идею для развития бота. Так что не волнуйся, если у ' \
                      'тебя что-то не получается!\n\nОбрати внимание, что все функции бота бесплатны, ' \
                      'но если есть желание поддержать проект (помочь с оплатой сервера и т.п.), можешь ввести ' \
                      'команду <b>/donate</b>'

weather_emoji = {'дождь': '🌧', 'ливень': '⛈', 'гроза': '⛈', 'пасмурно': '☁', 'солнечно': '☀',
                 'ясно': '🌞', 'облачно': '☁', 'облачно с прояснениями': '⛅',
                 'снег': '❄', 'туманно': '🌫', 'град': '🌨', 'небольшая морось': '🌧',
                 'небольшой дождь': '🌧', 'переменная облачность': '⛅', 'небольшая облачность': '☁',
                 'гроза с небольшим дождём': '⛈', 'гроза с сильным дождём': '⛈'}

link_to_group = '<b>@andrus_news_chat</b>'

not_correct_param = '😕Была допущена ошибка при вводе параметра. <b>Изменение не ' \
                    'принято</b>. Введи команду ещё раз, повтори попытку. ' \
                    'Если что-то не получается, задай вопрос в чате ' + link_to_group

not_correct_message = '😕Введены некорректные данные. Если ты не понимаешь, почему ' \
                      'произошла ошибка, задай вопрос в чате ' + link_to_group
