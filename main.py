import re
import webbrowser
from tkinter import Tk, messagebox, OptionMenu, StringVar, Button, Label, Entry, Frame, CENTER, LabelFrame, IntVar
from tkinter.filedialog import askopenfilename
from tkinter.font import Font
from typing import Callable

import pandas as pd
import numpy as np

LABEL_COLUMN_NAME = "class_label"
selected_column = ""
start_index = 0
end_index = 0
current_index = 0
labels = []
is_show_labeling_tool = False
labelling_frame = None
is_init = False

window = Tk()
window.title("Thoth")
window.config(width=1280, height=720)


def ask_for_file():
    try:
        filename = askopenfilename()
        df = pd.read_csv(filename)
        if not LABEL_COLUMN_NAME in df.columns:
            df[LABEL_COLUMN_NAME] = np.nan
        return df
    except FileNotFoundError:
        exit(1)
    except pd.errors.ParserError:
        messagebox.showwarning(message="File type is incorrect.")
        ask_for_file()


def setting_frame(df: pd.DataFrame):
    read_settings_from_file()

    def callback():
        if int(end.get()) >= len(df.index) or int(start.get()) < 0:
            messagebox.showerror(message="Please edit your start/end index to be in correct range.")
            return
        global selected_column, start_index, end_index, current_index
        selected_column = selected_value.get()
        start_index = int(start.get())
        end_index = int(end.get())
        current_index = start_index
        save_setting_to_file()
        messagebox.showinfo(message="Data saved to config file.")
        if not is_show_labeling_tool:
            show_labeling_tool(df)

    frame = LabelFrame(window, text="Config")

    global selected_column, start_index, end_index

    start = IntVar(frame, start_index)
    end = IntVar(frame, end_index)
    user_choice = StringVar(frame, selected_column)

    possible_choices = df.columns

    dataset_length = create_label(frame, f"This data set has shape of {df.shape}")
    selected_value, dropdown = create_drop_down(frame, possible_choices, user_choice)
    column_label = create_label(frame, "Column for display text")

    start_index_entry_label = create_label(frame, "Start index")
    start_index_entry = create_entry(frame, start)
    end_index_entry_label = create_label(frame, "End index")
    end_index_entry = create_entry(frame, end)

    confirm_button = create_button(frame, "Save", callback)

    frame.config(padx=48, pady=48)

    column_label.grid(row=0, column=0, padx=10, pady=5, sticky="W")
    dropdown.grid(row=0, column=1, padx=10, pady=5, sticky="W")
    dataset_length.grid(row=0, column=3, padx=10, pady=5, sticky="E")
    start_index_entry_label.grid(row=1, column=0, padx=10, pady=5, sticky="W")
    start_index_entry.grid(row=1, column=1, padx=10, pady=5, sticky="W")
    end_index_entry_label.grid(row=1, column=2, padx=20, pady=5, sticky="W")
    end_index_entry.grid(row=1, column=3, padx=10, pady=5, sticky="E")
    confirm_button.grid(row=2, column=3, padx=10, pady=5, sticky="E")

    frame.place(relx=0.5, rely=0.3, anchor=CENTER)


def show_labeling_tool(df: pd.DataFrame):
    global selected_column, start_index, end_index, current_index, labels, labelling_frame, remaining_label, text_label, is_init
    try:
        if labelling_frame is None:
            labelling_frame = LabelFrame(window, padx=24, pady=24)

        col_idx = df.columns.get_loc(LABEL_COLUMN_NAME)
        current_label = df.iloc[current_index, col_idx]
        try:
            if not np.isnan(current_label):
                proceed_next(df, labelling_frame)
        except TypeError:
            proceed_next(df, labelling_frame)

        column_index = df.columns.get_loc(selected_column)
        main_text = df.iloc[current_index, column_index]

        if not is_init:
            remaining_label = create_label(labelling_frame, f"Remaining: {current_index - start_index}/{end_index - start_index}")
            text_label = create_label(labelling_frame, main_text, wraplength=500)

            remaining_label.grid(row=0, column=1, padx=10, pady=5, sticky="E")
            text_label.grid(row=1, column=0, columnspan=2, padx=10, pady=5)

            if len(re.split("https?:\/\/", main_text)) > 1:
                text_label.config(fg="skyblue", cursor="hand2")
                font = Font(text_label, text_label.cget("font"))
                font.configure(underline=True)
                text_label.configure(font=font)
                text_label.bind("<Button-1>",
                                lambda e: webbrowser.open_new("http://" + re.split("https?:\/\/", main_text)[1]))

            def set_label_index_choice(label):
                col_idx = df.columns.get_loc(LABEL_COLUMN_NAME)
                df.iloc[current_index, col_idx] = label
                proceed_next(df, labelling_frame)

            for index, label in enumerate(labels):
                Button(labelling_frame, text=label, padx=20, pady=30, command=lambda label=label: set_label_index_choice(label)).grid(
                    row=(int(index / 3) + 2), column=int(index % 3), sticky='nesw')

            labelling_frame.place(relx=0.5, rely=0.7, anchor=CENTER)
        else:
            remaining_label.config(text=f"Remaining: {current_index - start_index}/{end_index - start_index}")
            text_label.config(text=main_text)

        global is_show_labeling_tool
        is_show_labeling_tool = True
        is_init = True
    except KeyError:
        pass


def proceed_next(df: pd.DataFrame, frame: LabelFrame):
    global current_index, end_index
    if current_index > end_index:
        messagebox.showinfo(message="You've reached the end of your settings. Program will close after this message.")
        exit(0)

    current_index += 1

    col_idx = df.columns.get_loc(LABEL_COLUMN_NAME)
    current_label = df.iloc[current_index, col_idx]
    try:
        if not np.isnan(current_label):
            proceed_next(df, frame)
        else:
            save_setting_to_file()
            save_current_data_frame(df)
            show_labeling_tool(df)
    except TypeError:
        save_setting_to_file()
        save_current_data_frame(df)
        show_labeling_tool(df)


def load_label():
    try:
        with open("labels.txt", "r") as file:
            contents = file.readlines()
            global labels
            for label in contents:
                labels.append(label.upper().split("\n")[0])
    except FileNotFoundError:
        messagebox.showerror(message="Please provide labels.txt file containing label.")


def save_setting_to_file():
    global selected_column, start_index, end_index, current_index
    with open("setting.conf", "w") as file:
        file.write(f"COLUMN={selected_column}\n")
        file.write(f"START={start_index}\n")
        file.write(f"END={end_index}\n")
        file.write(f"CURRENT={current_index}")


def read_settings_from_file():
    global selected_column, start_index, end_index, current_index
    try:
        with open("setting.conf", "r") as file:
            contents = file.readlines()

            selected_column = contents[0].split("=")[1].split("\n")[0]
            start_index = int(contents[1].split("=")[1].split("\n")[0])
            end_index = int(contents[2].split("=")[1].split("\n")[0])
            current_index = int(contents[3].split("=")[1].split("\n")[0])

            if current_index > end_index:
                messagebox.showinfo(message="Please edit end_index or start_index in setting.conf to continue.")
                exit(0)

    except FileNotFoundError:
        print("Config files does not exist.")


def save_current_data_frame(df: pd.DataFrame):
    df.to_csv("data.csv")


def create_label(main: Tk, text: str, **kwargs):
    label = Label(main, text=text, **kwargs)
    return label


def create_drop_down(main: Tk, choices: list, user_choice):
    column_options = OptionMenu(main, user_choice, *choices)
    return user_choice, column_options


def create_button(main: Tk, button_text: str, func: Callable):
    button = Button(main, text=button_text, command=func)
    return button


def create_entry(main: Tk, variable):
    entry = Entry(main, textvariable=variable)
    return entry


window.withdraw()
dataset = ask_for_file()
load_label()
window.wm_deiconify()
setting_frame(dataset)
show_labeling_tool(dataset)

window.mainloop()
