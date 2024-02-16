import pandas as pd
import re

def shine_spotlight(target :str, # The string that will be searched for
					path :str, # The file that will be searched
					column :str, # The column in which the target is located
					is_pattern :bool = False, # Is it a pattern
					is_excel :bool = None, # Is the file an excel file. Necessary because excel files contain worksheets
					sheet_name :str = None, # Sheet name with the columns, only applicable to excel files
					is_datetime :bool = False, # May make it easier to search for dates. May be unnecessary.
					search_nulls :bool = False, # All rest is irrelevant if searching for nulls
					search_len :bool = False, # Target would be used anyway, conflicts with searh nulls
					len_operator = lambda target,record: target == record # Function to compare record to target in a configurable way   
					) -> pd.DataFrame: # All rows that contain the relevant data.
	# Impossible search
	if search_len and search_nulls:
		return 'Cannot search for both lengths and nulls'

	# Finds the file type, could make is_excel obsolete
	if is_excel == None:
		if path.split('.')[-1] == 'xlsx':
			is_excel = True
		elif path.split('.')[-1] == 'csv':
			is_excel = False
		else:
			raise TypeError('The selected file is not supported')
	
	#Loads file as appropriate
	if is_excel:
		df = pd.read_excel(path,sheet_name)	
	else:
		df = pd.read_csv(path)
	
	if search_nulls:
		ids = df.loc[df[column].isnull()]
		return ids
		
	if search_len:
		ids = df.loc[len_operator(int(target),df[column].astype(str).str.len())]
		return ids

	regex = '^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'
	
	if re.match(regex,target):
		is_datetime = True
		if target == '9999-99-99 99:99:99':
			is_pattern = True
	
	regex = r'^'	# Sets the regex variable to the "start of string" character.
	
	if is_pattern: 
		# Clears special characters and changes regular characters to regex searches for pattern.
		for char in target: 
			# Converts the pattern string to 
			match char:
				case 'X':
					regex += r'[a-zA-Z]'
				case '9':
					regex += r'\d'
				case '\\' | '^' | '$' | '*' | '.' | '+' | '[' | ']' | '|' | '(' | ')' | '+' | '"' | '?' | "'":
					regex += '\\' + char
				case _:
					regex += char
		regex += r'$' 
		#Closes regex statement
		ids = df.loc[df[column].astype(str).str.match(regex,na= False)]	
		return ids
	
	elif not is_datetime:	
		for char in target:
			if char in ['\\' , '^' , '$' , '*' , '.' , '+' , '[' , ']' , '|' , '(' , ')' , '+' , '"' , '?' , "'"]:
				regex += '\\' + char
			else:
				regex += char
		regex += r'$' 
		#Closes regex statement
		ids = df.loc[df[column].astype(str).str.match(regex,na= False)]	
		return ids

	return df.loc[df[column] == target]