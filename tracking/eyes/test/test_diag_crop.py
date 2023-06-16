from tracking.eyes.utils import *
import numpy as np
import cv2
from core.dataclasses import Rect

rect = Rect(500,250,300,100)
angle = 35
image = 0.5*np.random.rand(1000,1000) + \
      0.5*cv2.resize(np.random.rand(100,100),None,fx=10,fy=10)
vert = rotate_vertices(rect,angle).T
for pts1,pts2 in zip(vert[:-1,], vert[1:,]):
    image = cv2.line(
        image,
        pts1.astype(np.int32),
        pts2.astype(np.int32),
        1
    )
bb, img_bb, img_rot, img_diag = diagonal_crop(image, rect, angle_deg=angle)
image = cv2.rectangle(image,(bb.left,bb.bottom),(bb.left+bb.width,bb.bottom+bb.height),0,1)
image = cv2.circle(image,(rect.left,rect.bottom),5,0)

for i,img in enumerate([image, img_bb, img_rot, img_diag]):
    cv2.namedWindow(f'{i}')
    cv2.imshow(f'{i}',img)
    cv2.waitKey(0)

cv2.destroyAllWindows()
