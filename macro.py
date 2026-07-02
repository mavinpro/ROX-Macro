import pyautogui
import time
import random
import pytesseract
import cv2
import numpy as np
import re  

# IMPORTANT: Tell Python where you installed Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def find_and_click(image_path, confidence_level=0.8):
    """Searches for an image and clicks it with a random offset."""
    print(f"Searching for {image_path} to click...")
    try:
        location = pyautogui.locateOnScreen(image_path, confidence=confidence_level)
        center_x, center_y = pyautogui.center(location)
        
        # Note: If your numpad buttons are small, you might want to change 15 to 10
        offset_x = random.randint(-7, 7)
        offset_y = random.randint(-7, 7)
        
        randomized_x = center_x + offset_x
        randomized_y = center_y + offset_y
        
        pyautogui.click(randomized_x, randomized_y)
       
        print(f"Successfully clicked {image_path} at (X: {randomized_x}, Y: {randomized_y})")
        return True
    except pyautogui.ImageNotFoundException:
        print(f"Could not find {image_path}.")
        return False

def get_image_location(image_path, confidence_level=0.8):
    """Returns the exact location box of the image, or None if not found."""
    try:
        return pyautogui.locateOnScreen(image_path, confidence=confidence_level)
    except pyautogui.ImageNotFoundException:
        return None

def read_screen_text(region=None):
    """Takes a screenshot, isolates pure white text, and extracts it as math."""
    screenshot = pyautogui.screenshot(region=region)
    img_np = np.array(screenshot)
    
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
    
    # RAISED THRESHOLD: 240 will drop the gray background and keep only the pure white numbers
    _, binary = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
    
    processed_img = cv2.bitwise_not(binary)
    cv2.imwrite("debug_crop.png", processed_img)
    
    # Tell Tesseract to only expect numbers and math symbols on a single line (PSM 7)
    custom_config = r'--psm 7 -c tessedit_char_whitelist=0123456789+-*xX='
    
    detected_text = pytesseract.image_to_string(processed_img, config=custom_config)
    return detected_text.strip()

def solve_math(text):
    """Safely evaluates a math string and returns the integer result."""
    # If text is exactly 2 digits, make it "first - second"
    if len(text) == 2 and text.isdigit():
        text = text[0] + '-' + text[1]
    
    # Check if the middle character is "4" in the original text
    if len(text) == 3 and text[1] == '4':
        text = text[0] + '+' + text[2]
    
    # Strip out any random garbage characters that aren't math
    clean_text = re.sub(r'[^0-9+\-*xX/]', '', text)
    # Replace the letter x with the multiply symbol just in case
    clean_text = clean_text.replace('x', '*').replace('X', '*')
    
    if not clean_text:
        return None
    
    try:
        result = int(eval(clean_text))
        return result
    except Exception as e:
        print(f"Could not calculate math from: '{text}'. Error: {e}")
        return None

def click_numpad(answer):
    """Clicks the corresponding numpad images, the 'v', and finally the confirm button."""
    answer_str = str(answer)
    print(f"Typing out answer: {answer_str}")
    
    print("Clicking answer")
    time.sleep(random.uniform(0.2, 0.5))
    find_and_click("answer.png", confidence_level=0.85)
    
    # 1. Click each digit
    if answer != 11:
        for digit in answer_str:
            image_path = f"numpad/{digit}.png" 
            success = find_and_click(image_path, confidence_level=0.98) 
            
            if not success:
                print(f"Failed to find {image_path}. Aborting this attempt.")
                return False
                
            time.sleep(random.uniform(0.3, 0.6))
    else:
        for digit in answer_str:
            image_path = f"numpad/{digit}.png" 
            success = find_and_click(image_path, confidence_level=0.98) 
            pyautogui.moveTo(100, 100)
            if not success:
                print(f"Failed to find {image_path}. Aborting this attempt.")
                return False
                
            time.sleep(random.uniform(0.3, 0.6))
        
    # 2. Click the green checkmark on the numpad
    print("Clicking numpad checkmark (v.png)...")
    time.sleep(random.uniform(0.2, 0.5))
    find_and_click("numpad/v.png", confidence_level=0.85)
    
    # 3. Click the final confirm button
    print("Clicking final confirm button (confirm.png)...")
    time.sleep(random.uniform(0.3, 0.6))  # Short pause before final confirmation
    find_and_click("confirm.png", confidence_level=0.8)
    
    return True

# --- MAIN MACRO LOOP ---
print("Starting in 3 seconds... Switch to your target window now!")
time.sleep(3)

try:
    while True:
        pending_box = get_image_location('pending.png', confidence_level=0.8)
        
        if pending_box:
            print("Pending image detected! Checking for math captcha...")
            
            center_x, center_y = pyautogui.center(pending_box)
            read_width = 200
            read_height = 50
            
            read_x = int(center_x - (read_width / 2))
            read_x = max(0, read_x) 
            read_y = int(pending_box.top + pending_box.height - 10)
            
            target_region = (read_x, read_y, read_width, read_height)
            
            # Read the math problem
            found_text = read_screen_text(region=target_region)
            
            if found_text:
                print("==============================")
                print(f"CAPTCHA DETECTED: {found_text}")
                
                # Calculate the answer
                answer = solve_math(found_text)
                
                if answer is not None:
                    print(f"CALCULATED ANSWER: {answer}")
                    print("==============================")
                    
                    # Wait 1 second for the numpad UI to fully load in the game
                    time.sleep(0.5)
                    
                    # Click the digits, the checkmark, and the confirm button
                    click_numpad(answer)
                    
                    # Wait a few seconds for the captcha to clear before resuming
                    print("Waiting for captcha UI to close...")
                    time.sleep(1)
                else:
                    print("Could not evaluate the text as math.")
                    print("==============================")
            else:
                print("Looked below the image, but no readable text was found.")
                
            time.sleep(1)
            continue 
            
        # Normal gardening loop
        find_and_click('target.png', confidence_level=0.8)
        time.sleep(0.7) 
        
except KeyboardInterrupt:
    print("\nMacro stopped by user.")