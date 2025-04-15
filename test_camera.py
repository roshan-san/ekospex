from picamera2 import Picamera2
import time
from PIL import Image
import os

def test_camera():
    print("Initializing camera test...")
    
    try:
        # Initialize the camera
        camera = Picamera2()
        
        # Configure the camera for Pi Zero W
        config = camera.create_preview_configuration(
            main={"size": (640, 480), "format": "RGB888"},
            buffer_count=2
        )
        camera.configure(config)
        
        print("Starting camera...")
        camera.start()
        
        # Give the camera time to initialize
        time.sleep(2)
        
        print("Capturing test image...")
        # Capture image
        frame = camera.capture_array()
        
        # Convert to PIL Image
        img = Image.fromarray(frame)
        
        # Save the test image
        test_image_path = "test_image.jpg"
        img.save(test_image_path)
        
        print(f"Test image saved as {test_image_path}")
        print(f"Image size: {img.size}")
        
        # Clean up
        camera.stop()
        camera.close()
        
        print("Camera test completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error during camera test: {e}")
        return False

if __name__ == "__main__":
    test_camera() 