# -*- coding: utf-8 -*-
"""Training loop

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1YX1oHdVOClHreY487_rbv5BfLl99Pegv
"""

import os
import gc
import PIL
import math
import tqdm
import torch
import random
import shutil
import numpy as np
import pandas as pd
from tqdm import tqdm
import torch.nn.functional as F
import matplotlib.pyplot as plt
from unet import PartialConvUnet
from loss import FeatureExtractor, InpaintingLoss
from dataset_generation import make_dataset_dirs
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from training_func import get_masked_inputs, train_one_epoch, val_one_epoch, test_samples


# Unified Configuration Dictionary to change all the configurations in the code

CONFIG = {'model_type':'Partial_conv_Inception_Inpainting_loss_1.6',
          'epochs':1,
          'lr':1e-4,
          'weight_decay':1e-5,
          'batch_size_train':32,
          'batch_size_eval':64,
          'kl_weights':0.02,
          'inception_out_multiplier':1.6, #times input channels count to get output channel count as inception module output
          'hole_coef':6,
          'valid_coef':1,
          'prc_coef':0,
          'style_coef':0,
          'tv_coef':0,
          'down_conv_out' : [64, 128, 256, 512], 
          'down_conv_ks':[3, 3, 3, 3],
          'down_conv_activation':nn.ReLU,
          'up_conv_out':[256, 128, 64],
          'up_conv_ks':[3, 3, 3],
          'up_conv_activation':nn.ReLU,
          'extractor':'vgg16',
          'add_inception':False,
          'verbose':False,
          'device':"cuda" if torch.cuda.is_available() else 'cpu'}

# seed everything for reproducibility 
def seed_everything(seed=42):
  random.seed(seed)
  os.environ['PYTHONHASHSEED'] = str(seed)
  np.random.seed(seed)
  torch.manual_seed(seed)
  torch.backends.cudnn.deterministic = True
  torch.backends.cudnn.benchmark = False

seed_everything()



# make training, testing and validation dataset
train_images, test_images = train_test_split(os.listdir('/content/processed_dataset'), test_size=0.02, random_state=1)
train_images, val_images = train_test_split(train_images, test_size=0.07, random_state=1)

original_dir = '/content/processed_dataset'
base_dir = 'artwork_dataset'
sub_dirs = ['train', 'validation', 'test']
image_name_lists = [train_images, val_images, test_images]

make_dataset_dirs(base_dir, original_dir, sub_dirs, image_name_lists)



# Training Loop
torch.cuda.empty_cache()
extractor = FeatureExtractor(extractor=CONFIG['extractor']).to(CONFIG['device'])
model = PartialConvUNet().to(device=CONFIG['device'])
criterion = InpaintingLoss(extractor)
optimizer = torch.optim.AdamW(model.parameters(), lr=CONFIG['lr'], weight_decay=CONFIG['weight_decay'])

train_loss_list = []
val_loss_list = []


for epoch in range(CONFIG['epochs']):
  train_hole, train_valid, train_prc, train_style, train_tv = train_one_epoch(model, train_dataloader, epoch, CONFIG['masks'], optimizer, criterion)
  
  val_hole, val_valid, val_prc, val_style, val_tv = val_one_epoch(model, val_dataloader, epoch, CONFIG['masks'], criterion)

  train_loss_list.append((train_hole, train_valid, train_prc, train_style, train_tv))
  val_loss_list.append((val_hole, val_valid, val_prc, val_style, val_tv))

  torch.save(model.state_dict(), f'{CONFIG["model_type"]}_epoch_{epoch}_batch_size_{CONFIG["batch_size_train"]}.pth')