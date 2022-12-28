# -*- coding: utf-8 -*-

# %% Import toolboxes
import os
import gc
import sys
import cv2
import time
import queue
import PySpin
import skvideo
import threading
import skvideo.io
import numpy as np
import tkinter as tk
import PySpinHelper as PSHelper
from operator import attrgetter
from PIL import Image, ImageTk

# %% Mapped Method class
class MappedMethod:
    """
    This class maps a single method to all elements of an iterable, with both
    *args and **kwargs compatibility.
    :param elements: Elements onto which the method should be applied.
    :type elements: iterable
    :param *args: Any args applicabale to the method (will be applied uniformly to all elements).
    :type *args: any (method-dependent)
    :param **kwargs: Any kwargs applicable to the method (will be applied unformly to all elements).
    :type **kwargs: any (method-dependent)
    """
    def __init__(self, elements):
        self.elements = elements
    def __getattr__(self, attr):
        def apply_to_all(*args, **kwargs):
            for obj in self.elements:
                getattr(obj, attr)(*args, **kwargs)
        return apply_to_all

# %% Display Window class
class DisplayWindow:
    """
    This class enables live-stream display of queued images.
    :param display: Tkinter frame for displaying images.
    :type display: tkinter.Toplevel
    :param display_height: Height (in pixels) of display frame. Used for transformation of raw image sizes.
    :type display_height: int
    :param display_width: Width (in pixels) of display frame. Used for transformation of raw image sizes.
    :type display_width: int
    :param display_queue: Queue of images to be displayed.
    :type display_queue: queue.Queue
    :param img_height: Height (in pixels) of raw image. Used for initialization of blank frame.
    :type img_height: int
    :param img_width: Width (in pixels) of raw image. Used for initialization of blank frame.
    :type img_width: int
    """
    def __init__(self,display,display_height,display_width,display_queue,\
                 img_height,img_width):
        self.display        = display
        self.display_height = display_height
        self.display_width  = display_width
        self.img_height     = img_height
        self.img_width      = img_width
        self.queue          = display_queue
        self.image          = np.zeros([self.img_height,self.img_width],dtype=np.uint8)
        self.prettify()
        self.image          = ImageTk.PhotoImage(master=self.display,image=Image.fromarray(self.image))
        self.label          = tk.Label(self.display,image=self.image)
        self.label.pack()
        #self.display.update()

    def draw(self):
        """
        This function converts numpy array-form images into tkinter-friendly PIL
        images for display and updates the display window.
        """
        self.image       = ImageTk.PhotoImage(master=self.display,image=Image.fromarray(self.image))
        self.label.configure(image=self.image)
        self.label.image = self.image

    def refresh(self):
        """
        This function recursively checks the queue for new images to display
        until the GLOBAL variable stop_acquisition is set to True. After acquiring
        a new image, the numpy array-form image is resized, color-adjusted,
        and sent for display. The queue is informed that the task has been completed
        and the function is called again.
        """
        global stop_acquisition
        if stop_acquisition is not True:
            self.image = self.queue.get()
            self.prettify()
            self.draw()
            self.queue.task_done()
            self.display.after(10,self.refresh)

    def prettify(self):
        """
        This function resizes numpy array-form images from their raw sizes to
        the size of the display using default interpolation algorithms. Images
        are recolored from RGB to BGR for PIL conversion and display.
        """
        self.image = cv2.resize(self.image,dsize=(self.display_width,self.display_height))
        self.image = cv2.cvtColor(self.image,cv2.COLOR_BGR2RGB)

    def terminate(self):
        """
        This function destroys the display window, removes it from memory,
        and calls on Python garbage collection to evade tlc-type terminal errors.
        """
        self.display.destroy()
        self.display = None
        del self.display
        gc.collect()

# %% Spinnaker Camera class
class SpinnakerCamera:
    """
    This class enables control of an individual camera.
    :param cam: Spinnaker camera for acquiring images.
    :type cam: PySpin.PySpin.CameraPtr
    :param display: Tkinter frame for displaying images.
    :type display: tkinter.Toplevel
    :param display_height: Height (in pixels) of display frame. Used for transformation of raw image sizes.
    :type display_height: int
    :param display_width: Width (in pixels) of display frame. Used for transformation of raw image sizes.
    :type display_width: int
    :param print_lock: Thread lock for print calls to prevent overwriting stdout from multiple threads.
    :type print_lock: _thread.lock
    :param exposure_time: Desired camera exposure time (us).
    :type exposure_time: int
    :param gain: Desired camera gain value.
    :type gain: int
    :param gamma: Desired camera gamma value (0-1).
    :type gamma: float
    :param img_height: Desired pixel height of camera acquisition.
    :type img_height: int
    :param img_width: Desored pixel width of camera acquisition.
    :type img_width: int
    :param height_offset: Desired vertical pixel offset of camera acquisition (from top edge).
    :type height_offset: int
    :param width_offset: Desired lateral pixel offset of camera acquisition (from left edge).
    :type width_offset: int
    :param frame_rate: Desired acquisiton frame rate.
    :type frame_rate: int
    """
    def __init__(self,cam,display,display_height,display_width,print_lock,cam_num,
                 session_type,exposure_time=15000,gain=5,gamma=0.5,img_height=1300,
                 img_width=1852,height_offset=200,width_offset=300,frame_rate=50):
        self.camera           = cam
        self.session_type     = session_type
        self.gain             = gain
        self.gamma            = gamma
        self.frame_rate       = frame_rate
        self.print_lock       = print_lock
        if self.session_type in {'Recall','Re-recall'}:
            self.img_height   = 1548
            self.img_width    = 2200
            self.height_offset= 320
            self.width_offset = 124
            self.exposure_time= 3500
        else:
            self.img_height       = img_height
            self.img_width        = img_width
            self.height_offset    = height_offset
            self.width_offset     = -1 * width_offset * cam_num + width_offset + cam_num * 100
            self.exposure_time    = exposure_time
        self.image_queue      = queue.Queue()
        self.display_queue    = queue.Queue()
        self.display_height   = display_height
        self.display_width    = display_width
        self.display          = DisplayWindow(display,self.display_height,self.display_width,\
                                              self.display_queue,self.img_height,\
                                              self.img_width)
        self.stop_acquisition = False
        self.camera.Init()

    def set_params(self,mouse,day,filepath):
        """
        This function sets basic camera parameters from the helper function
        PySpinHelper in accordance with object initialization parameters.
        :param mouse: Current mouse undergoing behavior training.
        :type mouse: str
        :param day: Day of training for current mouse.
        :type day: int
        :param filepath: Save location for video writer.
        :type filepath: str
        """
        nodemap   = self.camera.GetNodeMap()
        s_nodemap = self.camera.GetTLStreamNodeMap()
        # PSHelper.print_category_node_and_all_features(nodemap.GetNode('Root'))
        PSHelper.set_aquisition_params(nodemap)
        PSHelper.set_pixel_params(nodemap)
        PSHelper.set_picture_width(nodemap,self.img_width)
        PSHelper.set_picture_height(nodemap,self.img_height)
        PSHelper.set_offset_x(nodemap,self.width_offset)
        PSHelper.set_offset_y(nodemap,self.height_offset)
        PSHelper.set_exposure_params(nodemap,self.exposure_time)
        PSHelper.set_gain_params(nodemap,self.gain)
        PSHelper.set_gamma(nodemap,self.gamma)
        PSHelper.set_trigger_params(nodemap)
        PSHelper.set_frame_rate(nodemap,self.frame_rate)
        PSHelper.set_buffer_params(s_nodemap)

        try:
            t_nodemap   = self.camera.GetTLDeviceNodeMap()
            serial_node = PySpin.CStringPtr(t_nodemap.GetNode('DeviceSerialNumber'))
            if PySpin.IsAvailable(serial_node) and PySpin.IsReadable(serial_node):
                self.serial = serial_node.GetValue()
        except:
            self.serial = '00000000'

        self.recording_name = os.path.join(filepath,'day{}_{}_serial{}.mp4'.format(str(day),str(mouse),self.serial))

    def begin_acquisition(self,crf):
        """
        This function initiates acquisition by the Spinnaker camera, assigns
        an I/O writer for video output, and calls on the recursive display refresher
        function. All work is threaded.
        :param crf: Constant Rate Factor for determining encoding quality (scale: 0-51, where 0 is lossless)
        :type crf: int
        """
        self.camera.BeginAcquisition()
        self.writer = skvideo.io.FFmpegWriter(self.recording_name,\
                                              inputdict={'-r': str(self.frame_rate)},\
                                              outputdict={'-vcodec': 'libx264',\
                                                          '-preset': 'ultrafast',\
                                                          '-pix_fmt': 'yuv444p',\
                                                          '-crf': str(crf),\
                                                          '-r': str(self.frame_rate)})
        self.save_thread = threading.Thread(target=self.save_image)
        self.save_thread.start()
        self.acquire_thread = threading.Thread(target=self.acquire_image)
        self.acquire_thread.start()
        self.display.refresh()

    def acquire_image(self):
        """
        This function requests incoming images from the Spinnaker camera (blocking function)
        and transforms the images into numpy array-form images of the desired dimensions
        before placing images in two distinct cues for saving and display. Images
        are released from memory to create space for the following incoming image. Processes
        halt immediately after the GLOBAL variable stop_acquisition is set to True.
        """
        #with Spinner(self.print_lock):
        while True:
            global stop_acquisition
            if stop_acquisition is True:
                #self.print_lock.acquire()
                print('Stream aborted...')
                #self.print_lock.release()
                break
            else:
                try:
                    image = self.camera.GetNextImage()
                    image_reshaped = np.array(image.GetData(), dtype="uint8").reshape( (image.GetHeight(), image.GetWidth()) )
                    self.image_queue.put(image_reshaped)
                    self.display.queue.put(image_reshaped)
                    image.Release()
                except(PySpin.SpinnakerException):
                    break
        return

    def save_image(self):
        """
        This function saves images acquired by the Spinnaker camera one by one
        (oldest first) from the image queue. Processes halt immediately after
        the GLOBAL variable stop_acquisition is set to True, and the threading
        Event save_completed is set, enabling post-acquisition operation of the
        GUI.
        """
        while True:
            global stop_acquisition
            global save_completed
            if stop_acquisition is True:
                if not self.image_queue.empty():
                    dequeued_image = self.image_queue.get()
                    self.writer.writeFrame(dequeued_image)
                    self.image_queue.task_done()
                else:
                    #self.print_lock.acquire()
                    print('\rSaving completed...')
                    #self.print_lock.release()
                    save_completed.set()
                    break
            else:
                dequeued_image = self.image_queue.get()
                self.writer.writeFrame(dequeued_image)
                self.image_queue.task_done()

    def end_acquisition(self):
        """
        This function terminates Spinnaker camera acquisition, closes the video
        writer, destroys the display, and deletes all objects from memory. Python
        garbace collection is called to evade tlc-type terminal errors.
        """
        global save_completed
        self.camera.EndAcquisition()
        save_completed.wait()
        self.display.terminate()
        time.sleep(5)
        self.writer.close()
        self.camera.DeInit()
        del self.camera
        del self.writer
        del self.display
        gc.collect()

# %% Main class
class Main:
    """
    This class initializes the Spinnaker API, oversees camera operations, and
    manages all displays.
    :param savepath: Save location for video writer.
    :type savepath: str
    :param day: Day of training for current mouse.
    :type day: int
    :param mouse: Current mouse undergoing behavior training.
    :type mouse: str
    :param print_lock: Thread lock for print calls to prevent overwriting stdout from multiple threads.
    :type print_lock: _thread.lock
    :param session_type: Name of behavioral session type.
    :type session_type: str
    :param crf: Constant Rate Factor for determining encoding quality (scale: 0-51, where 0 is lossless).
    :type crf: int
    :param display_height: Height (in pixels) of display frame. Used for generating and organizing frames.
    :type display_height: int
    :param display_width: Width (in pixels) of display frame. Used for generating and organizing frames.
    :type display_width: int
    """
    def __init__(self,savepath,day,mouse_li,print_lock,session_type,\
                 crf=17,display_height=450,display_width=600):
        self.savepath       = savepath
        self.day            = day
        self.mouse          = next(iter(mouse_li)) if len(mouse_li) == 1 else '+'.join(mouse_li)
        self.print_lock     = print_lock
        self.session_type   = session_type
        self.crf            = crf
        self.display_height = display_height
        self.display_width  = display_width

    def run(self):
        """
        This workhorse function initializes all cameras and displays and begins
        acquisition while calling the recursive raise_exception function to
        seek the GLOBAL stop_acquisition flag. All processes are threaded prior
        to tkinter mainloop enterance.
        """
        self.initialize_pyspin()
        self.root     = tk.Tk()
        self.root.withdraw()
        self.displays = [tk.Toplevel(self.root) for cam in self.cam_list]
        self.initialize_cameras()
        cameras_ready.set()
        self.organize()
        MappedMethod(self.cameras).begin_acquisition(self.crf)
        MappedMethod(self.displays).lift()
        MappedMethod(self.displays).attributes("-topmost",True)
        self.root.after(1,self.raise_exception)
        #self.print_lock.acquire()
        print('Entering mainloop...')
        #self.print_lock.release()
        self.root.mainloop()

    def initialize_pyspin(self):
        """
        This function generates a Spinnaker instance and identifies the connected
        Spinnaker cameras. If session is of type RECALL, only camera 2 is
        kept for image acquisition. Otherwise, both cameras are utilized.
        """
        self.system   = PySpin.System.GetInstance()
        self.cam_list = self.system.GetCameras()
        # if self.session_type == 'Recall':
        #     print('Registering left camera for Recall image acquisition...')
        #     self.cam_list = [self.cam_list.pop()]
        # else:
        #     print('Registering all cameras for image acquisition...')

    def initialize_cameras(self):
        """
        This function generates Spinnaker Camera objects from each connected
        Spinnaker camera and sets all camera parameters as desired.
        """
        self.cameras  = list(map(SpinnakerCamera,self.cam_list,\
                                [display for display in self.displays],\
                                [self.display_height for cam in range(len(self.cam_list))],\
                                [self.display_width for cam in range(len(self.cam_list))],\
                                [self.print_lock for cam in range(len(self.cam_list))],\
                                [cam_num for (cam_num,cam) in enumerate(self.cam_list)],
                                [self.session_type for cam in range(len(self.cam_list))]))
        MappedMethod(self.cameras).set_params(self.mouse,self.day,self.savepath)

    def raise_exception(self):
        """
        This function attains the GLOBAL stop_acquisition flag to manage all operations
        and terminate them according to the flag status. After checking status,
        if False, the function is recursively called (in thread). Upon flag status
        change, camera acquisition is terminated and all references to Spinnaker
        and tkinter objects are deleted from memory. Python garbage collection
        is called to evade tlc-type terminal errors.
        """
        global stop_acquisition
        if stop_acquisition is True:
            #self.print_lock.acquire()
            print('\rTerminating acquisition...')
            #self.print_lock.release()
            MappedMethod(self.cameras).end_acquisition()
            self.cam_list.Clear()
            del self.cam_list
            self.system.ReleaseInstance()
            del self.system
            #self.print_lock.acquire()
            # print('All processes terminated...')
            #self.print_lock.release()
            del self.displays
            self.root.destroy()
            buffers_emptied.set()
            self.root = None
            gc.collect()
        else:
            self.root.after(1,self.raise_exception)

    def organize(self):
        """
        This function organizes display windows to generate a friendly UI.
        """
        screen_width  = self.root.winfo_screenwidth()
        y_loc         = 0
        serials       = iter(list(map(attrgetter('serial'),self.cameras)))
        for order, cam in enumerate(self.cameras):
            x_loc = screen_width - self.display_width - (order * self.display_width)
            cam.display.display.geometry('{}x{}+{}+{}'.format(self.display_width,self.display_height,x_loc,y_loc))
            cam.display.display.title('FLIR{} (Camera {})'.format(next(serials),(order+1)))

# %% Controller function
def controller(ready,terminate,print_lock,params):
    """
    This function is the top-level controller of all active cameras and camera
    tasks, monitoring camera readiness and buffer status and passing these
    states to the higher level behavior controller function. The Main class is
    initialized and run in a separate thread. Progress from this thread is
    monitored via a Threading.Event type object. After camera initialization and
    parameterization, behavior is initiated by updating the state of a second
    Threading.Event type object. Behavior is terminated following global update
    of a third Threading.Event type object. Python garbage collection is called
    to evade tlc-type terminal errors.
    :param ready: Thread event to signal completion of camera initialization and parameterization. Holding event for initiation of behavioral protocol.
    :type ready: Threading.Event
    :param terminate: Thread event to signal termination of behavioral protocol. Holding event for termination of camera acquisition.
    :type terminate: Threading.Event
    :param print_lock: Thread lock for print calls to prevent overwriting stdout from multiple threads.
    :type print_lock: _thread.lock
    :param params: Container for save path, behavioral day, and mouse ID.
    :type params: dict
    """
    global cameras_ready
    global buffers_emptied
    global stop_acquisition
    global save_completed
    global image_reshaped
    cameras_ready    = threading.Event()
    buffers_emptied  = threading.Event()
    save_completed   = threading.Event()
    stop_acquisition = False
    image_reshaped   = None
    save_path        = params.save_params['tmp_path']
    day              = params.save_params['day']
    mouse_li         = params.save_params['mice']
    main_thread      = Main(save_path,day,mouse_li,print_lock,params.session_type,17)
    threading.Thread(target=main_thread.run).start()
    print_lock.acquire()
    print('Waiting for cameras to initiate...')
    print_lock.release()
    cameras_ready.wait()
    ready.set()
    print_lock.acquire()
    print('Cameras initiated...')
    print_lock.release()
    terminate.wait()
    stop_acquisition = True
    buffers_emptied.wait()
    del main_thread
    gc.collect()