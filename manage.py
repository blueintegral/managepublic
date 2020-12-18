from jsondiff import diff, update, insert, delete
import requests
import os
import string
import json
import datetime
import numpy as np
from apiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle
import urllib.parse

smartsheet_secret = "" #auth key needed to fetch smartsheets through the API
test_smartsheet_id = "4318921219172228" #sheet ID of the smartsheet you're interested in
EVK_smartsheet_id = "4206409551243140"
github_secret = "" #personal access token for github. This token was generated to only have read access.
github_user = ""

scopes = ['https://www.googleapis.com/auth/calendar.readonly']

engineers=["Hunter Scott", "Alex Kiefer", "Chris Davlantes", "Ari Olson", "Asim Ghalib", 
			"Asmita Dani", "Gustavo Navarro", "Maaz Ahmad", "Robby Tong", "Scott MacDonald", "Varun Ramaswamy", 
			"Vinay Gowda", "Wolfgang Sedano"]


def generate_longest_delay(delay_string):
	delay_list = delay_string.split(' ')
	delay = delay_list[0]
	person = delay_list[1]
	html = "<div id=\"delay\" style=\"cursor:pointer\" onclick=\"$(\'."+person+"\').collapse(\'show\'); var elmnt=document.getElementById(\'"+person+"\'); elmnt.scrollIntoView(); \">"+delay+"d</div>"
	return html



def generate_task_rows(people, sheets, old_date, repos, smartsheet_secret, github_user, github_secret):
	#Returns HTML for the collapsible row for each person that lists all of their currently open tasks.
	collapse_id=""
	name=""
	num_tasks=""
	num_projects=""
	maker_time=""
	meeting_time=""
	load=""
	taskname=""
	projectname=""
	tasklength=""
	delay=""
	age=""
	final_html=""
	end_row="</div></div>"

	longest_delay = 0
	longest_delay_desc = ""

	total_maker_time = 0

	for person in people:
		collapse_id=(person.split())[0] #We need a unique div tag for each collapsible box, so we generate that based on the persons name. Should change this in case we hire two people with same name.
		name=person
		task_list = {}
		task_list = get_tasks(person, sheets, old_date, repos, smartsheet_secret, github_user, github_secret) #update this func to ingest new get_tasks output
		#tasks = tasks_raw[0] + tasks_raw[1]
		#print(tasks)
		num_tasks = 0
		num_projects = 0
		num_delay = 0
		for project in task_list:
			#print("project:"+str(project))
			#print("tasks: "+str(len(task_list[project])))
			if len(task_list[project]) > 0:
				num_projects = num_projects + 1
			num_tasks = num_tasks + len(task_list[project])
			for task in task_list[project]:
				if "delay" in task_list[project][task]:
					delay_string = task_list[project][task]["delay"]
					if delay_string != "N/A":
						delay_string = delay_string[:-1]
						if int(delay_string) > 0:
							num_delay = num_delay + 1
		num_tasks = str(num_tasks)
		num_projects = str(num_projects)
		delay_ratio = str(num_delay)
		#print(person)
		#print(get_email(person))
		meeting_list = get_meeting_data(get_email(person))
		meeting_time = meeting_list[0][:4]
		num_events = meeting_list[1]
		maker_time = str(int((int(meeting_list[2]) / 20)*100))
		total_maker_time = total_maker_time + int(meeting_list[2])

		load = "20" #should come from html input (number is gathered during 1:1 meetings)
		final_html = final_html + """<div class=\"card shadow mb-4\"> <!-- Card Header - Accordion --> 
			<a href=\"#"""+collapse_id+"""\" id=\""""+collapse_id+"""\"  style=\"width: 100%;\" class=\"d-block card-header py-3 \" data-toggle=\"collapse\" role=\"button\" aria-expanded=\"true\" aria-controls=\"collapseCardExample\">
                   <div class=\" \" style=\"margin:0px; width: 100%;\">
                    <div class=\"row\">
                      <div class=\"col\">
                      <i class=\"fa fa-bar-chart\" aria-hidden=\"true\"></i>&nbsp&nbsp&nbsp
                        <b>"""+name+"""</b>
                      </div>
                      <div class=\"col\">
                      <b>"""+num_tasks+"""</b> tasks, <b>"""+delay_ratio+"""</b> delayed
                      </div>
                      <div class=\"col\">
                      <b>"""+num_projects+"""</b> projects
                      </div>
                      <div class=\"col\">
                      <b>"""+maker_time+"""%</b> maker time
                      </div>
                      <div class=\"col\">
                      <b>"""+meeting_time+"""</b> hrs meeting time
                      </div>
                      
                    </div>
                  </div>
                </a>""" + """ <!-- Card Content - Collapse -->
                <div class=\"collapse hide """+collapse_id+"""\" id=\""""+collapse_id+"""\">
                  <div class=\"card-body\">
                    <div class=\"\" style=\"margin:0px\">
                    <div class=\"row\">
                      <div class=\"col\">
                        <b><u>Task</u></b>
                      </div>
                      <div class=\"col\">
                      <b><u>Project</u></b>
                      </div>
                      <div class=\"col\">
                      <b><u>Length</u></b> 
                      </div>
                      <div class=\"col\">
                      <b><u>Delay</u></b> 
                      </div>
                      <div class=\"col\">
                      <b><u>Age</u></b> 
                      </div>
                      <div class=\"col\">
                      <b><u>Source</u></b> 
                      </div>
                    </div>"""
			#we just added the peron's main row, now we're going to add a collapsible row for each task
		for project in task_list:
			if len(task_list[project]) > 0: #if this project has any tasks for this person
				for task in task_list[project]:
					#print(task)
					taskname = str(task)
					if len(taskname) > 16: #truncate the task name if it's too long to fit 
						display_taskname = str(task)[0:16] + "..."
					else:
						display_taskname = taskname

					projectname = project
					if len(projectname) > 18: #truncate the task name if it's too long to fit 
						display_projectname = str(project)[0:18] + "..."
					else:
						display_projectname = projectname

					tasklength = task_list[project][task]["length"]
					#print("length:"+str(tasklength))
					delay= task_list[project][task]["delay"]
					#print(delay)
					if delay != "N/A":
						if int(delay[:-1]) > longest_delay:
							longest_delay = int(delay[:-1])
							longest_delay_desc = str(longest_delay) + " " + person
					age = task_list[project][task]["age"]
					source = task_list[project][task]["source"]
					final_html = final_html + """  <div class=\"row\">
		                      <div class=\"col\" title=\""""+taskname+"""\">
		                        """+display_taskname+"""
		                      </div>
		                      <div class=\"col\" title=\""""+projectname+"""\">
		                      """+display_projectname+"""
		                      </div>
		                      <div class=\"col\">
		                      """+tasklength+"""
		                      </div>
		                      <div class=\"col\">
		                      """+delay+"""
		                      </div>
		                      <div class=\"col\">
		                      """+age+""" 
		                      </div>
		                      <div class=\"col\">
		                      """+source+""" 
		                      </div>
		                    </div>
		                  """
		final_html = final_html+"</div>" #that's closing container
		final_html = final_html+"</div>" #that's closing card body
		final_html = final_html+"</div>" #that's closing collapse hide
		final_html = final_html+"</div>" #that's closing card shadow

	possible_team_makertime = len(people)*20 #20 blocks of 2 hrs per week, times the number of people we're looking at
	team_makertime = int((total_maker_time/possible_team_makertime)*100)

	return final_html, longest_delay_desc, str(team_makertime)



def get_sheet_name(sheet, secret):
	raw_sheet = fetch_smartsheet(sheet, secret)
	return raw_sheet["name"]


def get_task_name(row, sheet):
	#Returns the task name for a given row
	#taskname = next(item for item in sheet["rows"] if item["rowNumber"] == int(row)+1)
	#print(sheet)
	if "cells" in sheet["rows"][row]:
		if sheet["rows"][row]["cells"][0]:
			if "displayValue" in sheet["rows"][row]["cells"][0]:
				return sheet["rows"][row]["cells"][0]["displayValue"]
	return ""

def get_old_value(row, cell, sheet, taskname):
	#Returns the value of a cell from the old sheet json. If the task name for the specified row doesn't equal the specified task name, returns the value of the cell with the specified task name.

	oldvalue = next(item for item in sheet["rows"] if item["rowNumber"] == int(row)+1)

	if "value" in oldvalue["cells"][cell]:
		oldvalue = oldvalue["cells"][cell]["value"]
		if get_task_name(row, sheet) == taskname:
			return oldvalue
	#This probably means there was a row insert and row numbers got shifted between sheet versions. 
	for row in sheet["rows"]:
		if "value" in row["cells"][0]:
			#print(row["cells"][0]["value"])
			if row["cells"][0]["value"] == taskname:
				return row["cells"][cell]["value"]

	# print("Original Taskname: ")
	# print(taskname)
	# print("")
	
	return "[couldn't locate old entry]"

# def locate_task_row(taskname, sheet):
# 	for row in sheet["rows"]:
# 		if "cells" in row:
# 			if "value" in row["cells"][0]:
# 				if row["cells"][0]["value"] == taskname:
# 					return row
# 	return ""



def get_new_value(row, cell, diff):
	#Returns the value of a cell from the diff, which is the latest value
	if update in diff[update]["rows"][row][update]["cells"][cell]:
		if "value" in diff[update]["rows"][row][update]["cells"][cell][update]:
			return diff[update]["rows"][row][update]["cells"][cell][update]["value"]
	if insert in diff[update]["rows"][row][update]["cells"][cell]:
		if "value" in diff[update]["rows"][row][update]["cells"][cell][insert]:
			return diff[update]["rows"][row][update]["cells"][cell][insert]["value"]

def get_tasks(person, sheets, old_date, repos, smartsheet_secret, github_user, github_secret):
	#Returns a list of currently open tasks across the github bug tracker repo and all of the sheets given for the given email.
	#Smartsheets uses email addresses, github uses user names. So we have to look up what the github user name is of a given email.
	#eventually read this from a config file

	github_person = ""
	smartsheet_person = ""
	if person == "Erik Johnson":
		smartsheet_person = "erik@reachlabs.co"
		github_person = "egjohnson7"
	if person == "Alex Kiefer":
		smartsheet_person = "alex@reachlabs.co"
		github_person = "alexkiefer93"
	if person == "Gustavo Navarro":
		smartsheet_person = "gustavo@reachlabs.co"
		github_person = "aramisentreri"
	if person == "Ari Olson":
		smartsheet_person = "ari@reachlabs.co"
		github_person = "ari-olson"
	if person == "Asim Ghalib":
		smartsheet_person = "asim@reachlabs.co"
		github_person = "Asim-ghalib"
	if person == "Asmita Dani":
		smartsheet_person = "asmita@reachlabs.co"
		github_person = "asmita1987"
	if person == "Chris Davlantes":
		smartsheet_person = "chris@reachlabs.co"
		github_person = "chrisdavl"
	if person == "Hunter Scott":
		smartsheet_person = "hunter@reachlabs.co"
		github_person = "hsotbf"
	if person == "Maaz Ahmad":
		smartsheet_person = "maaz@reachlabs.co"
		github_person = "maaz-reach"
	if person == "Robby Tong":
		smartsheet_person = "robert@reachlabs.co"
		github_person = "robwasab"
	if person == "Scott MacDonald":
		smartsheet_person = "scott@reachlabs.co"
		github_person = "scottreach"
	if person == "Varun Ramaswamy": 
		smartsheet_person = "varun@reachlabs.co"
		github_person = "v-rama"
	if person == "Vinay Gowda":
		smartsheet_person = "vinay@reachlabs.co"
		github_person = "vinayreachlabs"
	if person == "Wolfgang Sedano":
		smartsheet_person = "wolfgang@reachlabs.co"
		github_person = "wolfreachlabs"
	tasks = {}
	#start by getting the tasks from smartsheet
	for sheet in sheets:
		tasks.update(get_smartsheet_tasks(smartsheet_person, old_date, sheet, smartsheet_secret))

	#next get tasks from github
	for repo in repos:
		tasks.update(get_github_tasks(github_person, repo, github_user, github_secret))

	return tasks


def get_completed_this_week(sheets, smartsheet_secret, repos, github_user, github_secret):
	#first, we need to figure out what day of the week it is, since we only want to look at completed tasks since Monday.
	day_of_week = datetime.datetime.today().weekday()
	#0 means monday, 6 means Sunday
	today = str(datetime.datetime.now())
	today_year = int(today[0:4])
	today_mo = int(today[5:7])
	today_day = int(today[8:10])
	completed = 0
	if (day_of_week == 5) or (day_of_week == 6):
		day_of_week = 4 #If it's Saturday or Sunday, only look at tasks completed over the last work week.
	#First get Smartsheet tasks
	for sheet in sheets:
		sheet_contents = fetch_smartsheet(sheet, smartsheet_secret) 
		for row in sheet_contents["rows"]:
			if "value" in row["cells"][0]:
				row_date = row["modifiedAt"]
				row_year = int(row_date[0:4])
				row_mo = int(row_date[5:7])
				row_day = int(row_date[8:10])
				# print(day_of_week)
				# print(str(today_day - row_day))
				if (row_year == today_year) and (row_mo == today_mo) and ((today_day - row_day) <= day_of_week):
					#print("modified this week")
					if "value" in row["cells"][7]:
						if row["cells"][7]["value"] == "Complete":
							print(row["cells"][0]["value"])
							completed = completed + 1
	
	#Next get Github tasks
	for repo in repos:
		repo = repo+"?state=closed" #passing a parameter to only return closed (completed) issues
		all_issues = fetch_github_issues(repo, github_user, github_secret)
		#print(all_issues)
		for issue in all_issues:
			row_date = issue["closed_at"]
			row_year = int(row_date[0:4])
			row_mo = int(row_date[5:7])
			row_day = int(row_date[8:10])
			if (row_year == today_year) and (row_mo == today_mo) and ((today_day - row_day) <= day_of_week):
				completed = completed + 1
				#print(issue)
	return completed

def format_date(date):
	#Returns a datetime object that can be passed into np.busday_count(). Assumes date format is yyyy-mm-dd, and strips text past that.
	date = str(date)
	date_year = date[0:4]
	date_month = date[5:7]
	date_day = date[8:10]
	date = datetime.date(int(date_year), int(date_month), int(date_day))
	return date

def open_smartsheet(file):
	#Returns file handle for given file name (of the form "yyyy-mm-dd-sheet_id.json")
	with open("smartsheet_archive/"+file) as json_file:
		data = json.load(json_file)
	return data

def get_oldest_date(sheet_id, task_name, secret):
	#Returns the date of the first instance of a task_name in sheet_id by going through the historical downloaded copies of sheet_id until we find it
	files = [f for f in os.listdir("smartsheet_archive") if os.path.isfile(os.path.join("smartsheet_archive", f))]
	today = str(datetime.datetime.now())
	today = today[0:10] #slice off the time and keep only the day, month, and year
	if today+"-"+sheet_id not in files:
		download_smartsheet(sheet_id, secret)

	oldest_date = format_date(today)
	for file in files:
		if file[11:] == sheet_id:
			sheet = open_smartsheet(file)
			for row in sheet["rows"]:
				if "value" in row["cells"][0]:
					if row["cells"][0]["value"] == task_name:
						this_sheet_date = format_date(file[0:10])
						if (oldest_date - this_sheet_date).days > 0:
							oldest_date = this_sheet_date 
			#if the task is in here
			#record the date of the file and keep looking
	return str(oldest_date)[0:10]

def get_end_date(sheet_id, task_name, date):
	#Returns the end date for the specified task in the specified sheet on the specified date
	sheet = open_smartsheet(str(date)+"-"+str(sheet_id)+".json")
	for row in sheet["rows"]:
		if "value" in row["cells"][0]:
			if row["cells"][0]["value"] == task_name:
				if "value" in row["cells"][3]:
					return str(row["cells"][3]["value"])[0:10]

def get_smartsheet_tasks(person, old_date, sheet_id, secret):
	#Returns a dict of currently open tasks in the specified sheet for the specified person
	#Date must be in the form yyyy-mm-dd
	#If date argument is empty, then calculate delay from the first appearance of the task. If the date argument contains a date, calculate delay from that date.
	task_list = {}
	sheet = fetch_smartsheet(sheet_id, secret)
	project_name = sheet["name"]
	task_list[project_name] = {}

	today = format_date(datetime.datetime.now())
	#old_date = format_date(old_date)
	#old_date = dt.date(int(old_date[0:4]), int(old_date[5:7]), int(old_date[8:10]))
	#print(person)
	for row in sheet["rows"]:
		if "value" in row["cells"][5]:
			# if project_name == "Project Pinnacles":
			#print(row["cells"][5]["value"])
			#print("person: "+str(person))
			#cd print(person.split("@")[0])
			if person.split("@")[0] in row["cells"][5]["value"].lower():
				if not "value" in row["cells"][7] or row["cells"][7]["value"] != 'Complete': #If there's no status marked, count the task
					#Issue is that "person" is sometimes an email and sometimes a name. Also need to deal with multiple asignees per task

					# if project_name == "Project Pinnacles":
					# 	print(row["cells"][0]["value"])
					#print(row["cells"][0]["value"])
					task_name = row["cells"][0]["value"]
					task_list[project_name][task_name] = {}
					length = "None"
					if "value" in row["cells"][1]:
						length = row["cells"][1]["value"]
					task_list[project_name][task_name]["length"] = length
					if old_date == "":
						old_date = format_date(get_oldest_date(sheet_id, task_name, secret))
					#now we need to get the end date for this task from the sheet_id captured on old_date
					delay = "N/A"
					if "value" in row["cells"][3]:
						end_date = format_date(get_end_date(sheet_id, task_name, old_date))
						delay = str(np.busday_count(end_date, today))+"d"#current end date - end date from the old sheet. If we're on the "people" dash, old sheet is the first copy since the beginning of the project to contain that task. If we're on the sched dash, end date is an input.
						if int(delay[:-1]) < 0: #If we calculate a negative delay, that means the task is scheduled for the future
							delay = "0d" 
					task_list[project_name][task_name]["delay"] = delay
					
					start_date = "None"
					age = "None"
					if "value" in row["cells"][3]:
						start_date = format_date(row["cells"][3]["value"])
						age = str(np.busday_count(start_date, today))+"d"#today's date - start date
					
					task_list[project_name][task_name]["age"] = age
					source = "Smartsheet"
					task_list[project_name][task_name]["source"] = source
				# if row["cells"][7]["value"]: #If there is a status marked
				# 	if row["cells"][7]["value"] != 'Complete': #and if it's not marked complete, count the task
				# 		task_name = row["cells"][0]["value"]
				# 		task_list[project_name][task_name] = {}
				# 		length = row["cells"][1]["value"]
				# 		task_list[project_name][task_name]["length"] = length
				# 		if old_date == "":
				# 			old_date = format_date(get_oldest_date(sheet_id, task_name, secret))
				# 		#now we need to get the end date for this task from the sheet_id captured on old_date
				# 		end_date = format_date(get_end_date(sheet_id, task_name, old_date))
				# 		delay = str(np.busday_count(end_date, today))#current end date - end date from the old sheet. If we're on the "people" dash, old sheet is the first copy since the beginning of the project to contain that task. If we're on the sched dash, end date is an input.
						
				# 		task_list[project_name][task_name]["delay"] = delay
				# 		start_date = format_date(row["cells"][3]["value"])
				# 		age = str(np.busday_count(start_date, today))#today's date - start date
				# 		task_list[project_name][task_name]["age"] = age
				# 		source = "smartsheet"
				# 		task_list[project_name][task_name]["source"] = source
				#task_list.append(row["cells"][0]["value"])
	#if project_name == "Project Pinnacles":
	#	print(task_list)
	return task_list

#def get_unassigned_tasks(sheet_id, secret):
	#Returns all unassigned tasks for a project

def get_total_tasks(sheets, repos, smartsheet_secret, user, github_secret):
	#Returns the number of tasks across all sheets specified
	tasks = []
	for sheet in sheets:
		tasks = tasks + get_all_smartsheet_tasks(sheet, smartsheet_secret)
	
	tasks = tasks + get_all_github_tasks(repos, user, github_secret)
	
	return str(len(tasks))

def get_all_smartsheet_tasks(sheet_id, secret):
	#Returns a list of all tasks in the specified sheet
	task_list = []
	sheet = fetch_smartsheet(sheet_id, secret)
	for row in sheet["rows"]:
		if "value" in row["cells"][0]: #If there's a named task
			if "value" in row["cells"][7]:
				if row["cells"][7]["value"] != "Complete": #only count it if it's not marked as complete
					task_list.append(row["cells"][0]["value"])
			if not "value" in row["cells"][7]:
				task_list.append(row["cells"][0]["value"])

	return task_list

def get_all_github_tasks(repo_list, user, secret):
	#Returns a list of all tasks (really, issues), in the specified repos in github. This is used for counting total open tasks.
	task_list = []
	for repo in repo_list:
		all_issues = fetch_github_issues(repo, user, secret)
		for issue in all_issues:
			task_list.append(issue['title'])
	return task_list


def get_github_tasks(person, repo, user, secret):
	#Returns a list of the tasks assigned to the github username stored in 'person'. 'user' and 'secret' are github API creds.
	#This is used to generate the html rows, so we return a dict 
	#need to eventually implement pagination here
	task_list = {}
	today = format_date(datetime.datetime.now())

	
	all_issues = fetch_github_issues(repo, user, secret)
	project_name = (repo[39:])[:-7] #This chops off the front of the URL and the end of the URL and leaves just the repo name, which we're using as the project name
	task_list[project_name] = {}
	for issue in all_issues:
		for assignee in issue['assignees']: 
			if assignee['login'] == person:
				task_name = issue['title']
				task_list[project_name][task_name] = {}
				task_list[project_name][task_name]["length"] = "N/A" #Since this is a github task, it doesn't have a scheduled end date
				task_list[project_name][task_name]["delay"] = "N/A" #It doesn't have a delay, for the same reason
				start_date = issue['created_at']
				start_date = start_date[0:10]
				age = str(np.busday_count(start_date, today))#today's date - start date
				task_list[project_name][task_name]["age"] = age
				task_list[project_name][task_name]["source"] = "Github"
					
	return task_list


def fetch_github_issues(repo, user, secret):
	#Returns all of the github issues in the repo called "Issues", which we use exclusively as an issue tracker for hw builds
	issues = requests.get(repo, auth=(user, secret))
	return issues.json()

def get_meeting_data(email):
	#Returns number of hours that the specified person is in meetings this week.
	
	#TODO: This assumes everyone is on the same time zone as the internal_events calendar. Asim is the only one who's not on that time zone, so his meeting time will sometimes double count meetings.
	#I need to fix this by accounting for time zones appended to the start and end dates.


	#Because of the way the Google API works, I'm actually pulling in my calendar that has visibility of everyone elses's calendar and getting meetings from that.
	flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", scopes=scopes)
	
	#If you're running this for the first time, uncomment the next two lines. It'll auth your google account and save the creds in a file. Only do this once.
	# credentials = flow.run_console()
	# pickle.dump(credentials, open("token.pkl", "wb"))


	hours = datetime.datetime.strptime('2020-06-29T00:00:00','%Y-%m-%dT%H:%M:%S')-datetime.datetime.strptime('2020-06-29T00:00:00','%Y-%m-%dT%H:%M:%S') #This is a stupid way of doing this

	previous_date = datetime.datetime.strptime('09:00:00','%H:%M:%S') #We're going to assume people start work at 9 am
	num_events = 0
	maker_time = 0

	day_of_week = datetime.datetime.today().weekday()
	#0 means monday, 6 means Sunday
	today = str(datetime.datetime.now())
	# today_year = today[0:4]
	# today_mo = today[5:7]
	# today = str(datetime.datetime.now() + datetime.timedelta(days = 1))
	# today_day = today[8:10]
	
	# timeMax = today_year+"-"+today_mo+"-"+today_day+"T00:00:00Z"
	

	min_day_dt = datetime.datetime.now() + datetime.timedelta(days = -(day_of_week)) #This will get us to the Monday of this week
	min_day = str(min_day_dt)
	min_year = min_day[0:4]
	min_mo = min_day[5:7]
	min_day = min_day[8:10]

	timeMin = min_year+"-"+min_mo+"-"+min_day+"T00:00:00Z"


	max_day_dt = min_day_dt+datetime.timedelta(days = 6) #This will get us to the Friday of this week (actually Saturday, but we need to cover all of Friday)
	max_day = str(max_day_dt)
	max_year = max_day[0:4]
	max_mo = max_day[5:7]
	max_day = max_day[8:10]

	timeMax = max_year+"-"+max_mo+"-"+max_day+"T00:00:00Z"



	credentials = pickle.load(open("token.pkl", "rb"))
	service = build("calendar", "v3", credentials=credentials)
	#now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
	#result = service.events().list(calendarId='primary', timeMin=now, maxResults=10, singleEvents=True, orderBy='startTime').execute()
	

	#Sometimes, people duplicate an event that is already on the Reach Labs Internal calendar to their personal calendar. So we need to identify those and not count them. 
	#So if we see two events that have the same start and end time on both calendars, only count it once.

	now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
	events_result = service.events().list(calendarId=email, timeMin=timeMin, timeMax=timeMax, singleEvents=True, orderBy='startTime').execute()
	personal_events = events_result.get('items', []) #This contains the events on just the selected user's calendar

	#We also need to go through the Reach Labs Internal calendar that everyone shares, since that contains events that everyone has to attend.
	events_result = service.events().list(calendarId='reachlabs.co_dht1cknps0hq16lfagbtmeqfe4@group.calendar.google.com', timeMin=timeMin, timeMax=timeMax, singleEvents=True, orderBy='startTime').execute()
	internal_events = events_result.get('items', [])

	
	#print(email)
	# if email=="asim@reachlabs.co":
	# 	print("**************")
	# 	print(personal_events)
	# 	print("**************")
	# 	print(internal_events)
	# 	print("**************")

	#Remove events that don't have a summary
	new_personal_events = []
	new_internal_events = []
	for event in personal_events:
		if "summary" in event:
			new_personal_events.append(event)
	for event in internal_events:
		if "summary" in event:
			new_internal_events.append(event)

	personal_events = new_personal_events
	internal_events = new_internal_events

	
	new_personal_events = []
	new_internal_events = []

	if personal_events:
		personal_events[:] = [d for d in personal_events if not "OOO" in d.get("summary")]
		personal_events[:] = [d for d in personal_events if not "ooo" in d.get("summary")]
		personal_events[:] = [d for d in personal_events if "attendees" in d]
		personal_events[:] = [d for d in personal_events if "attendees" in d and not len(d.get("attendees")) == 0]

		for d in range(len(personal_events)):
			if "start" in personal_events[d]:
				if "dateTime" in personal_events[d]["start"]:
					start = personal_events[d]["start"]["dateTime"]
					end = personal_events[d]["end"]["dateTime"]
					start = to_dt(start[:-6])
					end = to_dt(end[:-6])
					if start.weekday() <= 4:
						new_personal_events.append(personal_events[d])
					elif end.weekday() <= 4:
						new_personal_events.append(personal_events[d])

	personal_events = new_personal_events
	if internal_events:
		internal_events[:] = [d for d in internal_events if not "OOO" in d.get("summary")]
		internal_events[:] = [d for d in internal_events if not "ooo" in d.get("summary")]
		
		for d in range(len(internal_events)):
			if "attendees" in internal_events[d]:
				if len(internal_events[d]["attendees"]) > 1:
					for i in range(len(internal_events[d]["attendees"])):
						if email == internal_events[d]["attendees"][i]["email"]:
							new_internal_events.append(internal_events[d])
			else:
				new_internal_events.append(internal_events[d])

	internal_events = new_internal_events
	new_internal_events = []
	dupes = []

	for d in range(len(internal_events)):
		if "start" in internal_events[d]:
				if "dateTime" in internal_events[d]["start"]:
					internal_start = internal_events[d]["start"]["dateTime"]
					internal_end = internal_events[d]["end"]["dateTime"]

					for i in range(len(personal_events)):
						if "start" in personal_events[i]:
							if "dateTime" in personal_events[i]["start"]:
								personal_start = personal_events[i]["start"]["dateTime"]
								personal_end = personal_events[i]["end"]["dateTime"]	
								if personal_start == internal_start and personal_end == internal_end:
									dupes.append(internal_events[d])
								
	internal_events[:] = [d for d in internal_events if d not in dupes]

	dupes = []

	for d in range(len(personal_events)):
		if "start" in personal_events[d]:
				if "dateTime" in personal_events[d]["start"]:
					personal1_start = personal_events[d]["start"]["dateTime"]
					personal1_end = personal_events[d]["end"]["dateTime"]

					personal2 = personal_events[(d+1):]

					for i in range(len(personal2)):
						if "start" in personal2[i]:
							if "dateTime" in personal2[i]["start"]:
								personal_start = personal2[i]["start"]["dateTime"]
								personal_end = personal2[i]["end"]["dateTime"]	
								if personal_start == personal1_start and personal_end == personal1_end:
									dupes.append(personal_events[d])

	personal_events[:] = [d for d in personal_events if d not in dupes]



	events = personal_events + internal_events
	# print("*********FINAL LIST***********")
	# print(email)
	# for event in events:
	# 	print(event["summary"])
	# print("******************************")


	if events:
		for event in events:
			start = event['start'].get('dateTime', event['start'].get('date'))
			if 'T' in start: #Only counting events that aren't all day. If the datetime string includes a "T", we know it has a timestamp. All day events do not.

				num_events = num_events + 1
				end = event['end'].get('dateTime', event['end'].get('date'))
				start = datetime.datetime.strptime(start[:-6],'%Y-%m-%dT%H:%M:%S')
				end = datetime.datetime.strptime(end[:-6],'%Y-%m-%dT%H:%M:%S')
				hours = hours + (end-start)

			
	#Finally, we need to calculate maker hours - that's the number of 2 hr blocks with no meetings in the week. From that we can calculate maker time percentage.
	#First we need to sort the events by age: oldest start time first.
	if events:
		sorted_events = sorted(events, key=return_start_date)

	possible_maker_blocks = 20 #There are 20 blocks of 2 hours in a work week
	actual_maker_blocks = 0

	current_day = set_6pm(max_day_dt) #Preserve the date, but change the time to 6pm, which we're calling the end of the work day

	#Well, I can't think of a better way to do this right now, so we're separating out each day into its own list of events
	day0 = []
	day1 = []
	day2 = []
	day3 = []
	day4 = []

	for event in sorted_events:
		if 'dateTime' in event['start']:
			if  to_dt(event['start']['dateTime'][:-6]).weekday() == 0:
				day0.append(event)
			if to_dt(event['start']['dateTime'][:-6]).weekday() == 1:
				day1.append(event)
			if  to_dt(event['start']['dateTime'][:-6]).weekday() == 2:
				day2.append(event)
			if to_dt(event['start']['dateTime'][:-6]).weekday() == 3:
				day3.append(event)
			if to_dt(event['start']['dateTime'][:-6]).weekday() == 4:
				day4.append(event)

	#Now we put theses lists in a list, one per day
	days = [day0, day1, day2, day3, day4]

	for day in days:
		if day:
			if (((set_6pm(to_dt(day[0]['start']['dateTime'][:-6])) - to_dt(day[-1]['end']['dateTime'][:-6])).seconds)/3600) > 2: #If there are more than two hours between the end of the last event of the day and the end of the workday (6pm)
				actual_maker_blocks = actual_maker_blocks + 1 #that's a maker block
			while(len(day)>1):
				if ((to_dt(day[-1]['start']['dateTime'][:-6]) - to_dt(day[-2]['end']['dateTime'][:-6])).seconds / 3600) > 2: #If there are more than two hours between the start of the last event and the end of the second to last event
					actual_maker_blocks = actual_maker_blocks + 1
				day = day[:-1]
			if (((to_dt(day[0]['end']['dateTime'][:-6]) - set_8am(to_dt(day[0]['start']['dateTime'][:-6]))).seconds)/3600) > 2: #If there are more than two hours between the beginning of the workday (8am) and the start of the first event
				actual_maker_blocks = actual_maker_blocks + 1 #that's a maker block


	#Uncomment this to print out a list of all of the calendars that my auth'd account can see. Only these calendar IDs can be used as inputs to get_meeting_time()
	# calendars_result = service.calendarList().list().execute()
	# calendars = calendars_result.get('items', [])

	# if not calendars:
	# 	print('No calendars found.')
	# for calendar in calendars:
	# 	summary = calendar['summary']
	# 	id = calendar['id']
	# 	primary = "Primary" if calendar.get('primary') else ""
	# 	print("%s\t%s\t%s" % (summary, id, primary))
	
	hours_of_meetings = str(hours.total_seconds()/3600)
	percent_maker_time = int((actual_maker_blocks/possible_maker_blocks)*100)

	return [hours_of_meetings, str(num_events), str(actual_maker_blocks)]

def to_dt(date):
	#Returns datetime object of the input string date (of the format coming from Google Calendar API)
	return datetime.datetime.strptime(date,'%Y-%m-%dT%H:%M:%S')

def set_6pm(date):
	#Takes in a datetime object and returns the same datetime object but with the time changed to 6pm
	str_date = str(date)
	str_date = str_date[0:10]+'T18:00:00'
	return datetime.datetime.strptime(str_date,'%Y-%m-%dT%H:%M:%S')


def set_8am(date):
	#Takes in a datetime object and returns the same datetime object but with the time changed to 8am
	str_date = str(date)
	str_date = str_date[0:10]+'T08:00:00'
	return datetime.datetime.strptime(str_date,'%Y-%m-%dT%H:%M:%S')

def return_start_date(event):
	return event['start'].get('dateTime', event['start'].get('date'))


def fetch_smartsheet(sheet_id, secret):
	#Gets the current version of the specified sheet and returns the json
	#First check to see if the sheet already exists. Return that rather than make an API call if it does.
	
	#Uncomment below if you want to check if we've already downloaded today's sheet before.
	#I'm leaving it disabled for now because caching works on the web interface and when I do a full refresh, I want to download the latest
	#version of the file. Useful for when people make changes at the last minute before the hw update.

	# today = str(datetime.datetime.now())
	# today = today[0:10]
	# if os.path.isfile("smartsheet_archive/"+today+"-"+sheet_id+".json"):
	# 	sheet_name = "smartsheet_archive/"+today+"-"+sheet_id+".json"
	# 	with open(sheet_name, 'r') as f:
	# 		sheet = json.load(f)
	# 	return sheet
	
	sheet = requests.get("https://api.smartsheet.com/2.0/sheets/"+sheet_id, headers={"Authorization":"Bearer "+secret})
	return sheet.json()

def download_smartsheet(sheet_id, secret):
	#Downloads today's copy of the json of the sheet specified and writes it to disk
	sheet = fetch_smartsheet(sheet_id, secret)
	date = str(datetime.datetime.now())
	date = date[0:10] #slice off the time and keep only the day, month, and year
	with open("smartsheet_archive/"+date+"-"+sheet_id+".json", 'w') as f:
		json.dump(sheet, f)
	return True

def diff_sheets(sheet_id, start_date, end_date, secret):
	#Returns three lists containing the differences between the specified sheet between the two dates. Lists are updates, inserts, and deletions.
	#todo: figure out how to cache the results of this func. It's slow.
	if os.path.isfile("smartsheet_archive/"+start_date+"-"+sheet_id+".json"): #load the start date / old sheet
		old_sheet_name = "smartsheet_archive/"+start_date+"-"+sheet_id+".json"
		with open(old_sheet_name, 'r') as f:
			old_sheet = json.load(f)
	if not os.path.isfile("smartsheet_archive/"+start_date+"-"+sheet_id+".json"):
		if start_date == str(datetime.datetime.now())[0:10]: #If the start date is today, we need to fetch the most recent json
			download_smartsheet(sheet_id, secret)
		else:
			return "Error: Missing sheet from "+start_date


	if end_date == str(datetime.datetime.now())[0:10]: #If the end date is today, we need to fetch the most recent json

		if not os.path.isfile("smartsheet_archive/"+end_date+"-"+sheet_id+".json"): #if we haven't already downloaded the file today, let's do that first
			download_smartsheet(sheet_id, secret)
		
	if os.path.isfile("smartsheet_archive/"+end_date+"-"+sheet_id+".json"): #now load the end date / new sheet
		new_sheet_name = "smartsheet_archive/"+end_date+"-"+sheet_id+".json"
		with open(new_sheet_name, 'r') as f:
			new_sheet = json.load(f)
	if not os.path.isfile("smartsheet_archive/"+end_date+"-"+sheet_id+".json"):
		return "Error: Missing sheet from "+end_date

	if start_date == end_date:
		return "Error: start and end date are the same."

	diffed = diff(old_sheet, new_sheet, syntax="explicit")

	#print(diffed)

	updated_tasks = []
	new_tasks = []
	deleted_tasks = []
	abridged_tasks = [] #This contains a shorter summary of the changes on each task and combines updated/new/deleted

	#This next part is tricky. We can handle diffing sheets pretty easily as long as there aren't row inserts. A row insert shifts all rows above or below it (depending if you insert above or below).
	#So now I can't compare the same row numbers of the same sheet of different ages.
	#But it's not always clear which rows are inserted and which are updates. So we have to search through the old sheet for an identical task name because the row number may be different.
	#This will fail if we have two of the same task names in a sheet, but I think that's rare enough to ignore for now.


	if update in diffed:
		if "rows" in diffed[update]:
			for key in diffed[update]["rows"]: #for each row
				new_duration = False
				if update in diffed[update]["rows"][key]:
					if "cells" in diffed[update]["rows"][key][update]: 
						for key2 in diffed[update]["rows"][key][update]["cells"]: #for each cell
							
							#cell 0 is task name
							#cell 1 is duration
							#cell 2 is start
							#cell 3 is finish
							#cell 4 is predecessors
							#cell 5 is Assigned To
							#cell 6 is % complete
							#cell 7 is status
							#cell 8 is comments

							taskname = get_task_name(key, new_sheet)
							if key2 == 1: #Duration is always in cell 1
								if update in diffed[update]["rows"][key][update]["cells"][key2]:
									if "value" in diffed[update]["rows"][key][update]["cells"][key2][update]:
										new_duration = True
										old_value = get_old_value(key, key2, old_sheet, taskname)
										if old_value == "[couldn't locate old entry]":
											abridged_string= "\"" + taskname + "\" duration was updated to " + get_new_value(key, key2, diffed)+". "
										else:
											abridged_string= "\"" + taskname + "\" duration was updated from " + old_value + " to " + get_new_value(key, key2, diffed)+". "

										#A new duration means a new start date and/or a new end date
										if 2 in diffed[update]["rows"][key][update]["cells"]:
											if update in diffed[update]["rows"][key][update]["cells"][2]:
												if "value" in diffed[update]["rows"][key][update]["cells"][2][update]:
													abridged_string = abridged_string + "New start date is "+ get_new_value(key, 2, diffed)[:-9]+". "
										if 3 in diffed[update]["rows"][key][update]["cells"]:	
											if update in diffed[update]["rows"][key][update]["cells"][3]:
												if "value" in diffed[update]["rows"][key][update]["cells"][3][update]:
													abridged_string = abridged_string + "New end date is "+ get_new_value(key, 3, diffed)[:-9]+". "
										abridged_tasks.append(abridged_string)

								elif insert in diffed[update]["rows"][key][update]["cells"][key2]:
									new_duration = True
									if get_new_value(key, key2, diffed):
									    abridged_string= "\"" + taskname + "\" has a new duration of " + get_new_value(key, key2, diffed)+"."

									#A new duration means a new start date and/or a new end date
									if 2 in diffed[update]["rows"][key][update]["cells"]:
										if update in diffed[update]["rows"][key][update]["cells"][2]:
											abridged_string = abridged_string + "New start date is "+ get_new_value(key, 2, diffed)[:-9]+". "
									if 3 in diffed[update]["rows"][key][update]["cells"]:
										if update in diffed[update]["rows"][key][update]["cells"][3]:
											abridged_string = abridged_string + "New end date is "+ get_new_value(key, 3, diffed)[:-9]+". "
									abridged_tasks.append(abridged_string)


								elif delete in diffed[update]["rows"][key][update]["cells"][key2]:
									abridged_string="\"" + taskname + "\" duration was deleted."
									abridged_tasks.append(abridged_string)

							
							if key2 == 2: #start date is always in cell 2
								if not new_duration: #Don't report a new start date if the duration changed, since we already reported it with the duration.
									if update in diffed[update]["rows"][key][update]["cells"][key2]:
										if "value" in diffed[update]["rows"][key][update]["cells"][key2][update]:
											#print("update: ")
											#`print(diffed[update]["rows"][key][update]["cells"][key2][update]["value"])
											old_value = get_old_value(key, key2, old_sheet, taskname)
											new_value = get_new_value(key, key2, diffed)[:-9]
											if old_value == "[couldn't locate old entry]":
												abridged_string="\"" + taskname + "\"  start date was changed to "+new_value+". "
											else:
												old_value = old_value[:-9]
												day_delta = np.busday_count(old_value, new_value)
												abridged_string="\"" + taskname + "\"  start date was changed by <a href=\"#\" data-toggle=\"tooltip\" data-placement=\"top\" title=\""+old_value+" to "+new_value+"\">"+str(day_delta)+"d. </a>"
										#abridged_string="\"" + taskname + "\" start date was updated from " + get_old_value(key, key2, old_sheet)[:-9] + " to " + get_new_value(key, key2, diffed)[:-9]+". "
										if 3 in diffed[update]["rows"][key][update]["cells"]:	
											if update in diffed[update]["rows"][key][update]["cells"][3]:
												old_value = get_old_value(key, 3, old_sheet, taskname)
												new_value = get_new_value(key, 3, diffed)[:-9]
												if old_value == "[couldn't locate old entry]":
													abridged_string= abridged_string + "End date was changed to "+new_value+". "
												else:
													old_value = old_value[:-9]
													day_delta = np.busday_count(old_value, new_value)
													abridged_string= abridged_string + "End date was changed by <a href=\"#\" data-toggle=\"tooltip\" data-placement=\"top\" title=\""+old_value+" to "+new_value+"\">"+str(day_delta)+"d. </a>"

											elif insert in diffed[update]["rows"][key][update]["cells"][3]:
												abridged_string = abridged_string + "New end date created: " + get_new_value(key, 3, diffed)[:-9]+"."
											abridged_tasks.append(abridged_string)

									elif insert in diffed[update]["rows"][key][update]["cells"][key2]:
										if "value" in diffed[update]["rows"][key][update]["cells"][key2][insert]:
											abridged_string="\"" + taskname + "\" has a new start date of " + get_new_value(key, key2, diffed)[:-9]+". "
										if update in diffed[update]["rows"][key][update]["cells"][3]:
											old_value = get_old_value(key, 3, old_sheet)
											if old_value == "[couldn't locate old entry]":
												abridged_string = abridged_string + "End date was updated to " + get_new_value(key, 3, diffed)[:-9]+". "
											else:
												old_value = old_value[:-9]
												abridged_string = abridged_string + "End date was updated from " + old_value + " to " + get_new_value(key, 3, diffed)[:-9]
										if insert in diffed[update]["rows"][key][update]["cells"][3]:
											abridged_string = abridged_string + "End date updated to " + get_new_value(key, 3, diffed)[:-9]
										abridged_tasks.append(abridged_string)

									elif delete in diffed[update]["rows"][key][update]["cells"][key2]:
										abridged_string="\"" + taskname + "\" start date was deleted."
										abridged_tasks.append(abridged_string)
							
							if key2 == 3: #end date is always in cell 3
								if not new_duration:
									if update in diffed[update]["rows"][key][update]["cells"][key2]:
										if not update in diffed[update]["rows"][key][update]["cells"][2]: #If we wrote a new start date, we also already wrote the end date
											if not insert in diffed[update]["rows"][key][update]["cells"][2]:
												old_value = get_old_value(key, key2, old_sheet)
												if old_value == "[couldn't locate old entry]":
													abridged_string="\"" + taskname + "\" end date was updated to " + get_new_value(key, key2, diffed)[:-9]
												else:
													old_value = old_value[:-9]
													abridged_string="\"" + taskname + "\" end date was updated from " + old_value + " to " + get_new_value(key, key2, diffed)[:-9]
												abridged_tasks.append(abridged_string)

									elif insert in diffed[update]["rows"][key][update]["cells"][key2]:
										#print("Task \"" + taskname + "\" has a new end date: " + get_new_value(key, key2, diffed))
										if not update in diffed[update]["rows"][key][update]["cells"][2]: #If we wrote a new start date, we also already wrote the end date
											if not insert in diffed[update]["rows"][key][update]["cells"][2]:
												abridged_string="\"" + taskname + "\" has a new end date of " + get_new_value(key, key2, diffed)[:-9]
												abridged_tasks.append(abridged_string)

									elif delete in diffed[update]["rows"][key][update]["cells"][key2]:
										#print("Task \"" + taskname + "\" end date was deleted.")
										if 1 in diffed[update]["rows"][key][update]["cells"][1]:
											if not delete in diffed[update]["rows"][key][update]["cells"][1]: #Don't report that the end date was deleted if we already reported the duration was deleted
												abridged_string="\"" + taskname + "\" end date was deleted."
												abridged_tasks.append(abridged_string)
										

							
							if key2 == 5: #assignee is always in cell 5
								if update in diffed[update]["rows"][key][update]["cells"][key2]:
									#print("Task \"" + taskname + "\" has a new assignee: " + get_old_value(key, key2, old_sheet) + " to " + get_new_value(key, key2, diffed))
									old_value = get_old_value(key, key2, old_sheet, taskname)
									if old_value == "[couldn't locate old entry]":
										abridged_string="\"" + taskname + "\" assignee was changed to " + get_new_value(key, key2, diffed)
									else:
										abridged_string="\"" + taskname + "\" assignee was changed from " + old_value + " to " + get_new_value(key, key2, diffed)
									abridged_tasks.append(abridged_string)

								if insert in diffed[update]["rows"][key][update]["cells"][key2]:
									#print("Task \"" + taskname + "\" has a new assignee: " + get_new_value(key, key2, diffed))
									abridged_string="\"" + taskname + "\" has a new assignee: " + get_new_value(key, key2, diffed)
									abridged_tasks.append(abridged_string)

								if delete in diffed[update]["rows"][key][update]["cells"][key2]:
									#print("Task \"" + taskname + "\" assignee was deleted.")
									abridged_string="\"" + taskname + "\" is no longer assigned to anyone."
									abridged_tasks.append(abridged_string)

							if key2 == 7: #status is always in cell 7
								if update in diffed[update]["rows"][key][update]["cells"][key2]:
									#print("Task \"" + taskname + "\" has an update status " + get_old_value(key, key2, old_sheet) + " to " + get_new_value(key, key2, diffed))
									old_value = get_old_value(key, key2, old_sheet, taskname)
									if old_value == "[couldn't locate old entry]":
										abridged_string="\"" + taskname + "\" status was updated to " + get_new_value(key, key2, diffed)
									else:
										abridged_string="\"" + taskname + "\" status was updated from " + old_value + " to " + get_new_value(key, key2, diffed)
									abridged_tasks.append(abridged_string)

								if insert in diffed[update]["rows"][key][update]["cells"][key2]:
									#print("Task \"" + taskname + "\" has a new status: " + get_new_value(key, key2, diffed))
									abridged_string="\"" + taskname + "\" has a new status: " + get_new_value(key, key2, diffed)
									abridged_tasks.append(abridged_string)

								if delete in diffed[update]["rows"][key][update]["cells"][key2]:
									#print("Task \"" + taskname + "\" status was deleted.")
									abridged_string="\"" + taskname + "\" status was deleted."
									abridged_tasks.append(abridged_string)
								
	return [updated_tasks, new_tasks, deleted_tasks, abridged_tasks]		


def get_email(person):
	if person == "Erik Johnson":
		email = "erik@reachlabs.co"
	if person == "Alex Kiefer":
		email = "alex@reachlabs.co"
	if person == "Gustavo Navarro":
		email = "gustavo@reachlabs.co"
	if person == "Ari Olson":
		email = "ari@reachlabs.co"
	if person == "Asim Ghalib":
		email = "asim@reachlabs.co"
	if person == "Asmita Dani":
		email = "asmita@reachlabs.co"
	if person == "Chris Davlantes":
		email = "chris@reachlabs.co"
	if person == "Hunter Scott":
		email = "hunter@reachlabs.co"
	if person == "Maaz Ahmad":
		email = "maaz@reachlabs.co"
	if person == "Robby Tong":
		email = "robert@reachlabs.co"
	if person == "Scott MacDonald":
		email = "scott@reachlabs.co"
	if person == "Varun Ramaswamy": 
		email = "varun@reachlabs.co"
	if person == "Vinay Gowda":
		email = "vinay@reachlabs.co"
	if person == "Wolfgang Sedano":
		email = "wolfgang@reachlabs.co"
	return email

def generate_sched_html(sheets, secret, *args):
	#Returns html rows for all the new tasks in the specified sheets
	#The last two arguments are optional, and are the start and end date.

	html = ""

	if len(args) > 2 or len(args) == 1:
		print('Too many or too few arguments.')
		return 1

	if len(args) == 0:
		#No dates specified, so we're going to use the default of this week
		day_of_week = datetime.datetime.today().weekday()
		start_date = datetime.datetime.now() + datetime.timedelta(days = -(day_of_week)) #This will get us to the Monday of this week
		end_date = str(datetime.datetime.today())[:10] #This is today
		start_date = str(start_date)[:10]
		
	if len(args) == 2:
		#Dates specified, so use those.
		start_date = args[0]
		end_date = args[1]


	for sheet_index, sheet in enumerate(sheets):
		tasks = diff_sheets(sheet, start_date, end_date, secret)
		#print(tasks)
		if "Error:" in tasks:
			html = html + "  <div class=\"row\"><b>"+tasks+"</b></div><br /> "
		else:
			if tasks:
				updated_tasks = tasks[0]
				new_tasks = tasks[1]
				deleted_tasks = tasks[2]

				abridged_tasks = tasks[3]
				
				name = get_sheet_name(sheet, secret)
				html = html + "  <div class=\"row\"><h4>"+name+"</h4></div><br />"
				if abridged_tasks:
					html = html + "  <div class=\"row\"><b>Changes:</b></div><br /> <ul class=\"list-group\">"
					for loopindex, task in enumerate(abridged_tasks):
						if "to Complete" in task:
							 html = html + "  <li class=\"list-group-item list-group-item-success\">"+task+"</li>"
						elif ": Complete" in task:
							html = html + "  <li class=\"list-group-item list-group-item-success\">"+task+"</li>"	 
						elif "duration was updated" in task:
							#If a duration changed, we want the ability to record why it changed. So we make a tiny form in this next div and submit it when the button is pressed.
							#The submitted div contains the task and duration change, as well as the comment. This gets handled in a route to /taskcomment and appended to a file.
							html = html + "  <li class=\"list-group-item list-group-item-warning\"><div id=\""+name+"\">"+task+"<br />" 
							script = "$('#"+str(sheet_index)+str(loopindex)+"').slideToggle();console.log('clicked');"
							html = html + "<div class=\"addcomment\" id=\"\" onclick=\""+script+"\" style=\"cursor:pointer;\"><i class=\"far fa-plus-square\"></i> Add comment</div>"
							submitscript =  "$.ajax({type: 'POST', url: '/taskcomment', data: {project: '"+urllib.parse.quote(name)+"', task: '"+urllib.parse.quote(task)+"', comment : $('#"+str(loopindex)+"-comment').serialize()}, success: function(){console.log('submitted');$('#"+str(sheet_index)+str(loopindex)+"').slideToggle()}});"
							html = html + "<div id=\""+str(sheet_index)+str(loopindex)+"\" style=\"display:none;\"><textarea rows=\"4\" cols=\"50\" id=\""+str(loopindex)+"-comment\" name=\"comment\"></textarea><br /><input type=\"submit\" value=\"Submit\" onclick=\""+submitscript+"\"></div></div></li>"
						
						else:
							html = html + "  <li class=\"list-group-item\">"+task+"</li>"
					html = html + "</ul><br />"
				else:
					html = html + "  <div class=\"row\"><b>No changes</b></div><br /> <ul class=\"list-group\">"
					html = html + "</ul><br />"
			if not tasks:
				html = html + "  <div class=\"row\"><h4>"+name+"</h4></div><br />"
				html = html + "  <div class=\"row\"><b>Changes:</b></div><br /> "
				html = html + "None"


	#print(tasks)
	# print(tasks[0])
	# print(tasks[1])
	# print(tasks[2])


	return html

#diff_sheets(test_smartsheet_id, "2020-06-03", "2020-06-04", smartsheet_secret)
#fetch_github_issues(github_user, github_secret)
#tasks = get_github_tasks("hsotbf", github_user, github_secret)
#tasks = get_smartsheet_tasks("alex@reachlabs.co", "", test_smartsheet_id, smartsheet_secret)

#sheets = [test_smartsheet_id]
#tasks = get_tasks("varun@reachlabs.co", sheets, smartsheet_secret, github_user, github_secret)
#print(tasks)
