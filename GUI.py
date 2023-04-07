import tkinter as tk
from typing import Dict, List
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib
import serial
from matplotlib import style
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import ttk
from tkinter.messagebox import showerror
import tkinter.font as font
import numpy as np
import math

from serial_link import get_from_serial, ARRAY_SIZE


class Action:
    def __init__(self, name: str, color: str) -> None:
        self.name = name
        self.values: np.ndarray = list(range(ARRAY_SIZE))
        self.isRegistered: bool = False
        self.isActive: tk.BooleanVar = None
        self.plot_line = None
        self.color: str = color

    def getState(self) -> tk.BooleanVar:
        if self.isActive == None:
            self.isActive = tk.BooleanVar(value=False)
        return self.isActive

    def setValues(self, values: List):
        self.values = values
        self.isRegistered = True

    def drawPlot(self, plt):
        if self.plot_line == None:
            (self.plot_line,) = plt.plot(range(160), self.values, self.color)
        else:
            self.plot_line.set_data(range(160), self.values)

    def reset(self):
        if not self.isRegistered:
            return

        self.plot_line.remove()
        self.plot_line = None
        self.isActive.set(False)
        self.values = None
        self.isRegistered = False


class GUI:
    def __init__(s) -> None:
        s.root = tk.Tk()
        s.root.geometry("1200x700+200+100")
        s.root.tk.call("tk", "scaling", 2.5)
        s.root.state("zoomed")
        s.root.title("Arduino Advanced Touch Sensor")
        s.root.option_add("*tearOff", False)  # This is always a good idea
        s.root.rowconfigure(index=0, weight=1)
        s.root.rowconfigure(index=1, weight=4)
        s.root.rowconfigure(index=2, weight=4)
        s.root.columnconfigure(index=0, weight=4)
        s.root.columnconfigure(index=1, weight=4)

        s.actions: List[Action] = [
            Action("Baseline", "g"),
            Action("Finger Touch", "b"),
            Action("Grip", "m"),
            Action("In Water", "r"),
        ]
        s.x_values = np.arange(160)
        s.y_values = np.zeros(shape=ARRAY_SIZE, dtype=np.int32)
        s.connection_state: bool = False
        s.connection_port: tk.StringVar = tk.StringVar(s.root, "COM4")
        s.connection_baud_rate: tk.IntVar = tk.StringVar(s.root, "115200")

        s.setup_theme("./themes/forest-dark.tcl")
        s.setup_title()
        s.setup_connection_frame()
        s.setup_connection_frame()
        s.setup_register_action_frame()
        s.setup_status_frame()
        s.setup_graph()

    def setup_title(s) -> None:
        title = ttk.Label(
            s.root,
            text="Arduino Advanced Touch Sensor",
            font=("Courier", 40),
            justify=tk.CENTER,
            anchor=tk.CENTER,
        )
        title.grid(row=0, column=0, rowspan=1, padx=10, pady=10, sticky=tk.NSEW)

    def setup_register_action_frame(s):
        register_actions_frame = ttk.LabelFrame(
            s.root, text="Register Actions", padding=(20, 20)
        )
        register_actions_frame.grid(row=1, column=1, sticky=tk.NSEW, padx=10, pady=10)
        for i, a in enumerate(s.actions):
            button = ttk.Button(
                register_actions_frame,
                text="Register " + a.name,
                style="Big.Accent.TButton",
                command=lambda action=a: s.register_action(action),
                state=tk.NORMAL if s.connection_state else tk.DISABLED,
            )
            button.grid(row=i, column=0, sticky=tk.NSEW, padx=20, pady=20)

    def setup_status_frame(s):
        status_frame = ttk.LabelFrame(
            s.root, text="Touch Detection Predictions", padding=(20, 20)
        )
        status_frame.grid(row=2, column=1, sticky=tk.NSEW, padx=10, pady=10)
        for i, a in enumerate(s.actions):
            chkbtn = ttk.Radiobutton(
                status_frame,
                text=a.name,
                variable=a.getState(),
                style="TRadiobutton",
            )
            chkbtn.grid(row=i, column=0, sticky=tk.NSEW, padx=20, pady=20)

    def setup_connection_frame(s):
        connection_frame = ttk.LabelFrame(s.root, text="Connection", padding=(20, 20))
        connection_frame.grid(row=2, column=0, sticky=tk.NSEW, padx=10, pady=10)
        connection_frame.columnconfigure(index=0, weight=1)
        connection_frame.columnconfigure(index=1, weight=1)
        connection_frame.rowconfigure(index=0, weight=1)

        config_frame = ttk.LabelFrame(
            connection_frame, text="Configuration", padding=(20, 20)
        )
        config_frame.grid(row=0, column=0, sticky=tk.NSEW, padx=10, pady=10)
        con_port_combobox = ttk.Combobox(
            config_frame,
            textvariable=s.connection_port,
            values=["COM4", "COM3", "COM2"],
            style="TCombobox",
        )
        con_port_combobox.current(0)
        con_port_combobox.grid(row=0, column=0, padx=5, pady=10, sticky="nsew")
        con_baud_rate_entry = ttk.Combobox(
            config_frame,
            textvariable=s.connection_baud_rate,
            style="TCombobox",
            values=[
                115200,
                57600,
                38400,
                31250,
                28800,
                19200,
                14400,
                9600,
                4800,
                2400,
                1200,
                600,
                300,
            ],
        )
        con_baud_rate_entry.current(0)
        con_baud_rate_entry.grid(row=1, column=0, padx=5, pady=10, sticky="nsew")

        control_frame = ttk.LabelFrame(
            connection_frame, text="Controls", padding=(20, 20)
        )
        control_frame.grid(row=0, column=1, sticky=tk.NSEW, padx=10, pady=10)
        control_frame.rowconfigure(index=0, weight=1)
        control_frame.rowconfigure(index=1, weight=1)
        control_frame.columnconfigure(index=0, weight=1)
        control_frame.columnconfigure(index=1, weight=1)

        s.start_button = ttk.Button(
            control_frame,
            text="Connect to Port",
            style="Big.Accent.TButton",
            command=lambda: s.open_connection(
                s.connection_port.get(), int(s.connection_baud_rate.get())
            ),
        )
        s.start_button.grid(row=0, column=0, padx=10, pady=10, sticky=tk.NSEW)
        s.reset_actions = ttk.Button(
            control_frame,
            text="Reset all actions",
            style="Big.Accent.TButton",
            command=lambda: [a.reset() for a in s.actions],
        )
        s.reset_actions.grid(row=1, column=0, padx=10, pady=10, sticky=tk.NSEW)

        s.add_action = ttk.Button(
            control_frame,
            text="Add an action",
            style="Big.Accent.TButton",
            command=s.open_add_action_window,
        )
        s.add_action.grid(row=0, column=1, padx=10, pady=10, sticky=tk.NSEW)

        s.remove_action = ttk.Button(
            control_frame,
            text="Remove all actions",
            style="Big.Accent.TButton",
            command=s.remove_all_actions,
        )
        s.remove_action.grid(row=1, column=1, padx=10, pady=10, sticky=tk.NSEW)

    def setup_theme(s, theme: str):
        # Create a style
        style = ttk.Style(s.root)
        # Import the tcl file
        s.root.tk.call("source", theme)
        # Set the theme with the theme_use method
        style.theme_use("forest-dark")
        style.configure("Big.Accent.TButton", font=("Courier", 20))
        style.configure("Big.Accent.TButton", font=("Courier", 20))
        style.configure("TRadiobutton", font=("Courier", 20))
        style.configure("TCombobox", font=("Courier", 20))

    def setup_graph(s):
        style.use("dark_background")
        s.fig = plt.figure(figsize=(8, 3.5), dpi=100)
        s.plot_axis = s.fig.add_subplot(1, 1, 1)
        s.plot_axis.set_ylim(0, 50)
        s.plot_axis.set_xlim(0, 160)
        (s.plot_line,) = s.plot_axis.plot(
            [0 for i in range(ARRAY_SIZE)], [0 for i in range(ARRAY_SIZE)], "y"
        )
        s.ani = animation.FuncAnimation(
            s.fig, s.animate, interval=10, cache_frame_data=False
        )
        s.ani.pause()
        graph_frame = ttk.LabelFrame(s.root, text="Input Waveform", padding=(20, 20))
        graph_frame.grid(row=1, column=0, sticky=tk.NSEW, padx=10, pady=10)
        plotcanvas = FigureCanvasTkAgg(s.fig, graph_frame)
        plotcanvas.get_tk_widget().grid(
            column=0, row=1, sticky=tk.NSEW, padx=10, pady=10
        )

        plt.subplots_adjust(bottom=0.30)
        plt.title("Frequency vs Response Plot")
        plt.ylabel("Analog Read")
        plt.xlabel("Frequency")
        plt.tight_layout(pad=2)

    def open_connection(s, com: str = "COM4", baud_rate: int = 115200) -> None:
        try:
            s.port = serial.serial_for_url(com, baud_rate)
            s.ani.resume()
            s.connection_state = True
            s.setup_register_action_frame()
            s.start_button["text"] = "Close Connection"
            s.start_button["command"] = s.close_connection
        except Exception as e:
            print("Error: Connection Failed !")
            showerror(
                title="Connection Failed",
                message=f"Error Connection to board failed: " + e.__str__(),
            )

    def close_connection(s) -> None:
        s.ani.pause()
        s.port.close()
        s.connection_state = False
        s.start_button["text"] = "Open Connection"
        s.start_button["command"] = s.open_connection

    def animate(s, _):
        try:
            if not s.connection_state:
                return

            inst_values, freq = get_from_serial(s.port)
            # s.plot_axis.cla()
            for inst_val, f in zip(inst_values, freq):
                s.y_values[f] = inst_val
            min = None
            min_action = None
            for action in s.actions:
                if not action.isRegistered:
                    continue
                action.getState().set(False)
                inst_val = math.dist(s.y_values, action.values)
                if min == None or min >= inst_val:
                    min = inst_val
                    min_action = action

            if min_action != None:
                min_action.getState().set(True)

            s.plot_line.set_data(s.x_values, s.y_values)
            return s.plot_line
        except Exception as e:
            print("Error: Updating graph ", e)

    def register_action(s, action: Action):
        # take the average of 5 readings
        try:
            s.ani.pause()
            values = np.zeros(shape=ARRAY_SIZE, dtype=np.int32)
            for i in range(10):
                vals, freqs = get_from_serial(s.port)
                for val, freq in zip(vals, freqs):
                    values[freq] = val * 0.5 + values[freq] * 0.5
            action.setValues(values)
            action.drawPlot(s.plot_axis)
            s.ani.resume()
        except Exception as e:
            print("Error registering action ", e)

    def open_add_action_window(s):
        
        window = tk.Toplevel(s.root)
        window.title("Add Action")
        window.rowconfigure(index=0, weight=1)
        window.rowconfigure(index=1, weight=1)
        window.rowconfigure(index=2, weight=1)
        window.columnconfigure(index=0, weight=1)
        window.geometry("600x500")

        def add_action(a: Action):
            s.actions.append(a)
            s.setup_register_action_frame()
            s.setup_status_frame()
            window.destroy()

        action_name = tk.StringVar()
        action_color = tk.StringVar()

        name_frame = ttk.LabelFrame(window, text="Action Name", padding=(20, 20))
        name_frame.grid(row=0, column=0, padx=5, pady=10, sticky=tk.NSEW)
        entry = ttk.Entry(name_frame, textvariable=action_name)
        entry.insert(0, "Enter Action Name")
        entry.pack(side=tk.TOP, expand=tk.YES, fill=tk.BOTH)
        # entry.grid(row=0, column=0, padx=5, pady=10, sticky=tk.NSEW)

        color_frame = ttk.LabelFrame(window, text="Color Graph", padding=(20, 20))
        color_frame.grid(row=1, column=0, padx=5, pady=10, sticky=tk.NSEW)
        combobox = ttk.Combobox(
            color_frame,
            textvariable=action_color,
            values=["b", "g", "r", "c", "m", "w"],
        )
        combobox.current(0)
        combobox.pack(side=tk.TOP, expand=tk.YES, fill=tk.BOTH)
        # combobox

        button = ttk.Button(
            window,
            text="Add Action",
            style="Accent.TButton",
            command=lambda: add_action(Action(action_name.get(), action_color.get()))
        )
        button.grid(row=2, column=0, padx=5, pady=10, sticky=tk.NSEW)    

    def remove_all_actions(s):
        s.actions.clear()
        s.setup_register_action_frame()
        s.setup_status_frame()

    def run(s):
        # Center the window, and set minsize
        s.root.update()
        s.root.minsize(s.root.winfo_width(), s.root.winfo_height())
        x_cordinate = int((s.root.winfo_screenwidth() / 2) - (s.root.winfo_width() / 2))
        y_cordinate = int(
            (s.root.winfo_screenheight() / 2) - (s.root.winfo_height() / 2)
        )
        s.root.geometry("+{}+{}".format(x_cordinate, y_cordinate))

        # Start the main loop
        s.root.mainloop()


# The lists to store serial data receive

# Setup Tkinter


# Create figure for plotting
# style.use('dark_background')
# fig = plt.figure(figsize=(14, 4.5), dpi=100)
# ax = fig.add_subplot(1, 1, 1)
# plt.subplots_adjust(bottom=0.30)
# plt.title('Frequency vs Response Plot')
# plt.ylabel('Analog OUT')
# line = ax.plot(y_axis, x_axis)[0]
# # This function is called periodically from FuncAnimation
# def animate(i:int, *args):
#     # port = args[0]
#     x_axis, y_axis= get_from_serial(port)
#     ax.cla()
#     ax.plot( y_axis, x_axis)
#     # Draw x and y lists


# Set up plot to call animate() function periodically
# port = s.serial_for_url("COM4",115200)
# port = s.serial_for_url("COM4",115200)


if __name__ == "__main__":
    g = GUI()
    g.run()
