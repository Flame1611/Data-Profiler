import re
import pandas as pd
from tkinter import filedialog as fd
import customtkinter as ctk
import os
from time import sleep

ctk.set_appearance_mode("System")

ctk.set_default_color_theme("blue")

results_folder = "Results"

class App(ctk.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Profiler")
        self.geometry("523x253")
        self.grid_rowconfigure([0,1,2],weight=1)
        self.grid_columnconfigure([0,1],weight=1)
        self.folder_label = ctk.CTkLabel(self,
                                         text= 'Folder with files:')
        
        self.folder_label.grid(row=0,
                               column=0,
                               padx = 5)

        self.folder_button = ctk.CTkButton(self, 
                                    text="Select a folder...",
                                    command=self.get_folder)
        
        self.folder_button.grid(row=0,
                        column=1,
                        padx = 5)
        
        self.folder_display = ctk.CTkLabel(self, text= 'Current folder is not selected')
        self.folder_display.grid(row=1,column=0,columnspan=2)

        self.run = ctk.CTkButton(self, 
                                 text= "Run", 
                                 command= self.run_funct)
        self.run.grid(row=2,
                      column=0,
                      columnspan=2)

    def get_folder(self):
        self.folder = fd.askdirectory(mustexist=True)
        if self.folder != "":
            self.folder_display.configure(text = f'Current folder location is "{self.folder}"')
        return self.folder
	
    def run_funct(self):
        if self.folder != "":
            filename = self.folder
            create_files(filename,results_folder)
            self.result = ctk.CTkLabel(self,text= 'Done! Automatically closing in 15 seconds...')
            self.result.grid(row=4,
		    				 column=0,
	    					 columnspan=2)
            sleep(2)
            exit()			

samples = 1000 #1000 is the initial value I was asked to test, but Im leaving as variable to change easily

def identify_files(cwd:str) -> list[str]:
	folder = ''
	if folder != '':
		filename = os.listdir(cwd+folder) #Files on which it works
		filename = [file for file in filename if file.split('.')[-1] in ['csv','xlsx']]
	else:
		filename = os.listdir(cwd)
		filename = [file for file in filename if file.split('.')[-1] in ['csv','xlsx']]
	return filename

# File must have only one header row
# To get an average files must contain exclusively numeric data in a column, except for the header,
# as it would be impossible for it to 100% accurately judge if non-numeric data is meant to be in a column.

def clear_blanks(df:pd.DataFrame) -> pd.DataFrame:
	# Sets all values equivalent to nothing to None, and drops empty columns created from data overflowing
	for i in df:
		df[i] = df[i].apply(lambda x: str(x).strip())
	none_regex = re.compile(r'^nan$')
	unnamed_regex = re.compile(r'^Unnamed:')
	df = df.replace('',None)
	df = df.replace(none_regex,None,regex=True)
	df = df.dropna(axis=0,how='all')
	df.drop(df.columns[df.columns.str.contains(unnamed_regex,regex=True)],axis = 1, inplace = True)
	return df

def type_colums(df:pd.DataFrame) -> pd.DataFrame:
	#Ensures all columns are of an apporopriate type where applicable
	for column in df:
		try:
			df[column] = pd.to_datetime(df[column])
			df[column] = df[column].astype(str)
			df[column] = df[column].replace('NaT','')
		except:
			try:
				df[column] = pd.to_numeric(df[column])
			except ValueError:
				df[column] = df[column].astype(str)
	return df

def format_df(df: pd.DataFrame) -> pd.DataFrame:
	df =  clear_blanks(type_colums(df))
	return df

def pattern_preparation(dataframe:pd.DataFrame, sample_size:int, metric_type:str, filename:str) -> pd.DataFrame:
	pattern_analysis = pd.DataFrame()
	# Method for patterns and unique are the same, with pattern just replacing all alphanumeric characters with X or 9.
	# It was kept in the same function to maintain readability
	if metric_type == 'Pattern Analysis':
		alpha_regex = re.compile(r'([a-zA-Z])')
		numeric_regex = re.compile(r'([0-9])')
		pattern_alpha = 'X'
		pattern_numeric = '9'
		dataframe = dataframe.replace(alpha_regex,pattern_alpha,regex=True)
		dataframe = dataframe.replace(numeric_regex,pattern_numeric,regex=True)
	# Collects all similar examples and counts how many exist of the same type
	for column in dataframe.columns:
		group = dataframe.groupby(column)
		group = group.size()
		group = group.sort_values(ascending=False)
		# Stops excessivly long lists if many unique examples exist by only using the top "sample_size" units, with the default being 1000
		if len(group) > sample_size:
			keys = group.keys()
			for i in range(sample_size):
				key = keys[i]
				pattern_analysis = pattern_count(pattern_analysis, group, key, metric_type, filename, column)
		else:
			for key in group.keys():
				pattern_analysis = pattern_count(pattern_analysis, group, key, metric_type, filename, column)
	pattern_analysis = pattern_analysis.iloc[::-1]
	return pattern_analysis

def pattern_count(pattern_analysis:pd.DataFrame, group:dict[str:int], key:str, metric_type:str, filename:str, column:str) -> pd.DataFrame:
	# "metric_value" is both the key of the dictionary, and also the contents of the cell, whereas "metric_count" is the amount of types it appears
	metric_value = key
	metric_count = group[key]
	new_row = pd.DataFrame({'File Name':filename,
							'Metric Type':metric_type,
							'Column' : column,
							'Metric value': metric_value,
							'Count' : metric_count},
							index=[0])
	pattern_analysis = pd.concat([new_row,pattern_analysis.loc[:]]).reset_index(drop=True)
	return pattern_analysis

def single_vals(df: pd.DataFrame, filename:str) -> pd.DataFrame:
	# Performs an analysis that returns a single value for each column as a whole, as opposed to a value for each individual record.
	column_stats = pd.DataFrame()
	for column in df:
		lengths = df[column].apply(lambda x: len(str(x)))
		column_data = pd.DataFrame({'File Name':filename,
							'Column' : column,
							'Max Length':lengths.max(),
							'Min Length':lengths.min(),
							'Nulls': len(df[column].loc[df[column].isna()]),
							'Non-nulls': len(df[column].loc[df[column].notna()])},
							index=[0])
		column_stats = pd.concat([column_data,column_stats.loc[:]]).reset_index(drop=True)

	return column_stats

def minmax_vals(df:pd.DataFrame, filename:str) -> pd.DataFrame:
	# Collects the largest and smallest values in a column, with words being valued alphabetically, then length wise.
	df = type_colums(df)
	extreme_values = pd.DataFrame()
	for column in df:
		min_row = pd.DataFrame({'File Name':filename,
							'Metric Type':'Min Value',
							'Column' : column,
							'Metric value': df[column].min(skipna=True)},
							index=[0])
		max_row = pd.DataFrame({'File Name':filename,
							'Metric Type':'Max Value',
							'Column' : column,
							'Metric value': df[column].max(skipna=True)},
							index=[0])		
		extreme_values = pd.concat([min_row,extreme_values.loc[:]]).reset_index(drop=True)
		extreme_values = pd.concat([max_row,extreme_values.loc[:]]).reset_index(drop=True)
	return extreme_values

def produce_examples(dataframe:pd.DataFrame, unique_values: pd.DataFrame) -> list:
	# Grabs the first example in the column, which should be the biggest
	examples = []
	for column in unique_values['Column']:
		slice = dataframe["Metric value"][dataframe['Column']==column].reset_index(drop = True)
		if len(slice) > 0:
			examples.append(slice[0])
		else:
			examples.append(slice)
	return examples

def headline_results(value:pd.DataFrame, extreme:pd.DataFrame, unique:pd.DataFrame, pattern:pd.DataFrame) -> pd.DataFrame:
	value['Max Value'] = extreme['Metric value'][(extreme['Metric Type'] == 'Max Value')].reset_index(drop = True)
	value['Min Value'] = extreme['Metric value'][(extreme['Metric Type'] == 'Min Value')].reset_index(drop = True)
	value['Pattern Example'] = produce_examples(pattern, value)
	value['Unique Example'] = produce_examples(unique, value)
	return value

def numerical_results(original_dataframe: pd.DataFrame,  filename: str) -> pd.DataFrame:
	df = pd.DataFrame()
	# Only performs operations on numeric data
	for column in original_dataframe:
		if original_dataframe[column].dtype in ['int64','float64']:
			means  = original_dataframe[column].mean()
			modes = original_dataframe[column].mode(dropna=False)
			medians = original_dataframe[column].median()
			averages = pd.DataFrame({
				"File Name" : [f'{filename}: {column}'],
				"Mean" : [means],
				"Mode" : [modes[0]],
				"Median" : [medians]
				})
			df = pd.concat([averages,df])
	return df

def parse_worksheets(data:pd.DataFrame|dict[str:pd.DataFrame], filename: str) -> pd.ExcelFile:
	top_unique = pattern_analysis = unique_values = extreme_values = headlines = top_1000_unique_and_patterns = numerical_analysis = None
	# Reading an excel file returns a dictionary, this reads all the sheets of a file and performs all necessary operations on them.
	# This treats all the sheets as seperate files inside of the excel file.
	if type(data) == dict:
		top_unique,pattern_analysis,unique_values,extreme_values,headlines,top_1000_unique_and_patterns,numerical_analysis = [],[],[],[],[],[],[]
		for df in data:
			if not data[df].empty:
				data[df] = format_df(data[df])
				pattern_analysis.append(pattern_preparation(data[df],samples,'Pattern Analysis',f'{filename} : {df}'))
				top_unique.append(pattern_preparation(data[df],samples,'Top Unique',f'{filename} : {df}'))
				unique_values.append(single_vals(data[df],f'{filename} : {df}'))
				extreme_values.append(minmax_vals(data[df],f'{filename} : {df}'))
				unique_vals = unique_values
				headlines.append(headline_results(unique_vals[-1],extreme_values[-1],top_unique[-1],pattern_analysis[-1]))
				top_1000_unique_and_patterns.append(pd.concat([top_unique[-1],pattern_analysis[-1]]).reset_index(drop= True))
				numerical_analysis.append(numerical_results(data[df],f'{filename} : {df}'))
		# Combines the operations performed on the sheets into one set of list
		headlines = pd.concat(headlines).reset_index(drop=True)
		pattern_analysis = pd.concat(pattern_analysis).reset_index(drop=True)
		top_unique = pd.concat(top_unique).reset_index(drop=True)
		unique_values = pd.concat(unique_vals).reset_index(drop=True)
		extreme_values = pd.concat(extreme_values).reset_index(drop=True)
		top_1000_unique_and_patterns = pd.concat(top_1000_unique_and_patterns).reset_index(drop=True)
		match len(numerical_analysis):
			case 1:
				numerical_analysis = numerical_analysis[0]
			case 0:
				pass
			case _:
				numerical_analysis = pd.concat(numerical_analysis).reset_index(drop=True)
	else:
		if not data.empty:
				data = format_df(data)
				pattern_analysis = pattern_preparation(data,samples,'Pattern Analysis',f'{filename}')
				top_unique = pattern_preparation(data,samples,'Top Unique',f'{filename}')
				unique_values = single_vals(data,f'{filename}')
				unique_vals = unique_values
				extreme_values = minmax_vals(data,f'{filename}')
				headlines = headline_results(unique_vals,extreme_values,top_unique,pattern_analysis)
				top_1000_unique_and_patterns = pd.concat([top_unique,pattern_analysis]).reset_index(drop= True)
				numerical_analysis = numerical_results(data,f'{filename}')	
	return top_unique,pattern_analysis,unique_values,extreme_values,headlines,top_1000_unique_and_patterns,numerical_analysis

def create_files(folder: str, results_folder: str) -> pd.ExcelFile:
	filename = identify_files(folder)
	# Creates a list for all the dataframes, as they can then easily be turned into a single dataframe using pd.concat
	top_unique,pattern_analysis,unique_values,extreme_values,headlines,top_1000_unique_and_patterns,numerical_analysis = [],[],[],[],[],[],[]
	create_directory(folder, results_folder)
	if type(filename) == str: #Should be impossible, but just in case
		filename = [filename]
	if type(filename) == list:
		for file in filename:
			print(f'Opening {file}')
			file = f'{folder}/{file}'
			# Ensures is correct file type, and handles the filetypes appropriately
			file_extension = file.split('.')[-1]
			match file_extension:
				case 'xlsx':
					given_data = pd.ExcelFile(file)
					given_data = pd.read_excel(file,sheet_name=None)
				case 'csv':
					given_data = pd.read_csv(file)
				case _:
					print(f'{file_extension} is an invalid file format')
			top_unique_to_append,pattern_analysis_to_append,unique_values_to_append,extreme_values_to_append,headlines_to_append,top_1000_unique_and_patterns_to_append,numerical_analysis_to_append = parse_worksheets(given_data,file)
			# The line above generates dataframes, and the line below adds them to the correct list
			headlines.append(headlines_to_append)
			pattern_analysis.append(pattern_analysis_to_append)
			top_unique.append(top_unique_to_append)
			unique_values.append(unique_values_to_append)
			extreme_values.append(extreme_values_to_append)
			top_1000_unique_and_patterns.append(top_1000_unique_and_patterns_to_append)
			numerical_analysis.append(numerical_analysis_to_append)
	else:
		raise TypeError(f'{filename} is not a valid type')
	print('Formatting')
	# Combines all the dataframes for each type of analysis
	headlines = pd.concat(headlines).reset_index(drop=True)
	pattern_analysis = pd.concat(pattern_analysis).reset_index(drop=True)
	top_unique = pd.concat(top_unique).reset_index(drop=True)
	unique_values = pd.concat(unique_values).reset_index(drop=True)
	extreme_values = pd.concat(extreme_values).reset_index(drop=True)
	top_1000_unique_and_patterns = pd.concat(top_1000_unique_and_patterns).reset_index(drop=True)
	numerical_analysis = pd.concat(numerical_analysis).reset_index(drop=True)
	print('Saving')
	with pd.ExcelWriter(f"{folder}/{results_folder}/Results.xlsx") as writer:
		# Sets all the dataframes to seperate sheets, and checks numerical analysis exists, as there could be no numbers
		headlines.to_excel(writer, sheet_name='Headlines')
		pattern_analysis.to_excel(writer, sheet_name='Pattern Analysis')
		top_unique.to_excel(writer, sheet_name='Top Unique')
		unique_values.to_excel(writer, sheet_name='Unique Values')
		extreme_values.to_excel(writer, sheet_name='Extreme Values')
		top_1000_unique_and_patterns.to_excel(writer, sheet_name='Top 1000 Unique and Patterns')
		if not numerical_analysis.empty:
			numerical_analysis.to_excel(writer, sheet_name='Numerical Analysis')
		print("Done")

def create_directory(cwd:str ,results_folder:str ) -> None: # Ensures that the folder for the results file exists, and if it doesn't, creates it.
	if not os.path.exists(cwd+'/'+results_folder):
		os.makedirs(cwd+'/'+results_folder)

if __name__ == "__main__":
	#Start of program
	app = App()
	app.mainloop()