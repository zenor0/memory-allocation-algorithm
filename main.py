import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import messagebox, simpledialog, Button, Entry, Label

import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

pid_counter = 0
class Process:
    def __init__(self, size, offset=0):
        global pid_counter
        self.index = pid_counter
        self.size = size
        self.offset = offset
        pid_counter += 1

    def __str__(self):
        return f"Process: size: {self.size}Kb, offset: {self.offset}"

class Partition:
    processes : list[Process]
    def __init__(self, size):
        self.size = size
        self.processes = []
        self.max_empty_size = size
        
    def reset(self):
        self.processes = []
        self.max_empty_size = self.size
        
    def update_max_empty_size(self):
        status_map = self.get_status_map()
        self.max_empty_size = 0
        max_empty_size = 0
        for i in range(self.size):
            if not status_map[i]:
                max_empty_size += 1
            else:
                max_empty_size = 0
            self.max_empty_size = max(self.max_empty_size, max_empty_size)
        logger.debug(f"Max empty size: {self.max_empty_size}")
        

    def allocate(self, process: Process):
            if process.size > self.max_empty_size:
                return False
            
            status_map = self.get_status_map()
            
            for i in range(self.size - process.size + 1):
                if not any(status_map[i:i+process.size]):
                    process.offset = i
                    break
            else:
                return False
            
            self.processes.append(process)
            status_map = self.get_status_map()
            
            self.update_max_empty_size()
            
    def deallocate(self, process_id):
        for i, p in enumerate(self.processes):
            if p.index == process_id:
                self.processes.pop(i)
                self.update_max_empty_size()
                return True
    
    def get_status_map(self):
        status_map = [False] * self.size
        for p in self.processes:
            for i in range(p.offset, p.offset + p.size):
                status_map[i] = True
        return status_map
        
    def __str__(self):
        return f"Partition: {self.size}Kb"

class MemoryAllocationSimulator:
    partitions : list[Partition]
    processes : list[Process]
    
    def __init__(self, master):
        self.master = master
        self.memory_size = 0
        self.partitions = []
        self.processes = []
        self.tasks = []
        self.alert_process = []
    
    def init_ui(self):
        self.__create_ui_grid()
        self.on_update_memory_view()
    
    def demo_data(self):
        self.memory_size = 300
        self.partitions = [Partition(100), Partition(140), Partition(40)]
        self.processes = []
        self.tasks = []
        
        self.tasks = [80, 30, 130, 25]
        self.on_update_memory_view()
        self.on_update_status_view()

    def on_delete(self, evt):
        w = evt.widget
        index = int(w.curselection()[0])
        value = w.get(index)
        self.deallocate_memory(int(value.split(' ')[1]))
        self.on_update_status_view()
    
    def on_select(self, evt):
        w = evt.widget
        index = int(w.curselection()[0])
        value = w.get(index)
        print(value.split(' ')[1])
        self.alert_process.append(int(value.split(' ')[1]))
        self.on_update_memory_view()
        self.alert_process.remove(int(value.split(' ')[1]))
        logger.info(f"Process {index} selected.")

    def on_delete_task(self, evt):
        w = evt.widget
        index = int(w.curselection()[0])
        value = w.get(index)
        self.tasks.remove(int(value.split(' ')[1]))
        self.on_update_status_view()

    def __create_ui_grid(self):
        self.master.title("Memory Allocation Simulator")
        mainframe = ttk.Frame(self.master, padding="3 3 12 12")
        mainframe.grid(column=0, row=0)
        # mainframe.columnconfigure(0, weight=1)
        # mainframe.rowconfigure(0, weight=1)
        
        self.canvas = tk.Canvas(mainframe, height=600, width=200, bg="white")
        self.canvas.grid(column=0, row=0, rowspan=100, columnspan=3 ,padx=10, pady=10)
        
        self.current_process_frame = tk.LabelFrame(mainframe, text="Current Process")
        self.current_process_frame.grid(column=3, row=0, sticky="n", padx=10, pady=10)
        self.current_process_list = tk.Listbox(self.current_process_frame, height=10, width=20)
        self.current_process_list.grid(column=0, row=0, sticky="n")
        self.current_process_list.bind('<<ListboxSelect>>', self.on_select)
        self.current_process_list.bind('<Double-1>', self.on_delete)
        
        
        self.process_frame = tk.LabelFrame(mainframe, text="Process size")
        self.process_frame.grid(column=3, row=1, sticky="n", padx=10, pady=10)
        self.entry_process_size = tk.Entry(self.process_frame)
        self.entry_process_size.bind('<Return>', self.push_task)
        self.entry_process_size.grid(column=0, row=0)
        
        self.push_button = tk.Button(self.process_frame, text="Push", command=self.push_task)
        self.push_button.grid(column=1, row=0)
        

        
        self.control_frame = tk.LabelFrame(mainframe, text="Control")
        self.control_frame.grid(column=3, row=3, padx=10, pady=10)
        
        self.algorithm_var = tk.StringVar()
        self.algorithm_var.set("First Fit")
        
        self.algorithm_menu = tk.OptionMenu(self.control_frame, self.algorithm_var, "First Fit", "Best Fit", "Worst Fit")
        self.algorithm_menu.grid(column=0, row=0, sticky="w")
        
        self.allocate_button = tk.Button(self.control_frame, text="Allocate", command=self.allocate_memory)
        self.allocate_button.grid(column=1, row=0)
        
        self.task_list_frame = tk.LabelFrame(mainframe, text="Task List")
        self.task_list_frame.grid(column=4, row=0, rowspan=3, sticky="n", padx=10, pady=10)
        self.task_list_frame.config(width=200, height=200)
        self.task_list = tk.Listbox(self.task_list_frame, height=10, width=20)
        self.task_list.grid(column=0, row=0, sticky="n")
        self.task_list.bind('<Double-1>', self.on_delete_task)
        
        
        self.config_frame = tk.LabelFrame(mainframe, text="Memory Configuration")
        self.config_frame.grid(column=4, row=1, rowspan=4, padx=10, pady=10)
        self.config_frame.config(width=200, height=200)
        
        Label(self.config_frame, text="Memory Size").grid(column=0, row=0, pady=5)
        self.memory_size_var = tk.Entry(self.config_frame)
        self.memory_size_var.grid(column=1, row=0, columnspan=3, pady=5)
        Label(self.config_frame, text="Partition Sizes").grid(column=0, row=1, pady=5)
        self.partition_var = Entry(self.config_frame)
        self.partition_var.grid(column=1, row=1, columnspan=3, pady=5)
        Button(self.config_frame, text="Update", command=self.get_initial_memory_setup).grid(column=2, row=2, pady=5)
        Button(self.config_frame, text="Demo", command=self.demo_data).grid(column=1, row=2, pady=5)
        Button(self.config_frame, text="Reset", command=self.reset).grid(column=3, row=2, pady=5)
        
        self.log_frame = tk.LabelFrame(mainframe, text="Log")
        self.log_frame.grid(column=3, row=10, columnspan=20, padx=10, pady=10)
        self.log_frame.config(width=500, height=100)
        self.log_text = tk.Text(self.log_frame, height=10, width=60)
        self.log_text.grid(column=0, row=0, sticky="n")
        
    def get_initial_memory_setup(self):
        partition_sizes_str = self.partition_var.get()
        partitions_vars = []
        for size in partition_sizes_str.split(' '):
            partitions_vars.append(int(size))
            
        self.partitions = []
        for size in partitions_vars:
            self.partitions.append(Partition(size))
        
        self.memory_size = sum(partitions_vars)

        if self.memory_size is None or any(i.size <= 0 for i in self.partitions):
            messagebox.showerror("Error", "Invalid input. Please provide valid memory and partition sizes.")
            self.master.destroy() 
            return

        self.on_update_memory_view()

    def push_task(self, event=None):
        input_task_list = []
        for task in self.entry_process_size.get().split(' '):
            input_task_list.append(int(task))
        # process_size = int(self.entry_process_size.get())
        
        for task in input_task_list:
            if task <= 0:
                messagebox.showerror("Error", "Process size must be greater than 0.")
                return
            self.tasks.append(task)
            self.task_list.insert(len(self.tasks), f"Task: {task} Kb")
        
        self.entry_process_size.delete(0, tk.END)
        self.log_text.insert(tk.END, f"[info] Task {input_task_list} pushed.\n")
        self.on_update_status_view()
        
    def on_update_memory_view(self):
        self.canvas.delete("all")
        width = 50
        gap = 5
        x, y = 50, 50
        for i, partition in enumerate(self.partitions):
            height = partition.size / self.memory_size * 500
            end_x, end_y = width, y + height
            self.canvas.create_rectangle(x, y, x + width, end_y, fill="lightblue", outline="black")
            self.canvas.create_text((x + x + width) / 2, (y + end_y) / 2, text=f"{partition.size}Kb", fill="black")
            
            # visualize the status_map. true for allocated, false for unallocated
            status_map = partition.get_status_map()
            prev_status = status_map[0]
            continuous_count = 0
            start_y = y
            for i, status in enumerate(status_map):
                if status != prev_status:
                    if not prev_status:
                        self.canvas.create_rectangle(x, start_y, x + width, start_y + continuous_count / partition.size * height, fill="lightblue", outline="black")
                    self.canvas.create_text((x + x + width) / 2, (start_y + start_y + continuous_count / partition.size * height) / 2, text=f"{continuous_count}Kb", fill="black")
                    
                    start_y += continuous_count / partition.size * height
                    continuous_count = 0
                    prev_status = status
                continuous_count += 1
                
                if i == len(status_map) - 1:
                    if not prev_status:
                        self.canvas.create_rectangle(x, start_y, x + width, start_y + continuous_count / partition.size * height, fill="lightblue", outline="black")
                    self.canvas.create_text((x + x + width) / 2, (start_y + start_y + continuous_count / partition.size * height) / 2, text=f"{continuous_count}Kb", fill="black")
                            
                
            
            for p in partition.processes:
                if p.index in self.alert_process:
                    self.canvas.create_rectangle(x, y + p.offset / partition.size * height, x + width, y + (p.offset + p.size) / partition.size * height, fill="red", outline="black")
                else:
                    self.canvas.create_rectangle(x, y + p.offset / partition.size * height, x + width, y + (p.offset + p.size) / partition.size * height, fill="lightgreen", outline="black")
                self.canvas.create_text((x + x + width) / 2, (y + p.offset / partition.size * height + y + (p.offset + p.size) / partition.size * height) / 2, text=f"{p.size}Kb", fill="black")
            
            y = end_y + gap

    def on_update_status_view(self):
        self.task_list.delete(0, tk.END)
        for i, task in enumerate(self.tasks):
            self.task_list.insert(i, f"Task: {task} Kb")
            
        self.current_process_list.delete(0, tk.END)
        for i, process in enumerate(self.processes):
            self.current_process_list.insert(i, f"Process {process.index} : {process.size}Kb")
            
    def deallocate_memory(self, process_id):
        for partition in self.partitions:
            if partition.deallocate(process_id) is not None:
                for i, process in enumerate(self.processes):
                    if process.index == process_id:
                        self.processes.pop(i)
                        
                self.on_update_memory_view()
                self.on_update_status_view()

    def allocate_memory(self):
        process_size = int(self.tasks[0])
        self.tasks.pop(0)
        algorithm = self.algorithm_var.get()

        if process_size <= 0:
            self.log_text.insert(tk.END, f"[error] Process size must be greater than 0.\n")
            # messagebox.showerror("Error", "Process size must be greater than 0.")
            return

        if algorithm == "Best Fit":
            block_index = self.best_fit(process_size)
        elif algorithm == "First Fit":
            block_index = self.first_fit(process_size)
        elif algorithm == "Worst Fit":
            block_index = self.worst_fit(process_size)
        else:
            messagebox.showerror("Error", "Invalid allocation algorithm.")
            return

        if block_index is not None:
            self.partitions[block_index].allocate(Process(process_size))
            self.processes.append(self.partitions[block_index].processes[-1])
        else:
            self.log_text.insert(tk.END, f"[error] Memory allocation failed. No suitable block found.\n")
            # messagebox.showinfo("Info", "Memory allocation failed. No suitable block found.")
        self.on_update_memory_view()
        self.on_update_status_view()

    def best_fit(self, process_size):
        fit_partitions = [partition for partition in self.partitions if partition.max_empty_size >= process_size]
        if not fit_partitions:
            return None
        
        min_index, min_size = 0, fit_partitions[0].max_empty_size
        for index, partition in enumerate(fit_partitions):
            if partition.max_empty_size < min_size:
                min_index, min_size = index, partition.max_empty_size
        return self.partitions.index(fit_partitions[min_index])

    def first_fit(self, process_size):
        for index, partition in enumerate(self.partitions):
            if partition.max_empty_size >= process_size:
                return index

        return None



    def worst_fit(self, process_size):
        max_index, max_size = None, 0
        for index, partition in enumerate(self.partitions):
            if partition.max_empty_size >= process_size and partition.max_empty_size > max_size:
                max_index, max_size = index, partition.max_empty_size
        

        return max_index

    def reset(self):
        self.processes = []
        self.tasks = []
        
        self.task_list.delete(0, tk.END)
        self.current_process_list.delete(0, tk.END)
        for partition in self.partitions:
            partition.reset()
        self.on_update_memory_view()
        self.on_update_status_view()


if __name__ == "__main__":

    root = tk.Tk()
    app = MemoryAllocationSimulator(root)
    app.init_ui()
    root.mainloop()