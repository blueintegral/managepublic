from flask import Flask, render_template, redirect, request, Markup
#from flask_caching import Cache
import manage
import pickle
import urllib.parse
import datetime

# #Load the settings
# with open('settings', 'rb') as f:
# 		settings = pickle.load(f)
# smartsheet_secret =  settings['smartsheet_secret']
# github_secret = settings['github_secret']
# github_user = settings['github_user']
# calendar_secret = settings['calendar_secret']
# repo_list = settings['repo_list']
# sheets = settings['sheets']
# people = settings['people']




smartsheet_secret = "" #auth key needed to fetch smartsheets through the API
github_secret = "" #personal access token for github. This token was generated to only have read access.
github_user = ""
calendar_secret = ""

repo_list = []
    
sheets = ["2025518573873028", "1393044676208516"] #order is 26 GHz, pinnacles
#EVK is "4206409551243140", 
#holographic is "1841556534650756",
#target ic is "5034469582235524",
#m8 is  "7033725318915972",


people=["Hunter Scott", "Alex Kiefer", "Chris Davlantes", "Ari Olson", "Asim Ghalib", 
			"Asmita Dani", "Gustavo Navarro", "Maaz Ahmad", "Robby Tong", "Scott MacDonald", "Varun Ramaswamy", 
			"Vinay Gowda", "Wolfgang Sedano"]

app = Flask(__name__)

#I really didn't want to have to deal with complicated caching and Redis and stuff, so this is my jank method of caching results.
#Please do not send me hate mail about it. I'm an electrical engineer, I have no business implementing an app like this.

@app.route('/people/reload')
def render_people_reload():
	#If we're reloading the page, recalculate everything 
	old_date = "" #This is empty, because on the people dashboard, we want to see the delay on each task since it was created. You can specify a date if you want to see the delay on each task since that date.
	row_html, longest_delay, team_makertime = manage.generate_task_rows(people, sheets, old_date, repo_list, smartsheet_secret, github_user, github_secret)
	longest_delay_html = manage.generate_longest_delay(longest_delay)
	total_open_tasks = manage.get_total_tasks(sheets, repo_list, smartsheet_secret, github_user, github_secret) #I think there might be a bug in here somewhere causing us to report slightly higher than correct total task count
	completed_this_week = manage.get_completed_this_week(sheets, smartsheet_secret, repo_list, github_user, github_secret)
	
	#Write the generated html to a file
	cache_data = [row_html, total_open_tasks, completed_this_week, longest_delay_html, team_makertime]
	with open('people_cache', 'wb') as f:
		pickle.dump(cache_data, f)

	#Finally, render the page
	return render_template('index.html', row_html=Markup(row_html),total_open_tasks=total_open_tasks,completed_this_week=completed_this_week,longest_delay=Markup(longest_delay_html),maker_time=team_makertime+"%")


@app.route('/people/')
def render_people():
	#If this page is requested, load from the "cache" to speed things up

	with open('people_cache', 'rb') as f:
		cache_data = pickle.load(f)

	row_html = cache_data[0]
	total_open_tasks = cache_data[1]
	completed_this_week = cache_data[2]
	longest_delay_html = cache_data[3]
	team_makertime = cache_data[4]

	#add card with number of delayed tasks, total projects
	return render_template('index.html', row_html=Markup(row_html),total_open_tasks=total_open_tasks,completed_this_week=completed_this_week,longest_delay=Markup(longest_delay_html),maker_time=team_makertime+"%")

@app.route('/schedule/')
def render_schedule():

	with open('schedule_cache', 'rb') as f:
		sched_html = pickle.load(f)

	return render_template('sched.html', sched_html=Markup(sched_html))

@app.route('/schedule/reload')
def render_schedule_reload():

	sched_html=manage.generate_sched_html(sheets, smartsheet_secret)
	
	#Write results to "cache"
	with open('schedule_cache', 'wb') as f:
		pickle.dump(sched_html, f)

	return render_template('sched.html', sched_html=Markup(sched_html))


@app.route('/schedule/<string:dates>') #Don't cache this result
def update_schedule(dates):
	
	start = dates[0:10]
	end = dates[11:21]

	sched_html=manage.generate_sched_html(sheets, smartsheet_secret, start, end)

	updated_tasks_html=""
	deleted_tasks_html=""
	top_delays_html=""
	
	return render_template('sched.html', sched_html=Markup(sched_html))

@app.route('/taskcomment', methods = ['POST'])
def record_comment():

	#print("comment got")
	#print(request.form.to_dict())
	request_dict = request.form.to_dict()
	project_name = urllib.parse.unquote(request_dict['project'])
	task_name = urllib.parse.unquote(request_dict['task'])
	comment = urllib.parse.unquote(request_dict['comment'])

	with open('comments.log', 'a') as f:
		f.write(project_name+" - "+task_name+comment+"<commented on "+datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")+">\n\n")
	return ""
	# with open('comments', 'wb') as f:
	# 	f.append(comments)


@app.route('/login/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != 'testuser' and request.form['password'] != 'testpass':
            error = 'Invalid Credentials. Please try again.'
        else:
            return redirect('/people')
    return render_template('login.html', error=error)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False)
