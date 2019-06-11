from matplotlib import pyplot as plt

import numpy as np

# numpy's fft implementation is slow, so use FFTW as a drop-in replacement
import pyfftw.interfaces.numpy_fft as fft

from math import floor

# Load an image
image = plt.imread("einstein1_7.jpg")

# Make image greyscale
image = np.average(image, axis=2)

# Set up geometry
width, height = image.shape

centre_x = floor(width) / 2
centre_y = floor(height) / 2

x_axis = np.arange(width)
y_axis = np.arange(height)

# Create circular filter
filter_radius = 100
filter = np.zeros_like(image)

for i in range(width):
    for j in range(height):
        if (i - centre_x) ** 2 + (j - centre_y) ** 2 > filter_radius ** 2:
            filter[i, j] = 1

# Invert: lowpass filter
filter = 1 - filter

# Move to Fourier plane
FT = fft.fftshift(fft.fft2(image))

# Apply Fourier filter
filtered_FT = FT * filter

# Inverse Fourier transform to image plane
filtered_image = fft.ifft2(fft.ifftshift(filtered_FT))

# Plot results
plt.figure(figsize=[20, 20])

# Original image
plt.subplot(2, 2, 1)
plt.title("Original image")
plt.imshow(image)

# Fourier transform; log scale to bring out detail outside centre
plt.subplot(2, 2, 2)
plt.title("Fourier transform of original image")
plt.imshow(np.log(np.abs(FT) ** 2))

# Filtered fourier transform
plt.subplot(2, 2, 3)
plt.title("Fourier transform restricted to leading modes")
plt.imshow(np.log(np.abs(filtered_FT) ** 2))

# Observed image
plt.subplot(2, 2, 4)
plt.title("Observed image with filter")
plt.imshow(np.abs(filtered_image) ** 2)

plt.savefig("fourier_restricted.pdf")


def salt_pepper(image, r):
    '''Add random light and dark pixels with frequency `r` to `image`,
    returning the result.'''

    r = min(1, r)
    uniform_random = np.random.random(image.shape)

    # Pepper
    noisy_image = np.where(uniform_random < r / 2,
                           np.zeros_like(image),
                           image)

    # Salt
    noisy_image = np.where(uniform_random > 1 - r / 2,
                           np.ones_like(image) * 255,
                           noisy_image)
    return noisy_image


# Add noise to image
noisy_image = salt_pepper(image, 0.1)

# Reuse filter from previous task
lowpass_filter = 1 - filter

# Move to Fourier plane
FT = fft.fftshift(fft.fft2(noisy_image))

# Apply Fourier filter
filtered_FT = FT * lowpass_filter

# Inverse Fourier transform to image plane
filtered_image = fft.ifft2(fft.ifftshift(filtered_FT))

# Plot results
plt.figure(figsize=[15, 15])

# Original image
plt.subplot(2, 2, 1)
plt.title("Image with noise added")

# White noise doesn't show up very well with the default colour map
plt.imshow(noisy_image, cmap='gray')

# Fourier transform; log scale to bring out detail outside centre
plt.subplot(2, 2, 2)
plt.title("Fourier transport of noisy image")
plt.imshow(np.log(np.abs(FT) ** 2))

# Filtered fourier transform
plt.subplot(2, 2, 3)
plt.title("Fourier transform with leading-order modes filtered out")
plt.imshow(np.log(np.abs(filtered_FT) ** 2))

# Observed image
plt.subplot(2, 2, 4)
plt.title("Observed image, noise only")
plt.imshow(np.abs(filtered_image) ** 2 / np.max(abs(filtered_image) ** 2),
           cmap='gray')

plt.savefig("noise_isolation.pdf")

# Move to Fourier plane
FT = fft.fftshift(fft.fft2(image))

# Remove phase information in Fourier plane
phaseless_image = fft.ifft2(fft.ifftshift(abs(FT) ** 2))

# Plot results
plt.figure(figsize=[15, 15])

# Original image
plt.subplot(2, 2, 1)
plt.title("Original image")
plt.imshow(image, cmap='gray')

# Phaseless image
plt.subplot(2, 2, 2)
plt.title("Phaseless image")
plt.imshow(abs(phaseless_image) ** 2)

plt.savefig("phase_contrast.pdf")
