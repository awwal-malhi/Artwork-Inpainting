# -*- coding: utf-8 -*-
"""Unet

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1qLYY0yg3NZIaWn27Ijitt2-6g6fFm1q4
"""

import torch
from torch import nn
import numpy as np
from double_conv_layer import DoubleConv, DoublePConv
from inception_module import InceptionModule

class Encoder(nn.Module):
  def __init__(self, down_conv_out, down_conv_ks, down_conv_activation, pad, add_inception, verbose):
    super().__init__()
    

    self.down_conv_out = down_conv_out
    self.down_conv_ks = down_conv_ks
    self.down_conv_activation = down_conv_activation
    self.pad = pad 
    self.add_inception = add_inception # add inception module or not
    self.verbose = verbose # False if do not want shape transformations

    # Down Conv Layers
    self.down_conv1 = DoublePConv(3, down_conv_out[0], down_conv_ks[0], down_conv_activation, padding=pad)
    self.down_conv2 = DoublePConv(down_conv_out[0], down_conv_out[1], down_conv_ks[1], down_conv_activation, padding=pad)
    self.down_conv3 = DoublePConv(down_conv_out[1], down_conv_out[2], down_conv_ks[2], down_conv_activation, padding=pad)
    self.down_conv4 = DoublePConv(down_conv_out[2], down_conv_out[3], down_conv_ks[3], down_conv_activation, padding=pad)

    # Inception Modules
    inception_in_1 = down_conv_out[3]
    inception_in_2 = int(CONFIG['inception_out_multiplier'] * inception_in_1)
    inception_in_3 = int(CONFIG['inception_out_multiplier'] * inception_in_2)
    self.inception_module_1 = InceptionModule(inception_in_1)
    self.inception_module_2 = InceptionModule(inception_in_2)
    self.inception_module_3 = InceptionModule(inception_in_3)

    # Maxpooling
    self.maxpool = nn.MaxPool2d(kernel_size=2, stride=2)


  def forward(self, input, mask):

    print_shape(self.verbose, f'Start : {input.shape}')

    x1, m1 = self.down_conv1(input, mask)
    print_shape(self.verbose, f'After Down Conv 1 : {x1.shape}')

    x = self.maxpool(x1)
    m = self.maxpool(m1)
    print_shape(self.verbose, f'After maxpool : {x.shape}')

    x2, m2 = self.down_conv2(x, m)
    print_shape(self.verbose, f'After Down Conv 2 : {x2.shape}')

    x = self.maxpool(x2)
    m = self.maxpool(m2)
    print_shape(self.verbose, f'After maxpool : {x.shape}')

    x3, m3 = self.down_conv3(x, m)
    print_shape(self.verbose, f'After Down Conv 3 : {x3.shape}')

    x = self.maxpool(x3)
    m = self.maxpool(m3)
    print_shape(self.verbose, f'After maxpool : {x.shape}')

    x, m = self.down_conv4(x, m)                 
    print_shape(self.verbose, f'After Down Conv 4 : {x.shape}')

    if self.add_inception:
      x = self.inception_module_1(x)
      print_shape(self.verbose, f'After 1st Inception module : {x.shape}')

      x = self.inception_module_2(x)
      print_shape(self.verbose, f'After 2nd Inception module : {x.shape}')

      x = self.inception_module_3(x)
      print_shape(self.verbose, f'After 3rd Inception module : {x.shape}')
    
    return x, x1, x2, x3


class Decoder(nn.Module):
  def __init__(self, up_conv_out, up_conv_ks, up_conv_activation, pad, add_inception, verbose):
    super().__init__()
  
    self.up_conv_out = up_conv_out
    self.up_conv_ks = up_conv_ks
    self.up_conv_activation = up_conv_activation
    self.pad = pad 
    self.add_inception = add_inception
    self.verbose = verbose # False if do not want shape transformations


    # Conv Transpose layers
    inception_in_1 = CONFIG['down_conv_out'][-1]
    inception_in_2 = int(CONFIG['inception_out_multiplier'] * inception_in_1)
    inception_in_3 = int(CONFIG['inception_out_multiplier'] * inception_in_2)
    transpose1_in_from_inception = int(CONFIG['inception_out_multiplier'] * inception_in_3)
    self.up_transpose1 = nn.ConvTranspose2d(transpose1_in_from_inception, up_conv_out[0], 2, 2) if self.add_inception else nn.ConvTranspose2d(CONFIG['down_conv_out'][-1], up_conv_out[0], 2, 2)
    self.up_transpose2 = nn.ConvTranspose2d(up_conv_out[0], up_conv_out[1], 2, 2)
    self.up_transpose3 = nn.ConvTranspose2d(up_conv_out[1], up_conv_out[2], 2, 2)
    
    # Up Conv Layers
    self.up_conv1 = DoubleConv(CONFIG['down_conv_out'][-1], up_conv_out[0], up_conv_ks[0], up_conv_activation, padding=pad)
    self.up_conv2 = DoubleConv(up_conv_out[0], up_conv_out[1], up_conv_ks[1], up_conv_activation, padding=pad)
    self.up_conv3 = DoubleConv(up_conv_out[1], up_conv_out[2], up_conv_ks[2], up_conv_activation, padding=pad)

    # final output conv
    self.output_conv = nn.Conv2d(up_conv_out[2], 3, 1)


  def forward(self, input, x1, x2, x3):

    x = self.up_transpose1(input) 
    print_shape(self.verbose, f'After Up Transpose 1 : {x.shape}')

    x = self.up_conv1(torch.cat([x, x3], 1)) # skip connection from down_conv3
    print_shape(self.verbose, f'After Up Conv 1 : {x.shape}')

    x = self.up_transpose2(x)
    print_shape(self.verbose, f'After Up Transpose 2 : {x.shape}')

    x = self.up_conv2(torch.cat([x, x2], 1)) # skip connection from down_conv2
    print_shape(self.verbose, f'After Up Conv 2 : {x.shape}')

    x = self.up_transpose3(x)
    print_shape(self.verbose, f'After Up Transpose 3 : {x.shape}')

    x = self.up_conv3(torch.cat([x, x1], 1)) # skip connection from down_conv1
    print_shape(self.verbose, f'After Up Conv 3 : {x.shape}')

    # final output conv layer
    x = self.output_conv(x)
    print_shape(self.verbose, f'After Final output conv : {x.shape}')
    
    
    return x


class PartialConvUNet(nn.Module):
  def __init__(self, 
               down_conv_out=CONFIG['down_conv_out'], 
               down_conv_ks=CONFIG['down_conv_ks'],
               down_conv_activation=CONFIG['down_conv_activation'],
               up_conv_out=CONFIG['up_conv_out'],
               up_conv_ks=CONFIG['up_conv_ks'],
               up_conv_activation=CONFIG['up_conv_activation'],
               pad='same',
               add_inception=CONFIG['add_inception'],
               verbose=CONFIG['verbose']):
    super().__init__()
    

    self.down_conv_out = down_conv_out
    self.down_conv_ks = down_conv_ks
    self.down_conv_activation = down_conv_activation
    self.up_conv_out = up_conv_out
    self.up_conv_ks = up_conv_ks
    self.up_conv_activation = up_conv_activation
    self.pad = pad 
    self.add_inception = add_inception # add inception module or not\
    self.verbose = verbose # False if do not want shape transformations

    # Instantiate the Encoder
    self.encoder = Encoder(down_conv_out=self.down_conv_out, 
                           down_conv_ks=self.down_conv_ks, 
                           down_conv_activation=self.down_conv_activation,
                           pad=self.pad,
                           add_inception=self.add_inception,
                           verbose=self.verbose)
    
    # Instantiate the Decoder
    self.decoder = Decoder(up_conv_out=self.up_conv_out,
                           up_conv_ks=self.up_conv_ks,
                           up_conv_activation=self.up_conv_activation,
                           pad=self.pad,
                           add_inception=self.add_inception,
                           verbose=self.verbose)


  def forward(self, input, mask):
    
    x, x1, x2, x3 = self.encoder(input, mask)

    x = self.decoder(x, x1, x2, x3)
    
    return x