# -*- coding: utf-8 -*-
"""training funcs

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1rEM9RG8-nU7IgPVJWPOPDfsIgc72KCQJ
"""

import gc
import torch
import numpy as np

def get_masked_inputs(targets, masks):
  '''
  This function outputs the masked inputs.

  targets : original images which have not been masked
  masks : buffer of masks out of which masks will be samples to mask the original image to create the input masked image
  '''
  i = [random.choice(range(len(targets))) for i in range(len(targets))]
  masks = torch.stack(masks)[i]
  masks = torch.permute(masks, (0, 3, 1, 2))
  # get masked_inputs
  masked_inputs = torch.tensor(torch.where(masks, targets, 1.0), requires_grad=True)

  return masked_inputs, torch.where(masks, 1, 0)

def train_one_epoch(model, dataloader, epoch, masks_buffer, optimizer, criterion):
  model.train()

  total_loss = 0
  total_loss_hole = 0
  total_loss_valid = 0
  total_loss_prc = 0
  total_loss_style = 0
  total_loss_tv = 0
  batches_iterated = 0
  hole_loss_list = []
  bar = tqdm.tqdm(enumerate(dataloader), total=len(dataloader))

  for step, batch in bar:
    targets = batch[0].to(float)
    inputs, masks = get_masked_inputs(targets, masks_buffer)
    masks = masks.to(device=CONFIG['device'], dtype=torch.float)
    inputs = inputs.to(device=CONFIG['device'], dtype=torch.float)
    targets = torch.tensor(targets, requires_grad=True).to(device=CONFIG['device'], dtype=torch.float)
    
    preds = model(inputs, masks)
    loss_dict = criterion(inputs, masks, preds, targets)
    loss_hole = CONFIG['hole_coef'] * loss_dict['hole']
    loss_valid = CONFIG['valid_coef'] * loss_dict['valid']
    loss_prc = CONFIG['prc_coef'] * loss_dict['prc']
    loss_style = CONFIG['style_coef'] * loss_dict['style']
    loss_tv = CONFIG['tv_coef'] * loss_dict['tv']
    loss = loss_hole+loss_valid+loss_prc+loss_style+loss_tv
      
    
    # backpropogate the loss
    loss.backward()

    # update the gradients
    optimizer.step()
    optimizer.zero_grad() # make the gradients for every param 0

    total_loss_hole += loss_hole.detach()
    total_loss_valid += loss_valid.detach()
    total_loss_prc += loss_prc.detach()
    total_loss_style += loss_style.detach()
    total_loss_tv += loss_tv.detach()
    batches_iterated += 1
    epoch_loss_hole = total_loss_hole / batches_iterated
    epoch_loss_valid = total_loss_valid / batches_iterated
    epoch_loss_prc = total_loss_prc / batches_iterated
    epoch_loss_style = total_loss_style / batches_iterated
    epoch_loss_tv = total_loss_tv / batches_iterated

    bar.set_postfix(Epoch=epoch+1, Train_hole=epoch_loss_hole.item(), Train_valid=epoch_loss_valid.item(), Train_prc=epoch_loss_prc.item(),
                    Train_style=epoch_loss_style.item(), Train_tv=epoch_loss_tv.item())

    gc.collect()
    torch.cuda.empty_cache()

    hole_loss_list.append(epoch_loss_hole)
    
  return hole_loss_list

@torch.no_grad()
def val_one_epoch(model, dataloader, epoch, masks_buffer, criterion):
  model.eval()
  
  total_loss = 0
  total_loss_hole = 0
  total_loss_valid = 0
  total_loss_prc = 0
  total_loss_style = 0
  total_loss_tv = 0
  batches_iterated = 0
  hole_loss_list = []
  bar = tqdm.tqdm(enumerate(dataloader), total=len(dataloader))

  for step, batch in bar:
    targets = batch[0].to(float)
    inputs, masks = get_masked_inputs(targets, masks_buffer)
    masks = masks.to(device=CONFIG['device'], dtype=torch.float)
    inputs = inputs.to(device=CONFIG['device'], dtype=torch.float)
    targets = targets.to(device=CONFIG['device'], dtype=torch.float)

    preds = model(inputs, masks)
    loss_dict = criterion(inputs, masks, preds, targets)
    loss_hole = loss_dict['hole']
    loss_valid = loss_dict['valid']
    loss_prc = loss_dict['prc']
    loss_style = loss_dict['style']
    loss_tv = loss_dict['tv']
    loss = loss_hole+loss_valid+loss_prc+loss_style+loss_tv

    total_loss_hole += loss_hole.detach()
    total_loss_valid += loss_valid.detach()
    total_loss_prc += loss_prc.detach()
    total_loss_style += loss_style.detach()
    total_loss_tv += loss_tv.detach()
    batches_iterated += 1
    epoch_loss_hole = total_loss_hole / batches_iterated
    epoch_loss_valid = total_loss_valid / batches_iterated
    epoch_loss_prc = total_loss_prc / batches_iterated
    epoch_loss_style = total_loss_style / batches_iterated
    epoch_loss_tv = total_loss_tv / batches_iterated

    hole_loss_list.append(epoch_loss_hole)

    bar.set_postfix(Epoch=epoch+1, Val_hole=epoch_loss_hole.item(), Val_valid=epoch_loss_valid.item(), Val_prc=epoch_loss_prc.item(),
                    Val_style=epoch_loss_style.item(), Val_tv=epoch_loss_tv.item())

    gc.collect()
    torch.cuda.empty_cache()


  return hole_loss_list

@torch.no_grad()
def test_samples(model, samples, masks_buffer):
  model.eval()

  targets = samples.to(float)
  inputs, masks = get_masked_inputs(targets, masks_buffer)
  masks = masks.to(device=CONFIG['device'], dtype=torch.float)
  inputs = inputs.to(device=CONFIG['device'], dtype=torch.float)
  targets = targets.to(device=CONFIG['device'], dtype=torch.float)
  
  preds = model(inputs, masks)

  gc.collect()
  torch.cuda.empty_cache()


  return inputs, preds, targets, masks