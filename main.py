import cv2
import numpy as np
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics.texture import Texture
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.widget import Widget

from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Rectangle
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import Screen

class MenuScreen(Screen):
    def __init__(self, **kwargs):
        super(MenuScreen, self).__init__(**kwargs)
        
        # Set background color to white
        with self.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(1, 1, 1, 1)  # White background
            self.rect = Rectangle(size=Window.size, pos=(0, 0))

        # Create a FloatLayout for flexible positioning
        layout = FloatLayout()

        # Add the logo on the top-center
        logo = Image(source='/home/dolphino/Downloads/ONSR.jpeg', size_hint=(None, None), size=(150, 150))
        logo.pos = (Window.width / 2 - logo.width / 2, Window.height - logo.height - 20)  # Top-center position
        layout.add_widget(logo)

        # Create buttons with smaller size
        button_layout = BoxLayout(orientation="vertical", spacing=10, size_hint=(None, None), size=(Window.width * 0.6, Window.height * 0.5))
        
        # Buttons to access camera screen with different filters
        self.blur_button = Button(text="Apranax (Flou)", size_hint=(1, 0.3), size=(200, 50))
        self.double_vision_button = Button(text="Vérapamil (Double Vision)", size_hint=(1, 0.3), size=(200, 50))
        self.delayed_vision_button = Button(text="Dompéridone (Vision Retardée)", size_hint=(1, 0.3), size=(200, 50))

        # Bind buttons to change filter type
        self.blur_button.bind(on_press=self.change_to_camera_screen)
        self.double_vision_button.bind(on_press=self.change_to_camera_screen)
        self.delayed_vision_button.bind(on_press=self.change_to_camera_screen)

        button_layout.add_widget(self.blur_button)
        button_layout.add_widget(self.double_vision_button)
        button_layout.add_widget(self.delayed_vision_button)

        # Center the button layout on the screen
        button_layout.pos = (Window.width / 2 - button_layout.width / 2, Window.height / 2 - button_layout.height / 2)

        # Add the button layout to the main layout
        layout.add_widget(button_layout)

        # Add the layout to the screen
        self.add_widget(layout)

    def change_to_camera_screen(self, instance):
        # Change to camera screen and set the appropriate filter
        app = App.get_running_app()
        filter_name = instance.text.lower().replace(" vision", "")
        app.set_filter(filter_name)
        app.root.current = "camera"


class CameraScreen(Screen):
    def __init__(self, **kwargs):
        super(CameraScreen, self).__init__(**kwargs)
        self.img = Image()
        layout = BoxLayout(orientation="vertical")
        
        # Make the camera display bigger
        self.img.size_hint = (1, 0.8)

        layout.add_widget(self.img)

        # OpenCV VideoCapture with the back camera (usually index 1 for back camera)
        self.capture = cv2.VideoCapture(1)
        self.current_filter = None
        self.previous_frames = []

        # Schedule camera updates at 30 FPS
        Clock.schedule_interval(self.update_frame, 1.0 / 30)  # 30 FPS

        self.add_widget(layout)

    def update_frame(self, dt):  # Include 'dt' to match Clock callback signature
        ret, frame = self.capture.read()
        if ret:
            # Apply selected filter
            if self.current_filter == "blur":
                frame = cv2.GaussianBlur(frame, (15, 15), 0)
            elif self.current_filter == "double":
                overlay = frame.copy()
                frame = cv2.addWeighted(frame, 0.5, np.roll(overlay, 20, axis=1), 0.5, 0)
            elif self.current_filter == "delayed":
                # Store previous frames and overlay them to create a trailing effect
                self.previous_frames.append(frame)
                if len(self.previous_frames) > 5:  # Keep the last 5 frames
                    self.previous_frames.pop(0)
                frame = np.copy(self.previous_frames[0])
                for prev_frame in self.previous_frames[1:]:
                    frame = cv2.addWeighted(frame, 0.7, prev_frame, 0.3, 0)

            # Create a VR-like double vision effect (side-by-side)
            h, w = frame.shape[:2]
            left_frame = frame  # Left side of the display
            right_frame = np.roll(frame, 20, axis=1)  # Right side with slight offset

            # Create a subtle rectangular mask to cut off small edges (instead of round)
            mask = np.ones((h, w), dtype=np.uint8) * 255  # White mask (no cut initially)
            border_width = int(w * 0.05)  # 5% of the width as the border to cut
            mask[:, :border_width] = 0  # Cut off 5% on the left side
            mask[:, -border_width:] = 0  # Cut off 5% on the right side

            # Apply the mask to both left and right frames
            left_frame = cv2.bitwise_and(left_frame, left_frame, mask=mask)
            right_frame = cv2.bitwise_and(right_frame, right_frame, mask=mask)

            # Combine the left and right frames into one image
            vr_frame = np.hstack((left_frame, right_frame))

            # Convert frame to texture for Kivy
            buffer = cv2.flip(vr_frame, 0).tobytes()
            texture = Texture.create(size=(vr_frame.shape[1], vr_frame.shape[0]), colorfmt="bgr")
            texture.blit_buffer(buffer, colorfmt="bgr", bufferfmt="ubyte")
            self.img.texture = texture

        return True  # Keep scheduling updates

    def set_filter(self, filter_name):
        self.current_filter = filter_name

    def on_stop(self):
        self.capture.release()

    def on_keyboard(self, key, *args):
        if key == 27:  # Android back button (keycode 27)
            app = App.get_running_app()
            app.root.current = "menu"
            return True  # Consume the event so that it doesn't go further

class CameraApp(App):
    def build(self):
        # Create screen manager
        sm = ScreenManager()
        
        # Add screens to the manager
        sm.add_widget(MenuScreen(name="menu"))
        sm.add_widget(CameraScreen(name="camera"))

        return sm

    def set_filter(self, filter_name):
        # Pass filter setting to camera screen
        camera_screen = self.root.get_screen("camera")
        camera_screen.set_filter(filter_name)

if __name__ == "__main__":
    CameraApp().run()
