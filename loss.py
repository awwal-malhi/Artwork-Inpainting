# -*- coding: utf-8 -*-
"""Loss

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1KIIjLsROH6m3Zdyp0lXO0nbeLlyFEkV-
"""

import torch
import numpy as np
from torch import nn
from torchvision import models

def gram_matrix(feat):
    # https://github.com/pytorch/examples/blob/master/fast_neural_style/neural_style/utils.py
    (b, ch, h, w) = feat.size()
    feat = feat.view(b, ch, h * w)
    feat_t = feat.transpose(1, 2)
    gram = torch.bmm(feat, feat_t) / (ch * h * w)
    return gram


def total_variation_loss(image):
    # shift one pixel and get difference (for both x and y direction)
    loss = torch.mean(torch.abs(image[:, :, :, :-1] - image[:, :, :, 1:])) + \
        torch.mean(torch.abs(image[:, :, :-1, :] - image[:, :, 1:, :]))
    return loss

class FeatureExtractor(nn.Module):
    def __init__(self, extractor='vgg16'):
        super().__init__()
        self.extractor = extractor
        if self.extractor == 'vgg16':
          vgg16 = models.vgg16(pretrained=True)
          self.enc_1 = nn.Sequential(*vgg16.features[:5])
          self.enc_2 = nn.Sequential(*vgg16.features[5:10])
          self.enc_3 = nn.Sequential(*vgg16.features[10:17])
        elif self.extractor == 'resnet':
          res = models.resnet101(pretrained=True)
          self.enc_1 = nn.Sequential(*[res.conv1, res.bn1, res.relu, res.maxpool, *res.layer1])
          self.enc_2 = nn.Sequential(*res.layer2)
          self.enc_3 = nn.Sequential(*res.layer3)
          self.enc_4 = nn.Sequential(*res.layer4)

        # fix the encoder
        for i in range(4 if not (CONFIG['extractor'] == 'vgg16') else 3):
            for param in getattr(self, 'enc_{:d}'.format(i + 1)).parameters():
                param.requires_grad = False

    def forward(self, image):
        results = [image]
        for i in range(4 if not (CONFIG['extractor'] == 'vgg16') else 3):
            func = getattr(self, 'enc_{:d}'.format(i + 1))
            results.append(func(results[-1]))
        return results[1:]

class InpaintingLoss(nn.Module):
    def __init__(self, extractor):
        super().__init__()
        self.l1 = nn.L1Loss()
        self.extractor = extractor

    def forward(self, input, mask, output, gt):
        loss_dict = {}
        output_comp = mask * input + (1 - mask) * output

        loss_dict['hole'] = self.l1((1 - mask) * output, (1 - mask) * gt)
        loss_dict['valid'] = self.l1(mask * output, mask * gt)

        if output.shape[1] == 3:
            feat_output_comp = self.extractor(output_comp)
            feat_output = self.extractor(output)
            feat_gt = self.extractor(gt)
        elif output.shape[1] == 1:
            feat_output_comp = self.extractor(torch.cat([output_comp]*3, 1))
            feat_output = self.extractor(torch.cat([output]*3, 1))
            feat_gt = self.extractor(torch.cat([gt]*3, 1))
        else:
            raise ValueError('only gray an')

        loss_dict['prc'] = 0.0
        for i in range(4 if not (CONFIG['extractor'] == 'vgg16') else 3):
            loss_dict['prc'] += self.l1(feat_output[i], feat_gt[i])
            loss_dict['prc'] += self.l1(feat_output_comp[i], feat_gt[i])

        loss_dict['style'] = 0.0
        for i in range(4 if not (CONFIG['extractor'] == 'vgg16') else 3):
            loss_dict['style'] += self.l1(gram_matrix(feat_output[i]),
                                          gram_matrix(feat_gt[i]))
            loss_dict['style'] += self.l1(gram_matrix(feat_output_comp[i]),
                                          gram_matrix(feat_gt[i]))

        loss_dict['tv'] = total_variation_loss(output_comp)

        return loss_dict