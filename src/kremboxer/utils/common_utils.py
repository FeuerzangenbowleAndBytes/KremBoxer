import datetime
import numpy as np


def construct_datetime(year, month, day, hours_utc, minutes, seconds):
    if int(year) == 0:
        return datetime.datetime.min
    dt = datetime.datetime(year=int(year),
                           month=int(month),
                           day=int(day),
                           hour=int(hours_utc),
                           minute=int(minutes),
                           second=int(seconds),
                           tzinfo=datetime.timezone.utc)
    return dt


def get_signal_bounds(data: np.array, p_start: float, p_end: float):
    """
    Compute the indices, `ind_start` `ind_end`, containing the specified percentage of the signal's integrated weight.  IE `p_start` of the
    signal occurs before `ind_start`, `p_end` of the signal occurs before `ind_end`.

    :param data: One dimensional signal data
    :param p_start:  Want position in signal where `p_start` of the total weight has occurred
    :param p_end: Want position in signal where `p_end` of the total weight has occurred

    :return: `ind_start`, `ind_end`, integers specifying the indices of the signal between which `p_end` - `p_start` of the signal occurs
    :group: krembox_utils
    """

    N = len(data)
    Itotal = np.sum(data)

    if Itotal <= 0:
        print("get_signal_bounds: given array contains no data")
        return 0, 0

    Imin = Itotal*p_start
    Imax = Itotal*p_end

    w = 0
    i = 0
    while w < Imin and i < N:
        w += data[i]
        i += 1
    ind_start = i
    while w < Imax and i < N:
        w += data[i]
        i += 1
    ind_end = i-1
    return ind_start, ind_end