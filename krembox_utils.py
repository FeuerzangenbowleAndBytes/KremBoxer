import numpy as np
import matplotlib.pyplot as plt


def get_signal_bounds(data: np.array, p_start: float, p_end: float):
    N = len(data)
    Itotal = np.sum(data)
    print(Itotal, N)
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


if __name__ == "__main__":
    xs = np.arange(0, 100, 0.1)
    ys = np.fmax(0, np.sin(xs*2*np.pi/75))

    ind_start, ind_end = get_signal_bounds(ys, 0.05, 0.95)

    fig, axs = plt.subplots(1, 1)
    axs.plot(xs, ys)
    axs.axvline(xs[ind_start], color='black', ls='--')
    axs.axvline(xs[ind_end], color='black', ls='--')
    plt.show()
