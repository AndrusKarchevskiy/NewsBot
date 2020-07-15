import requests
import xml.etree.ElementTree as ET


def message_former(currencies: dict) -> str:
    message_to_user = '<b>Курсы валют на сегодня. За единицу взят Российский рубль</b>\n\n'

    for valute in currencies:
        message_to_user += f'{currencies[valute][0]}<b>{valute} ({currencies[valute][1]}):</b> ' \
                           f'<i>{currencies[valute][2]}</i>\n'

    return message_to_user


def get_currencies(get_xml) -> str:
    """Возвращает словарь с полученными данными по нужным валютам"""
    structure = ET.fromstring(get_xml.content)

    flags = ('🇧🇾', '🇺🇦', '🇰🇿', '🇺🇸', '🇪🇺')
    i = 0

    currencies = {}

    for currency_id in ('R01090B', 'R01720', 'R01335', 'R01235', 'R01239'):
        valute_name = structure.find(f'./*[@ID="{currency_id}"]/Name').text
        valute_char_code = structure.find(f'./*[@ID="{currency_id}"]/CharCode').text
        valute_value = structure.find(f'./*[@ID="{currency_id}"]/Value').text
        state_flag = flags[i]

        currencies[valute_name] = (state_flag, valute_char_code, valute_value)
        i += 1

    formed_message = message_former(currencies)
    return formed_message


def get_message():
    xml_link = 'http://www.cbr.ru/scripts/XML_daily.asp'
    get_xml = requests.get(xml_link)
    return get_currencies(get_xml)
