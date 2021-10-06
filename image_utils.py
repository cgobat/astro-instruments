import numpy as np

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

def not_blank(arr):
    rows, cols = arr.shape[0], arr.shape[1]
    indexer = np.zeros(shape=(rows,cols))
    for i in range(rows):
        for j in range(cols):
            if np.any(arr[i,j]!=0):
                indexer[i,j] = True
            else:
                indexer[i,j] = False
    return indexer.astype(int)
    
def crop_array(arr):
    valid = not_blank(arr)
    top_left = np.argwhere(valid).min(axis=0)
    bottom_right = np.argwhere(valid).max(axis=0)
    
    return arr[top_left[0]:bottom_right[0]+1, # plus 1 because slice isn't
               top_left[1]:bottom_right[1]+1] # inclusive

def center_slice(arr):
    nrows,ncols = arr.shape[0], arr.shape[1]

    even = (nrows//2 == nrows/2)
    if even:
        i1 = nrows//2
        i2 = i1+1
        slice = (arr[i1,:]+arr[i2,:])/2 # average the two middle rows
    else:
        i = nrows//2 + 1
        slice = arr[i,:]

    return slice

def img_fold(arr):
    width = arr.shape[1]
    return np.mean(arr,axis=0).reshape(1,width,3)