import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
from datetime import datetime
import os

class TodoApp:
    """
    A comprehensive To-Do List application built using Tkinter.
    Features include: quick entry, priority levels (P1, P2, P3),
    due dates, multiple lists (Projects), task persistence (via JSON),
    and a simplified UI for managing task details.
    """
    
    DATA_FILE = 'tasks.json'
    
    def __init__(self, master):
        self.master = master
        master.title("My Productivity Hub (Tkinter Todo)")
        master.geometry("800x600")
        
        # Load tasks from file or initialize
        self.tasks = self._load_tasks()
        self.current_list = "Inbox"
        self.priority_colors = {
            "P1": "red", "P2": "orange", "P3": "gold", "Done": "gray"
        }
        
        # Configure a modern theme
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Custom style for the Treeview rows (for priority coloring)
        self.style.configure("P1.Treeview", background="lightpink")
        self.style.configure("P2.Treeview", background="lightyellow")
        self.style.configure("P3.Treeview", background="lightcyan")
        self.style.configure("Done.Treeview", background="lightgray", foreground="darkgray")
        self.style.map('Done.Treeview', background=[('selected', 'gray')])

        # === Layout Frames ===
        self.main_frame = ttk.Frame(master, padding="10 10 10 10")
        self.main_frame.pack(fill='both', expand=True)
        
        # Configure grid weights for resizing
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(2, weight=1)
        
        # === 1. Quick Entry and List Selector (Top Row) ===
        header_frame = ttk.Frame(self.main_frame)
        header_frame.grid(row=0, column=0, sticky='ew', pady=(0, 10))
        
        self.list_selector = ttk.Combobox(header_frame, values=self._get_all_list_names(), state="readonly", width=15)
        self.list_selector.set(self.current_list)
        self.list_selector.pack(side='left', padx=(0, 10))
        self.list_selector.bind("<<ComboboxSelected>>", self._switch_list)
        
        self.add_list_btn = ttk.Button(header_frame, text="+ New List", command=self._add_new_list)
        self.add_list_btn.pack(side='left', padx=(0, 20))

        self.task_entry = ttk.Entry(header_frame, font=('Inter', 12))
        self.task_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        self.task_entry.bind('<Return>', lambda event: self.add_task())
        
        self.add_btn = ttk.Button(header_frame, text="Add Task", command=self.add_task)
        self.add_btn.pack(side='left')

        # === 2. Controls and Filters (Second Row) ===
        controls_frame = ttk.Frame(self.main_frame)
        controls_frame.grid(row=1, column=0, sticky='ew', pady=(0, 10))
        
        ttk.Button(controls_frame, text="Mark Complete", command=self.mark_complete).pack(side='left', padx=5)
        ttk.Button(controls_frame, text="Edit Details", command=self.edit_task_details).pack(side='left', padx=5)
        ttk.Button(controls_frame, text="Delete Task", command=self.delete_task, style='Danger.TButton').pack(side='right', padx=5)

        # Style for the delete button
        self.style.configure('Danger.TButton', foreground='red')

        # === 3. Task Treeview (Main Task Display) ===
        
        # Treeview setup
        self.tree = ttk.Treeview(self.main_frame, columns=('due', 'priority', 'status'), show='headings')
        self.tree.grid(row=2, column=0, sticky='nsew')
        
        # Define headings
        self.tree.heading('#0', text='Task Title')
        self.tree.heading('due', text='Due Date', anchor='w')
        self.tree.heading('priority', text='P', anchor='center')
        self.tree.heading('status', text='Status', anchor='center')
        
        # Define column widths
        self.tree.column('#0', width=450, stretch=tk.YES)
        self.tree.column('due', width=100, anchor='w')
        self.tree.column('priority', width=40, anchor='center')
        self.tree.column('status', width=70, anchor='center')
        
        # Bind double-click to edit details
        self.tree.bind('<Double-1>', lambda event: self.edit_task_details())

        # Scrollbar
        vsb = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.tree.yview)
        vsb.grid(row=2, column=0, sticky='nse', padx=(0, 0))
        self.tree.configure(yscrollcommand=vsb.set)
        
        # Initial population of the treeview
        self.refresh_task_view()

    def _get_all_list_names(self):
        """Returns a list of all unique project/list names."""
        list_names = {"Inbox"}
        for task in self.tasks:
            list_names.add(task.get('list_name', 'Inbox'))
        return sorted(list(list_names))

    def _switch_list(self, event=None):
        """Changes the current list view based on the combobox selection."""
        new_list = self.list_selector.get()
        if new_list and new_list != self.current_list:
            self.current_list = new_list
            self.refresh_task_view()

    def _add_new_list(self):
        """Prompts the user to add a new project/list."""
        new_list_name = simpledialog.askstring("New Project/List", "Enter the name for the new list:", parent=self.master)
        if new_list_name and new_list_name not in self._get_all_list_names():
            # Add the new list name to the combobox values
            current_values = list(self.list_selector['values'])
            current_values.append(new_list_name)
            self.list_selector['values'] = sorted(current_values)
            self.list_selector.set(new_list_name)
            self.current_list = new_list_name
            self.refresh_task_view()
            messagebox.showinfo("Success", f"List '{new_list_name}' created and selected.")

    def add_task(self):
        """
        Adds a new task from the quick entry bar.
        Includes a very simple simulation of NLP for dates and priority.
        """
        title = self.task_entry.get().strip()
        if not title:
            return

        # Simple NLP simulation: Check for keywords
        priority = "P3"
        due_date = ""
        
        # Check for Priority
        if any(keyword in title.lower() for keyword in ["p1", "priority 1", "high"]):
            priority = "P1"
        elif any(keyword in title.lower() for keyword in ["p2", "priority 2", "medium"]):
            priority = "P2"
            
        # Check for Due Date (very basic simulation)
        today = datetime.now().strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        
        if "today" in title.lower():
            due_date = today
        elif "tomorrow" in title.lower():
            due_date = tomorrow
        
        # Remove keywords from title (simplified)
        title = title.replace("p1", "").replace("p2", "").replace("high", "").replace("medium", "").strip()
        
        new_task = {
            'id': datetime.now().strftime('%Y%m%d%H%M%S%f'), # Unique ID
            'title': title,
            'due_date': due_date,
            'priority': priority,
            'is_done': False,
            'notes': '',
            'is_recurring': False,
            'list_name': self.current_list
        }
        
        self.tasks.append(new_task)
        self.task_entry.delete(0, tk.END)
        self._save_tasks()
        self.refresh_task_view()

    def mark_complete(self):
        """Marks the selected task as complete/incomplete."""
        selected_item = self.tree.focus()
        if not selected_item:
            return

        task_id = self.tree.item(selected_item, 'values')[3]
        
        for task in self.tasks:
            if task['id'] == task_id:
                task['is_done'] = not task['is_done'] # Toggle status
                self._save_tasks()
                self.refresh_task_view()
                return

    def delete_task(self):
        """Deletes the selected task."""
        selected_item = self.tree.focus()
        if not selected_item:
            return
            
        task_id = self.tree.item(selected_item, 'values')[3]
        
        # Find the task index
        task_index = next((i for i, task in enumerate(self.tasks) if task['id'] == task_id), None)
        
        if task_index is not None:
            del self.tasks[task_index]
            self._save_tasks()
            self.refresh_task_view()

    def edit_task_details(self):
        """Opens a new window to edit selected task details (Date, Priority, Notes, Recurring)."""
        selected_item = self.tree.focus()
        if not selected_item:
            return
            
        task_id = self.tree.item(selected_item, 'values')[3]
        
        # Find the task object
        task = next((t for t in self.tasks if t['id'] == task_id), None)
        if not task:
            return

        # --- Details Edit Window Setup ---
        edit_window = tk.Toplevel(self.master)
        edit_window.title(f"Edit Task: {task['title'][:30]}...")
        edit_window.geometry("400x450")
        edit_window.transient(self.master) # Make it modal
        edit_window.grab_set()

        frame = ttk.Frame(edit_window, padding="10")
        frame.pack(fill='both', expand=True)

        # Title
        ttk.Label(frame, text="Title:", font=('Inter', 10, 'bold')).pack(anchor='w', pady=(5, 0))
        title_var = tk.StringVar(value=task['title'])
        ttk.Entry(frame, textvariable=title_var, width=50).pack(fill='x', pady=(0, 10))

        # Due Date
        ttk.Label(frame, text="Due Date (YYYY-MM-DD):", font=('Inter', 10, 'bold')).pack(anchor='w', pady=(5, 0))
        due_date_var = tk.StringVar(value=task['due_date'])
        ttk.Entry(frame, textvariable=due_date_var, width=50).pack(fill='x', pady=(0, 10))
        
        # Priority
        ttk.Label(frame, text="Priority Level:", font=('Inter', 10, 'bold')).pack(anchor='w', pady=(5, 0))
        priority_var = tk.StringVar(value=task['priority'])
        ttk.Combobox(frame, textvariable=priority_var, values=['P1', 'P2', 'P3', ''], state='readonly', width=10).pack(anchor='w', pady=(0, 10))

        # Recurring
        recurring_var = tk.BooleanVar(value=task.get('is_recurring', False))
        ttk.Checkbutton(frame, text="Recurring Task (Placeholder)", variable=recurring_var).pack(anchor='w', pady=(5, 10))
        
        # Notes / Subtasks (Text Area)
        ttk.Label(frame, text="Notes / Subtasks (use bullet points or checklist format):", font=('Inter', 10, 'bold')).pack(anchor='w', pady=(5, 0))
        notes_text = tk.Text(frame, height=8, width=40)
        notes_text.insert(tk.END, task.get('notes', ''))
        notes_text.pack(fill='both', expand=True, pady=(0, 10))

        def save_and_close():
            """Saves changes and closes the edit window."""
            task['title'] = title_var.get()
            task['due_date'] = due_date_var.get()
            task['priority'] = priority_var.get()
            task['is_recurring'] = recurring_var.get()
            task['notes'] = notes_text.get('1.0', tk.END).strip()
            
            # Simple validation for due date format
            if task['due_date'] and not self._is_valid_date(task['due_date']):
                messagebox.showerror("Error", "Due Date must be in YYYY-MM-DD format or left empty.")
                return

            self._save_tasks()
            self.refresh_task_view()
            edit_window.destroy()

        ttk.Button(frame, text="Save Changes", command=save_and_close).pack(pady=10)

    def _is_valid_date(self, date_str):
        """Helper to validate date format."""
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def refresh_task_view(self):
        """Clears and repopulates the Treeview based on the current list and sorting."""
        
        # Clear existing items
        for i in self.tree.get_children():
            self.tree.delete(i)
            
        # Filter tasks for the current list
        filtered_tasks = [t for t in self.tasks if t.get('list_name', 'Inbox') == self.current_list]

        # Sort: Incomplete tasks first, then by priority (P1 > P2 > P3), then by due date
        def sort_key(task):
            done_status = task['is_done']
            
            # Map priority to a number for sorting (P1=1, P2=2, P3=3)
            priority_map = {'P1': 1, 'P2': 2, 'P3': 3, '': 4}
            priority_num = priority_map.get(task.get('priority', ''), 4)
            
            # Use a sentinel value for dates to ensure empty dates sort last
            due_date = task.get('due_date')
            date_sort_key = datetime.strptime(due_date, '%Y-%m-%d') if due_date else datetime.max

            return (done_status, priority_num, date_sort_key)

        sorted_tasks = sorted(filtered_tasks, key=sort_key)
        
        # Insert tasks into the Treeview
        for task in sorted_tasks:
            status_text = "Done" if task['is_done'] else "Pending"
            priority_tag = "Done" if task['is_done'] else task.get('priority', 'P3')
            
            # Values are (due_date, priority, status_text, id)
            values = (
                task.get('due_date', ''),
                task.get('priority', ''),
                status_text,
                task['id']
            )
            
            self.tree.insert(
                '', 
                'end', 
                text=task['title'], 
                values=values, 
                tags=(priority_tag, 'Treeview')
            )
            
        # Update the list selector with all available lists
        self.list_selector['values'] = self._get_all_list_names()
        
    def _load_tasks(self):
        """Loads tasks from the JSON file."""
        if os.path.exists(self.DATA_FILE):
            try:
                with open(self.DATA_FILE, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                messagebox.showerror("Error", "Could not read tasks.json. Starting with a blank list.")
                return []
        return []

    def _save_tasks(self):
        """Saves current tasks to the JSON file."""
        try:
            with open(self.DATA_FILE, 'w') as f:
                json.dump(self.tasks, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save tasks: {e}")

if __name__ == '__main__':
    root = tk.Tk()
    app = TodoApp(root)
    root.mainloop()
