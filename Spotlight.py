import customtkinter as ctk
from tkinter import filedialog as fd
import pandas as pd
import Spotlight_Search as search

pd.set_option('display.max_columns', None)

ctk.set_appearance_mode("System")

ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self, *args, **kwargs):
        # Creates initial window, which asks for a file name.
        super().__init__(*args, **kwargs)
        self.geometry("465x348")
        self.grid_rowconfigure([0,1,2,3,4,5,6,7,8],weight=1)
        self.grid_columnconfigure([0,1,2],weight=1)
        self.worksheet_exists = False
        self.column_exists = False
        self.title("Spotlight")
        self.file = ctk.StringVar()
        self.target_name = ctk.StringVar()
        self.file_button = ctk.CTkButton(self,
                                  text = "Select a file",
                                  command= self.change_file)
        self.file_button.grid(row= 0, 
                              column= 0, 
                              columnspan=3)

        self.file_lable = ctk.CTkLabel(self,
                                       text="Currently Selected File: None")
        self.file_lable.grid(row = 1,
                             column = 0,
                             columnspan=3)

        self.is_pattern = False
        self.target_exists = False
        self.run_before = False
        self.is_excel = False
        self.len_previous = False

        self.run = ctk.CTkButton(self,text='Search',
                            state=ctk.DISABLED)
        self.run.grid(column = 0, 
                      row = 7,
                      columnspan = 3)
        values= ['Pattern','Exact Match','Length','Nulls']
        self.search_type = ctk.CTkOptionMenu(self, values = ['-- Select Search Type --'], command= self.set_run_button)
        self.search_type.configure(values=values)
        self.search_type.grid(row = 2,column=0,columnspan = 3)

    def set_run_button(self, search_type):
        if self.target_exists:
            self.target.destroy()
            self.target_label.destroy()
            self.target_exists = False
        if self.len_previous:
            self.len_previous = False
            self.operator.destroy()
        match search_type:
            case 'Pattern':
                  self.is_pattern = True
                  self.run.configure(command = self.search_strings,state = ctk.DISABLED)
                  self.create_search_box()
            case 'Exact Match':
                  self.is_pattern = False
                  self.run.configure(command = self.search_strings,state = ctk.DISABLED)
                  self.create_search_box()
            case 'Length':
                  self.len_previous = True
                  self.run.configure(command = self.search_lengths,state = ctk.DISABLED)
                  self.create_search_box()
                  self.operator = ctk.CTkOptionMenu(self, values=["Select your operator"], dynamic_resizing= True, command= self.set_opperator)
                  self.operator.grid(row=5 if self.is_excel else 4, column = 0, columnspan = 3)
                  self.operator.configure(values = ["Results more than target", 
                                                    "Results more than or equal to target", 
                                                    "Results equal to target", 
                                                    "Results less than or equal to target",
                                                    "Results less than target"])
            case 'Nulls':
                  self.run.configure(command = self.search_nulls,state = ctk.DISABLED)
            case _:
                  self.run.configure(command = self.search_nulls,state = ctk.DISABLED)
            
    def create_search_box(self):
        self.target_exists = True
        self.target = ctk.CTkEntry(self,
                                   textvariable=self.target_name,
                                   placeholder_text="Search Target")
        self.target.grid(column = 1, 
                         row = (6 if self.len_previous else 5) if self.is_excel else (5 if self.len_previous else 4))
        self.target_label = ctk.CTkLabel(self,
                                         text="Search Target:")
        self.target_label.grid(column=0,
                               row=(6 if self.len_previous else 5) if self.is_excel else (5 if self.len_previous else 4))
            
    def set_opperator(self,option):
        match option:
            case "Results more than target":
                self.len_operator = lambda target,record: target < record
            case "Results more than or equal to target":
                self.len_operator = lambda target,record: target <= record
            case "Results equal to target":
                self.len_operator = lambda target,record: target == record
            case "Results less than or equal to target":
                self.len_operator = lambda target,record: target >= record
            case "Results less than target":
                self.len_operator = lambda target,record: target > record
            case _:
                pass

    def change_file(self):
        file = fd.askopenfilename(filetypes=(('Compatible File',['*.xlsx','*.csv']),))
        # If a file is selected, choses the buttons need to select the specific column in the table that has the data.
        # This is obtained from the file column in the results file, in the format File/Worksheet:Column for excel files (.xlsx),
        # or File:Column for CSVs (.csv), obtained from the profiler.
        if file:
            self.file_lable.configure(text = f"Currently Selected File: {file.split('/')[-1]}")

            if self.run_before:
                if self.column_exists:
                    self.column_selector.destroy()
                    self.column_label.destroy()
                if self.worksheet_exists :
                    self.worksheet_selector.destroy()
                    self.worksheet_label.destroy()
            self.file = file
            self.run_before = True
            if file.split('.')[-1] == "xlsx":
                df = pd.read_excel(file,sheet_name=None)
                self.worksheet = ctk.StringVar()

                self.worksheet_selector = ctk.CTkOptionMenu(self,
                                                            values= None,
                                                            variable=self.worksheet,
                                                            command=self.select_column)
                self.worksheet_selector.grid(column= 1, 
                                             row = 3)
                self.worksheet_selector.configure(require_redraw= True, 
                                                  values= df.keys())
                self.worksheet_label = ctk.CTkLabel(self,
                                                    text="Select Worksheet:")
                self.worksheet_label.grid(column=0,
                                          row=3)

                self.is_excel = True
                self.worksheet_exists = True
                self.column_exists = False
            elif file.split('.')[-1] == "csv":
                self.column_exists = True
                self.worksheet_exists = False
                df = pd.read_csv(file)
                self.column = ctk.StringVar()

                self.column_selector = ctk.CTkOptionMenu(self,
                                                            values=None,
                                                            variable= self.column,
                                                            command= self.activate_button)
                self.column_label = ctk.CTkLabel(self,text="Select Column:",)
                self.column_label.grid(row = 3, 
                                       column= 0)
                self.column_selector.grid(row=3, 
                                          column = 1, 
                                          columnspan= 2)
                self.column_selector.configure(require_redraw= True, 
                                               values= df.columns)

                self.run.configure(state=ctk.ACTIVE)
                self.is_excel = False
            
    def select_column (self,worksheet):
        self.column_exists = True
        file = self.file
        # When an excel file is selected, the file needs a worksheet to be selected. This allows the columns be selected after the worsheet, from 
        # just the ones in the worksheet. 
        file:pd.DataFrame = pd.read_excel(file,sheet_name=worksheet)
        self.column = ctk.StringVar()

        self.column = ctk.StringVar()
        self.column_label = ctk.CTkLabel(self,
                                            text="Select Column:")
        self.column_label.grid(row=4,
                                column=0)
        self.column_selector = ctk.CTkOptionMenu(self,
                                                values=file.columns,
                                                variable=self.column)
        self.column_selector.grid(row=4, 
                                    column=1)
        
        self.run.configure(state=ctk.ACTIVE)
    
    def activate_button(self,_):
        self.run.configure(state = ctk.ACTIVE)

    def search_nulls(self):
        if self.is_excel:
            results = search.shine_spotlight(
                None,
                path = self.file,
                column = str(self.column.get()),
                is_excel= self.is_excel,
                sheet_name = self.worksheet.get(),
                search_nulls = True
                )
        else:
            results = search.shine_spotlight(
                None,
                path = self.file,
                column = str(self.column.get()),
                is_excel = self.is_excel,
                search_nulls = True
                )
            
        self.clear(results)

    def search_strings (self):
        # Searches for all the rows that feature the target string, or one matching a pattern string if it is a pattern. Outputs all rows found.
        if self.is_excel:
            results = search.shine_spotlight(
                target = str(self.target_name.get()),
                path = self.file,
                column = str(self.column.get()),
                is_excel= self.is_excel,
                sheet_name = self.worksheet.get(),
                is_pattern = True
                )
        else:
            results = search.shine_spotlight(
                target = str(self.target_name.get()),
                path = self.file,
                column = str(self.column.get()),
                is_excel= self.is_excel,
                is_pattern = True
                )
        
        self.clear(results)

    def search_lengths(self):
        if self.is_excel:
            results = search.shine_spotlight(
                target = str(self.target_name.get()),
                path = self.file,
                column = str(self.column.get()),
                is_excel= self.is_excel,
                sheet_name = self.worksheet.get(),
                search_len = True,
                len_operator = self.len_operator
                )
        else:
            results = search.shine_spotlight(
                target = str(self.target_name.get()),
                path = self.file,
                column = str(self.column.get()),
                is_excel= self.is_excel,
                search_len = True,
                len_operator = self.len_operator
                )
            
        self.clear(results)

    def clear(self,results):
        # Deletes all the buttons and input areas to prevent users sending another search through.
        self.file_lable.destroy()
        self.search_type.destroy()
        if self.target_exists:
            self.target.destroy()
            self.target_label.destroy()
        self.file_button.destroy()
        self.column_selector.destroy()
        self.column_label.destroy()
        if self.file.split('.')[-1]=='xlsx':
            self.worksheet_selector.destroy()
            self.worksheet_label.destroy()
        self.run.destroy()
        self.direct = ctk.CTkLabel(self,text="Check Terminal for neater grid.").grid(column=0,row=9,columnspan=10)
        self.results = ctk.CTkLabel(self,text=results)
        self.results.grid(column=0,row=0,columnspan=10, rowspan = 10)
        if self.len_previous:
            self.operator.destroy()
        print(results) 

if __name__ == "__main__":
    app = App()
    app.mainloop()