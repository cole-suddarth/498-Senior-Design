import numpy as np
import sys
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.signal import convolve2d
import spectral as spy

fileName = sys.argv[1]

contents = np.load(fileName)

updated_single_frame = contents.squeeze()

#print(updated_single_frame[79])

def gaussian(x, amplitude, mean, stddev):
    if stddev == 0:
        return [0]*728
    return amplitude * np.exp(-((x - mean) / stddev) ** 2 / 2)

# Function to create 2D Gaussian PSF
def create_gaussian_psf(size, sigma):
    x = np.linspace(-size // 2, size // 2, size)
    y = np.linspace(-size // 2, size // 2, size)
    x, y = np.meshgrid(x, y)
    psf = np.exp(-(x**2 + y**2) / (2 * sigma**2))
    return psf / np.sum(psf)

def compute_fwhm(x, y):
    half_max = max(y) / 2.0
    d = np.where(y >= half_max)[0]
    return x[d[-1]] - x[d[0]]

# adjust both of these to the accurate levels
psf_size = 1
psf_sigma = 1

# Convolve PSF with each row of the array
#psf_array = np.zeros_like(array)
for i in range(250, 255):#)updated_single_frame.shape[0]):
    '''psf_array[i] = convolve2d(updated_single_frame[i], psf, mode='same', boundary='wrap')

# Plot original row and PSF-convolved row
row_index = 0  # Choose which row to visualize
plt.plot(psf_array[row_index], label='PSF Convolved Row')
plt.xlabel('Index')
plt.ylabel('Value')
plt.title('Point Spread Function Convolution')
plt.legend()
plt.show()
    '''
    #print(f'row {i+1} on 1 index: {updated_single_frame[i]}')
    # Get data for the current row
    x_data = np.arange(updated_single_frame.shape[1])
    y_data = updated_single_frame[i]
    # Fit Gaussian curve to the data
    popt, _ = curve_fit(gaussian, x_data, y_data, p0=[np.max(y_data), np.argmax(y_data), np.std(y_data)])    # Plot Gaussian curve
    plt.plot(x_data, y_data, '-', label=f'Row {i+1}')
    #fwhm = compute_fwhm(x_data, gaussian(x_data, *popt))
    #print(f'FWHM for Row {i+1}: {fwhm:.2f}')
    #plt.plot(x_data, gaussian(x_data, *popt), '--'), label=f"Gaussian Fit {i+1}")


plt.xlabel('Detector X')
plt.ylabel('Value')
plt.axis([000, 700, 0, 200])
plt.title('HeNe-Laser Gaussian Fit')
#plt.axis([550, 570, 0, 200])
#plt.title('Neon Source Gaussian Fit')
plt.legend(loc='upper left')
plt.show()

'''
# Define the ranges for the third axis
ranges = [(0, 182), (182, 388), (388, 560), (560, 728)]
# Initialize a list to store the averaged arrays
averaged_arrays = []
# Loop over the ranges
for start, end in ranges:
    # Extract the subarray for the current range
    subarray = contents[:, :, start:end]
    # Take the average over the third dimension
    averaged_subarray = np.mean(subarray, axis=2)
    # Append the averaged subarray to the list
    averaged_arrays.append(averaged_subarray)
# Stack the averaged arrays along the third dimension
result = np.stack(averaged_arrays, axis=2)

#view = spy.imshow(result, (2,1,0))
# Flip the y-axis
plt.gca().invert_yaxis()
plt.show()
#view = spy.imshow(result, (2,1,0), aspect="auto")
# Flip the y-axis
plt.gca().invert_yaxis()
plt.show()
#view = spy.imshow(result[:,:,0], cmap= "Blues")
plt.gca().invert_yaxis()
plt.show()
#view = spy.imshow(result[:,:,0], cmap= "Blues", aspect="auto")
plt.gca().invert_yaxis()
plt.show()
#view = spy.imshow(result[:,:,1], cmap= "Greens")
plt.gca().invert_yaxis()
plt.show()
view = spy.imshow(result[:,:,1], cmap= "Greens", aspect="auto")
plt.gca().invert_yaxis()
plt.show()
view = spy.imshow(result[:,:,2], cmap= "Reds")
plt.gca().invert_yaxis()
plt.show()
view = spy.imshow(result[:,:,2], cmap= "Reds", aspect = "auto")
plt.gca().invert_yaxis()
plt.show()
view = spy.imshow(result[:,:,3], cmap= "Reds")
plt.gca().invert_yaxis()
plt.show()
view = spy.imshow(result[:,:,3], cmap= "Reds", aspect="auto")
plt.gca().invert_yaxis()
plt.show()

m, c = spy.kmeans(contents, nclusters= 10, max_iterations=100)
# Display the original image with the classification overlay
spy.imshow(classes=m)
plt.show()
plt.figure()
for i in range(c.shape[0]):
    plt.plot(c[i])

plt.grid()'''