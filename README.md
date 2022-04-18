# Artwork Inpainting for Artwork Restoration

Create a useful tool for artworks, for restoration purpose or digital presentation purpose 
in museums/art galleries. This model initially trained on over 
100,000 artwork images but is also designed to be easily trainable
without requiring expensive computation settings and time. 
Therefore, art restorators can re-train the model on specific
datasets to gain better predictions on specific types of 
artworks. 

## Model architecture

To achieve the final results a modified UNet based 
convolutional autoencoder architecture was used
where partial convolutions were used instead of normal convolution layers
in the encoder. A stack of 3 Inception modules was used at the 
end of the encoder to enhance and enrich the encodings form
the encoder. Addition of these features showed significant improvement
over the base UNet architecture.

![Model infographic](https://github.com/awwal-malhi/Artwork-Inpainting/blob/main/architecture.png)

## Screenshots

The screenshot below is from the testing dataset.
![Result on test set](https://github.com/awwal-malhi/Artwork-Inpainting/blob/main/Results/result1.png)

The screenshot below is from images web scrapped from internet belonging to people artwork images.
![Result on images of people drawing from web](https://github.com/awwal-malhi/Artwork-Inpainting/blob/main/Results/result2.png)
