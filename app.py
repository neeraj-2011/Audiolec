from flask import Flask, render_template, request, url_for, redirect, session
import GoogleNLPAPI as api
import getYoutubeVideoLinks as getYT
import emailer as email
import speech_recognition as sr
from emailAnalysis import send_email
import sqlite3

app = Flask(__name__)
app.secret_key = 'thisisasecretkey'

@app.route('/delallsessions')
def delallsessions():
    session.pop('transcript', None)
    session.pop('summary', None)
    session.pop('keywords', None)
    session.pop('email_sent', None)
    return redirect('/')


@app.route('/', methods=['GET', 'POST'])
def index():
    # session.pop('transcript', None)
    # session.pop('summary', None)
    # session.pop('keywords', None)
    return render_template('home.html')


@app.route('/logon')
def logon():
	return render_template('signup.html')

@app.route('/login')
def login():
	return render_template('signin.html')

@app.route("/signup")
def signup():

    username = request.args.get('user','')
    name = request.args.get('name','')
    email = request.args.get('email','')
    number = request.args.get('mobile','')
    password = request.args.get('password','')
    con = sqlite3.connect('signup.db')
    cur = con.cursor()
    cur.execute("insert into `info` (`user`,`email`, `password`,`mobile`,`name`) VALUES (?, ?, ?, ?, ?)",(username,email,password,number,name))
    con.commit()
    con.close()
    return render_template("signin.html")

@app.route("/signin")
def signin():

    mail1 = request.args.get('user','')
    password1 = request.args.get('password','')
    con = sqlite3.connect('signup.db')
    cur = con.cursor()
    cur.execute("select `user`, `password` from info where `user` = ? AND `password` = ?",(mail1,password1,))
    data = cur.fetchone()

    if data == None:
        return render_template("signin.html")    

    elif mail1 == 'admin' and password1 == 'admin':
        return render_template("convertwav.html")

    elif mail1 == str(data[0]) and password1 == str(data[1]):
        return render_template("convertwav.html")
    else:
        return render_template("signup.html")


@app.route('/delsession', methods=['GET', 'POST'])
def delscript():
    session.pop('transcript', None)
    session.pop('summary', None)
    session.pop('keywords', None)
    return redirect('/convertwav')


@app.route('/textanalysis', methods=['GET', 'POST'])
def textanalysis():
    videos = []
    # people = []
    # places = []
    if 'transcript' in session:
        if request.method == 'POST':
            emailform = request.form
            reciever = emailform['email']
            subject = emailform['subject']
            send_email(f"{subject} - Your AudioLec Lecture", session['transcript'], reciever,
                       'hackathon2020', 'audiolec4@gmail.com', session['videos'], session['keywords'])
        keywords = api.sample_analyze_entities(session['transcript'])
        session["keywords"] = []

        for x in range(0, len(keywords)):
            if not keywords[x].isdigit():
                session["keywords"].append(keywords[x])
        
        if 'keywords' in session:
            for keyword in keywords:
                video = getYT.searchVideoForKeyword(keyword)
                for indivvideo in video:
                        #     if catergory == "people":
                        #         people.append(f'{indivvideo}')
                        #     elif catergory == "placesOrOrganizations":
                        #         places.append(f'{indivvideo}')
                    videos.append(f'{indivvideo}')
            session['videos'] = videos
            length_keywords = len(session['keywords'])
            return render_template('textanalysis.html', session=session, length_keywords=length_keywords)
        else:
            return redirect('/convertwav')

@app.route('/youtubevids')
def youtubevids():
    videos = []
    # people = []
    # places = []
    if 'keywords' in session:
       
        for keyword in session['keywords']:
            video = getYT.searchVideoForKeyword(keyword);
            for singlevid in video:
                videos.append(f'{singlevid}')

        return render_template('videos.html', videos=videos)
    else:
        return redirect('/convertwav')


@app.route('/convertwav', methods=['GET', 'POST'])
def convertwav():
    transcript = ""
    if request.method == "POST":
        if "myfiles[]" not in request.files:
            return redirect(request.url)

        file = request.files["myfiles[]"]
        if file.filename == "":
            return redirect(request.url)

        if file:
            # create recognizer object
            recognizer = sr.Recognizer()

            
            audioFile = sr.AudioFile(file)
            with audioFile as source:
                recognizer.adjust_for_ambient_noise(source)
                data = recognizer.record(source)
            transcript = recognizer.recognize_google(data, key=None)
            session['transcript'] = transcript


            return redirect('/textanalysis')

    return render_template('convertwav.html')





if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)
