# import argparse
# import torch.nn as nn
# import torch.nn.functional as F
# import torch.optim as optim
# from torch.optim.lr_scheduler import StepLR

# import os
# from PIL import Image
# from copy import deepcopy
# from tqdm import tqdm
# import time

from data.domain import *
import torch
import numpy as np
np.set_printoptions(precision=2, suppress=True)
DEVICE = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

ROOT_DIR = './data/'
IMG_DIR = ROOT_DIR + 'symbol_images/'
IMG_SIZE = 45

from torchvision import transforms
IMG_TRANSFORM = transforms.Compose([
                    transforms.ToTensor(),
                    transforms.Normalize((0.5,), (1,))])

def compute_rewards(preds, res, seq_len):
    expr_preds, res_preds = eval_expr(preds, seq_len)
    rewards = equal_res(res_preds, res)
    rewards = [1.0 if x else 0. for x in rewards]
    return np.array(rewards)