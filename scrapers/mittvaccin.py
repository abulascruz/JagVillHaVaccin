from datetime import datetime
import time
from time import mktime

from service.downloader import Downloader

BASE_URL = 'https://booking-api.mittvaccin.se/clinique/'
DATE_STRUCT = "%y%m%d"

NO_SLOTS = {'next': None, 'amount_of_slots': 0}


def get_appointment_types(id):
    return Downloader.get_json('{}{}/appointmentTypes'.format(BASE_URL, id))


def get_slots(id, appointment_type_id, start_date, end_date):
    start = start_date.strftime(DATE_STRUCT)
    end = end_date.strftime(DATE_STRUCT)

    url = '{}{}/appointments/{}/slots/{}-{}'.format(BASE_URL, id,
                                                    appointment_type_id, start,
                                                    end)
    return Downloader.get_json(url)


def get_next_time_and_slots(id, start_date, end_date):
    types = get_appointment_types(id)

    if not types: return NO_SLOTS

    types_id = [type['id'] for type in types]

    all_available_slots = []

    for type_id in types_id:
        days = get_slots(id, type_id, start_date, end_date)

        if not days: return NO_SLOTS

        for day in days:
            slots = day['slots']
            available_slots = [
                slot['when'] for slot in slots if slot['available']
            ]
            if len(available_slots) > 0:
                available_slots = {
                    'day': day['date'],
                    'times': available_slots
                }
                all_available_slots.append(dict(available_slots))

    if len(all_available_slots) > 0:
        next_slot = all_available_slots[0]
        next_slot = date_from(next_slot['day'], next_slot['times'][0])

        amount_of_slots = 0

        for day in all_available_slots:
            amount_of_slots += len(day['times'])

        return {'next': next_slot, 'amount_of_slots': amount_of_slots}

    return NO_SLOTS


def get_id_from_url(url):
    id = url.replace('https://bokning.mittvaccin.se/klinik/', '')
    id = id.replace('/bokning', '')
    id = id.replace('/min-bokning', '')
    return id


def get_url_from_id(id):
    return 'https://bokning.mittvaccin.se/klinik/{}'.format(id)

def normalise_url(url):
    return get_url_from_id(get_id_from_url(url))

def date_from(slotDate, slotTime):
    struct = time.strptime('{}{}'.format(slotDate, slotTime), "%y%m%d%H:%M")
    return datetime.fromtimestamp(mktime(struct))


def get_info(id):
    url = BASE_URL + str(id)
    json = Downloader.get_json(url)
    if len(json) == 0:
        print("Id not used: {}".format(id))
    else:
        json = json[0]
        name = json['name']
        style = json['style']
        print("{} - {}".format(name, style))
        if style != 0:
            types = get_appointment_types(id)
            covid_vaccine_types = [
                type['name'] for type in types
                if "covid" in type['name'].lower()
                and "vaccin" in type['name'].lower()
            ]
            return {
                "id": id,
                "name": name,
                "style": style,
                "covid_types": covid_vaccine_types
            }
