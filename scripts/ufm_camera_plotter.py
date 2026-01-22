import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

raw_cam_datafile = Path("/home/jepaki/Projects/Objects/AthensExperiments_0624/FireBehaviorDatasets/Raw/UFM/UFM_14_2024-06-20T12-58-27+00-00_ir_images.npy")

raw_cam_data = np.load(raw_cam_datafile)

center_mean = np.mean(raw_cam_data[:, 12, 16])

print(raw_cam_data.shape, center_mean)

fig, axs = plt.subplots(1, 1, figsize=(5, 5))
axs.plot(raw_cam_data[:, 12, 16])
plt.show()

plots_dir = raw_cam_datafile.parent.joinpath(raw_cam_datafile.stem)
plots_dir.mkdir(exist_ok=True)
print(plots_dir)

num_images = raw_cam_data.shape[0]
pngs = []
for i in range(0, num_images, 1):
    print(i)
    fig, axs = plt.subplots(1, 1, figsize=(5, 5))
    axs.imshow(raw_cam_data[i, :, :], vmin=0, vmax=5000)
    plt.tight_layout()
    plot_file = plots_dir.joinpath(f'cam_{i}.png')
    plt.savefig(plot_file)
    pngs.append(plot_file)
    plt.close()
