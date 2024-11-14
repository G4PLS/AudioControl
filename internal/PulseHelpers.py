import enum

import pulsectl
from loguru import logger as log

class DeviceFilter(enum.StrEnum):
    SINK = "sink",
    SOURCE = "source",

class PulseError(Exception):
    pass

def filter_proplist(proplist) -> str | None:
    filters: list[str] = [
        "alsa.card_name",
        "alsa.long_card_name",
        "node.name",
        "node.nick",
        "device.name",
        "device.nick",
        "device.description",
        "device.serial"
    ]

    weights: list[(str, int)] = [
        ('.', -50),
        ('_', -10),
        (':', -25),
        (';', -100),
        ('-', -5)
    ]

    length_weight: int = -5

    minimal_weights: list[(int, str)] = []

    for filter in filters:
        out: str = proplist.get(filter)

        if out is None or len(out) < 3:
            continue
        current_weight: int = 0

        current_weight += sum(out.count(weight[0]) * weight[1] for weight in weights)
        current_weight += (len(out) * length_weight)

        minimal_weights.append((current_weight, out))

    minimal_weights.sort(key=lambda x: x[0], reverse=True)

    if len(minimal_weights) > 0:
        return minimal_weights[0][1] or None
    return None


def get_device(filter: DeviceFilter, pulse_device_name):
    with pulsectl.Pulse("device-getter") as pulse:
        try:
            if filter == DeviceFilter.SINK:
                return pulse.get_sink_by_name(pulse_device_name)
            elif filter == DeviceFilter.SOURCE:
                return pulse.get_source_by_name(pulse_device_name)
        except Exception as e:
            log.error(e)
            raise PulseError
    return None


def get_device_list(filter: DeviceFilter):
    with pulsectl.Pulse("device-list-getter") as pulse:
        switch = {
            DeviceFilter.SINK: pulse.sink_list(),
            DeviceFilter.SOURCE: pulse.source_list(),
        }
        return switch.get(filter, {})


def get_volumes_from_device(device_filter: DeviceFilter, pulse_device_name: str):
    try:
        device = get_device(device_filter, pulse_device_name)
        device_volumes = device.volume.values
        return [round(vol * 100) for vol in device_volumes]
    except:
        return []


def change_volume(device, adjust):
    with pulsectl.Pulse("change-volume") as pulse:
        try:
            pulse.volume_change_all_chans(device, adjust * 0.01)
        except Exception as e:
            log.error(e)
            raise PulseError


def set_volume(device, volume):
    with pulsectl.Pulse("change-volume") as pulse:
        try:
            pulse.volume_set_all_chans(device, volume * 0.01)
        except Exception as e:
            log.error(e)
            raise PulseError


def mute(device, state):
    with pulsectl.Pulse("change-volume") as pulse:
        try:
            pulse.mute(device, state)
        except Exception as e:
            log.error(e)
            raise PulseError

def get_standard_device(device_filter: DeviceFilter):
    with pulsectl.Pulse("change-volume") as pulse:
        try:
            if device_filter == DeviceFilter.SINK:
                return get_device(device_filter, pulse.server_info().default_sink_name)
            elif device_filter == DeviceFilter.SOURCE:
                return get_device(device_filter, pulse.server_info().default_source_name)
            return None
        except Exception as e:
            log.error(e)
            raise PulseError