#Importing library which we need
import cv2

#Describe the images which will be converted
image = cv2.imread("ates.jpg")

#Guassian Blur
blur = cv2.GaussianBlur(image, (35,35), 1000)
ret, th1 = cv2.threshold(blur, 240, 255, cv2.THRESH_BINARY)
ret, th2 = cv2.threshold(image, 240, 255, cv2.THRESH_BINARY)
cv2.imshow("th", th1)
cv2.imshow("th2", th2)
cv2.imshow("Orginal", image)
cv2.imshow("Blured", blur)
cv2.waitKey(0)
