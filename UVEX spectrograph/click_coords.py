import numpy as np
import matplotlib.pyplot as plt
import easygui
from skimage import color, io, transform
from image_utils import crop_array, center_slice

def onclick(event):
    ix, iy = event.xdata, event.ydata
    #print(f'x = {ix}, y = {iy}')

    global CLICKS
    CLICKS.append((iy, ix))

    if len(CLICKS) == 2:
        fig.canvas.mpl_disconnect(cid)
        plt.close()

def pixel_coords_on_line(x0, y0, x1, y1):

    x=[]
    y=[]
    dx = x1-x0
    dy = y1-y0
    steep = abs(dx) < abs(dy)

    if steep:
        x0,y0 = y0,x0
        x1,y1 = y1,x1
        dy,dx = dx,dy

    if x0 > x1:
        x0,x1 = x1,x0
        y0,y1 = y1,y0

    gradient = float(dy) / float(dx)  # slope

    """ handle first endpoint """
    xstart = round(x0)
    ystart = y0 + gradient * (xstart - x0)
    xpxl0 = int(xstart)
    ypxl0 = int(ystart)
    x.append(xpxl0)
    y.append(ypxl0) 
    x.append(xpxl0)
    y.append(ypxl0+1)
    intery = ystart + gradient

    """ handles the second point """
    xend = round (x1)
    yend =  gradient * (xend - x1) + y1
    xpxl1 = int(xend)
    ypxl1 = int (yend)

    """ main loop """
    for px in range(xpxl0 + 1 , xpxl1):
        x.append(px)
        y.append(int(intery))
        x.append(px)
        y.append(int(intery) + 1)
        intery += gradient

    x.append(xpxl1)
    y.append(ypxl1) 
    x.append(xpxl1)
    y.append(ypxl1 + 1)

    if steep:
        y,x = x,y

    return list(zip(x,y)), gradient

image_path = easygui.fileopenbox(msg="Select an image.")
image = io.imread(image_path).copy()

CLICKS = []

fig,ax = plt.subplots()
ax.set(xticks=[],yticks=[])

ax.imshow(image)

cid = fig.canvas.mpl_connect('button_press_event', onclick)

plt.show()

print(CLICKS)
x0,y0 = CLICKS[0]
x1,y1 = CLICKS[1]
xmin = int(min(x0,x1))
xmax = int(max(x0,x1))
ymin = int(min(y0,y1))
ymax = int(max(y0,y1))
pxls,slope = pixel_coords_on_line(x0, y0, x1, y1)
theta = np.rad2deg(np.arctan(slope))

A = np.zeros_like(image)
#A += 255
for xy in pxls:
    A[xy] = image[xy]

selection = A[xmin:xmax+1, ymin:ymax+1].copy()

rot = transform.rotate(selection, theta)

smear = crop_array(rot)
plt.imshow(smear)
plt.gca().set(xticks=[],yticks=[])
plt.show()