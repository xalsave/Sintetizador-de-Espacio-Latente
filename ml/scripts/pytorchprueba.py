import numpy as np
import torch

waves    = np.load(r"M:\Users\alsav_9f696wk\Desktop\TFG\ml\dataset\akwf_processed.npy")
families = np.load(r"M:\Users\alsav_9f696wk\Desktop\TFG\ml\dataset\akwf_families.npy")

tensor = torch.from_numpy(waves).to("cuda")
print(tensor.shape)
print(tensor.dtype)
print(tensor.device)