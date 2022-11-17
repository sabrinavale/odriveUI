import os
import sys

# os.environ['DISPLAY'] = ":0.0"
# os.environ['KIVY_WINDOW'] = 'egl_rpi'

from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen

from pidev.MixPanel import MixPanel
from pidev.kivy.PassCodeScreen import PassCodeScreen
from pidev.kivy.PauseScreen import PauseScreen
from pidev.kivy import DPEAButton
from pidev.kivy import ImageButton

sys.path.append("/home/soft-dev/Documents/dpea-odrive/")
from time import sleep
from odrive_helpers import *
od = find_odrive()
ax = ODriveAxis(od.axis1)

ax.set_gains()
if not ax.is_calibrated():
    print("calibrating...")
    ax.calibrate()
ax.set_vel_limit(15)

MIXPANEL_TOKEN = "x"
MIXPANEL = MixPanel("Project Name", MIXPANEL_TOKEN)

SCREEN_MANAGER = ScreenManager()
MAIN_SCREEN_NAME = 'main'
TRAJ_SCREEN_NAME = 'traj'
GPIO_SCREEN_NAME = 'gpio'
ADMIN_SCREEN_NAME = 'admin'


class ProjectNameGUI(App):
    """
    Class to handle running the GUI Application
    """

    def build(self):
        """
        Build the application
        :return: Kivy Screen Manager instance
        """
        return SCREEN_MANAGER


Window.clearcolor = (1, 1, 1, 1)  # White


class MainScreen(Screen):
    """
    Class to handle the main screen and its associated touch events
    """
    velocity = 0
    currentRamp = 0

    def switch_to_traj(self):
        SCREEN_MANAGER.transition.direction = "left"
        SCREEN_MANAGER.current = TRAJ_SCREEN_NAME

    def switch_to_gpio(self):
        SCREEN_MANAGER.transition.direction = "right"
        SCREEN_MANAGER.current = GPIO_SCREEN_NAME

    def rotate_motor(self):
        if self.ids.rotate.rotation == False:
            #ax.set_vel(self.velocity)
            self.ids.rotate.rotation = True
            self.ids.rotate.text = "clockwise"
            ax.set_relative_pos(5)
            ax.wait_for_motor_to_stop()
        elif self.ids.rotate.rotation == True:
            #ax.set_vel(self.velocity)
            self.ids.rotate.rotation = False
            self.ids.rotate.text = "counter-clockwise"
            ax.set_relative_pos(-5)
            ax.wait_for_motor_to_stop()

    def stop(self):
        ax.set_vel(0)

    def home(self):
        ax.home_without_endstop(1, .5)

    def set_velocity(self, velocity: float):
        ax.set_vel(velocity)
        self.velocity = velocity

    def set_acceleration(self, accel: float):
        ax.set_ramped_vel(self.velocity, accel)
        #print(ax.get_vel())

    def admin_action(self):
        """
        Hidden admin button touch event. Transitions to passCodeScreen.
        This method is called from pidev/kivy/PassCodeScreen.kv
        :return: None
        """
        SCREEN_MANAGER.current = 'passCode'


class TrajectoryScreen(Screen):
    """
    Class to handle the trajectory control screen and its associated touch events
    """
    currentPos = 0
    currentRamp = 0
    currentDeRamp = 0
    currentVel = 0

    def switch_screen(self):
        SCREEN_MANAGER.transition.direction = "right"
        SCREEN_MANAGER.current = MAIN_SCREEN_NAME

    def target_pos(self):
        current_pos = self.ids.target_position.value
        current_pos = int(current_pos)
        current_pos += 1
        self.ids.target_position.value = str(current_pos)
        self.currentPos = current_pos

    def accelerate(self):
        acc = self.ids.accelerate.value
        acc = int(acc)
        acc += 1
        self.ids.accelerate.value = str(acc)
        self.currentRamp = acc

    def deceleration(self):
        dec = self.ids.decelerate.value
        dec = int(dec)
        dec += 1
        self.ids.decelerate.value = str(dec)
        self.currentDeRamp = dec

    def velocity(self):
        vel = self.ids.velo.value
        vel = int(vel)
        vel += 1
        self.ids.velo.value = str(vel)
        self.currentVel = vel

    def submission(self):
        ax.set_pos_traj(self.currentPos, self.currentRamp, self.currentVel, self.currentDeRamp)

class GPIOScreen(Screen):
    """
    Class to handle the GPIO screen and its associated touch/listening events
    """

    def switch_screen(self):
        SCREEN_MANAGER.transition.direction = "left"
        SCREEN_MANAGER.current = MAIN_SCREEN_NAME


class AdminScreen(Screen):
    """
    Class to handle the AdminScreen and its functionality
    """

    def __init__(self, **kwargs):
        """
        Load the AdminScreen.kv file. Set the necessary names of the screens for the PassCodeScreen to transition to.
        Lastly super Screen's __init__
        :param kwargs: Normal kivy.uix.screenmanager.Screen attributes
        """
        Builder.load_file('AdminScreen.kv')

        PassCodeScreen.set_admin_events_screen(
            ADMIN_SCREEN_NAME)  # Specify screen name to transition to after correct password
        PassCodeScreen.set_transition_back_screen(
            MAIN_SCREEN_NAME)  # set screen name to transition to if "Back to Game is pressed"

        super(AdminScreen, self).__init__(**kwargs)

    @staticmethod
    def transition_back():
        """
        Transition back to the main screen
        :return:
        """
        SCREEN_MANAGER.current = MAIN_SCREEN_NAME

    @staticmethod
    def shutdown():
        """
        Shutdown the system. This should free all steppers and do any cleanup necessary
        :return: None
        """
        os.system("sudo shutdown now")

    @staticmethod
    def exit_program():
        """
        Quit the program. This should free all steppers and do any cleanup necessary
        :return: None
        """
        quit()


"""
Widget additions
"""

Builder.load_file('main.kv')
SCREEN_MANAGER.add_widget(MainScreen(name=MAIN_SCREEN_NAME))
SCREEN_MANAGER.add_widget(TrajectoryScreen(name=TRAJ_SCREEN_NAME))
SCREEN_MANAGER.add_widget(GPIOScreen(name=GPIO_SCREEN_NAME))
#SCREEN_MANAGER.add_widget(PassCodeScreen(name='passCode'))
SCREEN_MANAGER.add_widget(PauseScreen(name='pauseScene'))
SCREEN_MANAGER.add_widget(AdminScreen(name=ADMIN_SCREEN_NAME))

"""
MixPanel
"""


def send_event(event_name):
    """
    Send an event to MixPanel without properties
    :param event_name: Name of the event
    :return: None
    """
    global MIXPANEL

    MIXPANEL.set_event_name(event_name)
    MIXPANEL.send_event()


if __name__ == "__main__":
    # send_event("Project Initialized")
    # Window.fullscreen = 'auto'
    ProjectNameGUI().run()
