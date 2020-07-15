import requests
import xml.etree.ElementTree as ET


def base_message_former(currencies: dict) -> str:
    message_to_user = '<b>Курсы валют на сегодня. За единицу взят Российский рубль</b>\n\n'

    for valute in currencies:
        message_to_user += f'{currencies[valute][0]}<b>{valute} ({currencies[valute][1]}):</b> ' \
                           f'<i>{currencies[valute][2]}</i>\n'

    return message_to_user


def detailed_message_former(currencies: dict) -> str:
    message_to_user = f''

    for valute in currencies:
        message_to_user += f'{currencies[valute][0]}<b>{valute} ({currencies[valute][1]}):</b> ' \
                           f'<i>{currencies[valute][2]}</i>\n'

    return message_to_user


def get_base_currencies(get_xml) -> str:
    """Возвращает словарь с полученными данными по валютам: доллар, евро"""
    structure = ET.fromstring(get_xml.content)

    flags = ('🇺🇸', '🇪🇺')

    i = 0
    currencies = {}

    for currency_id in ('R01235', 'R01239'):
        valute_name = structure.find(f'./*[@ID="{currency_id}"]/Name').text
        valute_char_code = structure.find(f'./*[@ID="{currency_id}"]/CharCode').text
        valute_value = structure.find(f'./*[@ID="{currency_id}"]/Value').text
        state_flag = flags[i]

        currencies[valute_name] = (state_flag, valute_char_code, valute_value)
        i += 1

    formed_message = base_message_former(currencies)
    return formed_message


def get_detailed_currencies(get_xml) -> str:
    """Возвращает словарь с полученными данными по другим некоторым валютам"""
    structure = ET.fromstring(get_xml.content)

    flags = ('🏴󠁧󠁢󠁥󠁮󠁧󠁿', '🇧🇾', '🇺🇦', '🇰🇿', '🇦🇲')
    dividers = (1, 1, 10, 100, 100)
    i = 0
    currencies = {}

    for currency_id in ('R01035', 'R01090B', 'R01720', 'R01335', 'R01060'):
        valute_name = structure.find(f'./*[@ID="{currency_id}"]/Name').text
        valute_char_code = structure.find(f'./*[@ID="{currency_id}"]/CharCode').text
        valute_value = structure.find(f'./*[@ID="{currency_id}"]/Value').text.replace(',', '.')
        valute_value = float(valute_value) / dividers[i]
        valute_value = str(valute_value).replace('.', ',')
        state_flag = flags[i]

        currencies[valute_name] = (state_flag, valute_char_code, valute_value)
        i += 1

    formed_message = detailed_message_former(currencies)
    return formed_message


def get_base_message():
    xml_link = 'http://www.cbr.ru/scripts/XML_daily.asp'
    get_xml = requests.get(xml_link)
    return get_base_currencies(get_xml)


def get_detailed_message():
    xml_link = 'http://www.cbr.ru/scripts/XML_daily.asp'
    get_xml = requests.get(xml_link)
    return get_detailed_currencies(get_xml)
