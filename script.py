import os
import sys
import cv2
import numpy as np


def add_label(img, text, font_scale=1.0, thickness=2, margin=8):
	color = (255, 255, 255)
	outline = (0, 0, 0)
	org = (margin, 30)
	cv2.putText(img, text, org, cv2.FONT_HERSHEY_SIMPLEX, font_scale, outline, thickness + 2, cv2.LINE_AA)
	cv2.putText(img, text, org, cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness, cv2.LINE_AA)


def ensure_bgr(img):
	"""Return a 3-channel BGR image. If input is single-channel, convert to BGR."""
	if img is None:
		return None
	if len(img.shape) == 2:
		return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
	return img


def main(input_filename="ates.jpg", out_filename="process_output.png", output_scale=1.5, show_gui=True):
	# startup info removed per user request (no printed library explanations)

	if not os.path.isfile(input_filename):
		print(f"Error: input file '{input_filename}' not found in {os.getcwd()}")
		sys.exit(1)

	image = cv2.imread(input_filename)
	if image is None:
		print(f"Error: failed to read image '{input_filename}'")
		sys.exit(1)

	# Blurred (color) for display and blurred grayscale for thresholding
	blur_color = cv2.GaussianBlur(image, (35, 35), 0)
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	gray_blur = cv2.GaussianBlur(gray, (35, 35), 0)

	# Thresholds (use gray inputs). If you want Otsu, change thresh value to 0 and add +cv2.THRESH_OTSU
	th_blur = cv2.threshold(gray_blur, 220, 255, cv2.THRESH_BINARY)[1]

	# Prepare images for side-by-side display: all must be BGR and same size
	h, w = image.shape[:2]
	display_orig = ensure_bgr(image.copy())
	display_blur = ensure_bgr(blur_color.copy())
	display_th = ensure_bgr(th_blur.copy())

	# --- Fire detection on the threshold result (th_blur) ---
	# Clean small noise with a morphological open, then count bright pixels
	kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
	mask = cv2.morphologyEx(th_blur, cv2.MORPH_OPEN, kernel)
	white_count = int(cv2.countNonZero(mask))
	total_pixels = mask.shape[0] * mask.shape[1]
	white_ratio = white_count / total_pixels

	# Heuristic: if more than threshold_ratio of pixels are bright, flag as fire
	# You can tune detection_threshold to be more/less sensitive
	detection_threshold = 0.005  # 0.5% of image area by default
	is_fire = white_ratio >= detection_threshold

	# Find contours (blobs) of bright areas to optionally draw boxes
	contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
	min_blob_area = 200  # ignore tiny blobs
	boxes = []
	for cnt in contours:
		area = cv2.contourArea(cnt)
		if area >= min_blob_area:
			x, y, bw, bh = cv2.boundingRect(cnt)
			boxes.append((x, y, bw, bh))

	# Do not draw boxes on the original image (user requested). We'll draw on the fire panel instead.

	# Also visualize the cleaned mask in the threshold display (convert to BGR)
	display_th = ensure_bgr(mask)

	# Create a fire-visualization panel: overlay mask in red on the original
	colored_mask = np.zeros_like(display_orig)
	colored_mask[mask == 255] = (0, 0, 255)  # red overlay for fire regions (BGR)
	display_fire = cv2.addWeighted(display_orig, 0.7, colored_mask, 0.3, 0)

	# Draw detection boxes and label on the fire panel only
	for (x, y, bw, bh) in boxes:
		cv2.rectangle(display_fire, (x, y), (x + bw, y + bh), (0, 0, 255), 2)
		cv2.putText(display_fire, "FIRE", (x, max(y - 6, 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2, cv2.LINE_AA)

	# Print a short summary to console
	print(f"[Detection] bright pixels: {white_count} / {total_pixels} ({white_ratio:.4%}), fire={is_fire}")

	# Optionally resize if images are too large for display (keep reasonable width)
	max_width = 1600
	scale = 1.0
	if 4 * w > max_width:
		scale = max_width / (4 * w)
		new_w = int(w * scale)
		new_h = int(h * scale)
		display_orig = cv2.resize(display_orig, (new_w, new_h), interpolation=cv2.INTER_AREA)
		display_blur = cv2.resize(display_blur, (new_w, new_h), interpolation=cv2.INTER_AREA)
		display_th = cv2.resize(display_th, (new_w, new_h), interpolation=cv2.INTER_AREA)
		display_fire = cv2.resize(display_fire, (new_w, new_h), interpolation=cv2.INTER_AREA)

	# Add labels
	add_label(display_orig, "Original")
	add_label(display_blur, "Blurred")
	add_label(display_th, "Threshold")
	add_label(display_fire, "Detected Fire")

	# Concatenate horizontally: Original | Blurred | Threshold | Fire
	combined = np.hstack([display_orig, display_blur, display_th, display_fire])

	# Show the combined image in a single window unless disabled
	if show_gui:
		cv2.namedWindow("Process: Original | Blurred | Threshold | Fire", cv2.WINDOW_NORMAL)
		cv2.imshow("Process: Original | Blurred | Threshold | Fire", combined)
		print("Press any key in the image window to exit.")
		cv2.waitKey(0)
		cv2.destroyAllWindows()


if __name__ == "__main__":
	main()

