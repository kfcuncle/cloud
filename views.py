from flask import Flask
from flask import render_template, request, redirect, url_for, session
from datetime import datetime
from pymysql import connections
import os
import boto3

app = Flask(__name__)

app.secret_key = 'kepsi'

db_conn = connections.Connection(
    host="database-3.cgnhhjdy7gio.us-east-1.rds.amazonaws.com",
    port=3306,
    user="aws_user",
    password="Bait3273",
    db="Assignment"
)

bucket = "tanjiahe-assignment"
region = "us=east-1"

@app.route("/", methods=['GET', 'POST'])
@app.route("/login", methods=['GET', 'POST'])
@app.route("/login/<type>", methods=['GET', 'POST'])
def login(type=None):
    if type:
        type=type
    else:
        type='student'
    msg = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']

        cursor = db_conn.cursor()
        cursor.execute('SELECT * FROM '+type+' WHERE '+type+'Email = %s AND '+type+'Password = %s', (email, password,))
        data = cursor.fetchone()

        if data:
            session['loggedin'] = True
            session['Id'] = data[0]
            session['userType'] = type
            # Redirect to home page
            
            return redirect(url_for("home"))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
            
    return render_template("login.html",type=type,msg=msg)


@app.route("/logOut")
def logOut(type=None):
    session['loggedin'] = False
    session['Id'] = ''
    session['userType'] = ''

    return redirect(url_for("login"))

@app.route("/signup", methods=['GET', 'POST'])
@app.route("/signup/<type>", methods=['GET', 'POST'])
def signup(type=None):
    type = type
    msg=''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form and 'confirmPassword' in request.form:
        email = request.form.get('email')
        password = request.form.get('password')
        confirmPassword = request.form.get('confirmPassword')
        img = request.files.get('img')

        if password == confirmPassword:
            cursor = db_conn.cursor()
            if type == 'student':
                insert_sql = "INSERT INTO student VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                cursor.execute(insert_sql,(None,None,email,password,None,None,None,None,None,None,None,None,None,None))
            else:
                insert_sql = "INSERT INTO company VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                cursor.execute(insert_sql,(None,None,email,password,None,None,None,None,None))
            db_conn.commit()
            return redirect(url_for("login",type=type))
        else:
            msg = 'Password Does Not Match!'
    return render_template("signup.html",type=type,msg=msg)

@app.route("/home")
def home():
    type=session['userType']
    return render_template("home.html",type=type)

@app.route("/jobList", methods=['GET', 'POST'])
def jobList():
    type=session['userType']

    jobEducationLevel = request.form.get('comp_select_educationLevel')
    jobIndustry = request.form.get('comp_select_industry')
    companyLocation = request.form.get('comp_select_location')
    read_sql = "SELECT jobID, companyProfilePic, jobPosition, companyLocation, jobWorkingHour, jobSalary, jobPostedDate FROM job INNER JOIN company ON job.companyID = company.companyID WHERE jobStatus = 'Approved'"
    if jobEducationLevel or jobIndustry or companyLocation:
        read_sql += " AND"
        if jobEducationLevel :
            read_sql += " jobEducationLevel = '" + jobEducationLevel + "'"
        if (jobEducationLevel and jobIndustry) or (jobEducationLevel and jobIndustry and companyLocation):
            read_sql += "AND"
        if jobIndustry:
            read_sql += " jobIndustry = '" + jobIndustry + "'"
        if (jobEducationLevel and companyLocation) or (jobIndustry and companyLocation) or (jobEducationLevel and jobIndustry and companyLocation):
            read_sql += "AND"        
        if companyLocation:
             read_sql += " companyLocation = '" + companyLocation + "'"
                
    cursor = db_conn.cursor()
    cursor.execute(read_sql)
    data = cursor.fetchall()
    cursor.execute('SELECT DISTINCT jobEducationLevel FROM job')
    educationLevel = cursor.fetchall()
    cursor.execute('SELECT DISTINCT jobIndustry FROM job')
    industry = cursor.fetchall()
    cursor.execute('SELECT DISTINCT companyLocation FROM company')
    location = cursor.fetchall()

    return render_template("jobList.html",type=type, data=data,educationLevel=educationLevel,industry=industry,location=location)

@app.route("/myJob", methods=['GET', 'POST'])
def myJob():
    type=session['userType']
    Id=session['Id']
    read_sql = "SELECT jobID, companyProfilePic, jobPosition, companyLocation, jobWorkingHour, jobSalary, jobPostedDate FROM job INNER JOIN company ON job.companyID = company.companyID WHERE company.companyID = %s"
                
    cursor = db_conn.cursor()
    cursor.execute(read_sql,(Id))
    data = cursor.fetchall()

    return render_template("myJob.html",type=type, data=data)

@app.route("/jobDetail/<jobID>" , methods=['GET', 'POST'])
def jobDetail(jobID = None):
    type=session['userType']

    jobID = jobID
    Id = session['Id']
    cursor = db_conn.cursor()

    if type == 'student':
        if request.method == 'POST' and 'apply' in request.form:
            insert_sql = "INSERT INTO application VALUES (%s, %s, %s, %s)"
            cursor.execute(insert_sql,(jobID,Id, datetime.now(), 'Pending'))
            db_conn.commit()
    else:
        if request.method == 'POST' and 'approve' in request.form:
            cursor.execute("UPDATE job SET jobStatus = 'Approved' WHERE jobID = '" + jobID + "'")
            db_conn.commit()
        if request.method == 'POST' and 'reject' in request.form:
            cursor.execute("UPDATE job SET jobStatus = 'Rejected' WHERE jobID = '" + jobID + "'")
            db_conn.commit()    

    cursor.execute("SELECT * FROM application WHERE jobID = %s and studentID = %s",(jobID,Id))
    application = cursor.fetchone()
    cursor.execute('SELECT jobID, jobPosition, companyLocation, jobIndustry, jobSalary, jobDescription, jobResponsibility, jobRequirement, jobPostedDate, jobWorkingHour, companyDescription, jobStatus FROM job INNER JOIN company ON job.companyID = company.companyID WHERE jobID =' + jobID)
    data = cursor.fetchone()
    return render_template("jobDetail.html",type=type, data=data, application=application)

    

@app.route("/profile")
def profile():
    type=session['userType']
    Id = session['Id']
    cursor = db_conn.cursor()

    if type == 'student':
        cursor.execute('SELECT * FROM student WHERE studentID = %s', (Id))
    else:
        cursor.execute('SELECT * FROM company WHERE companyID = %s', (Id))
    data = cursor.fetchone()
    return render_template("profile.html",type=type,data = data)

@app.route("/editProfile", methods=['GET', 'POST'])
def editProfile():
    type=session['userType']
    Id = session['Id']
    cursor = db_conn.cursor()
    image_url = ''
    resume_url = ''

    if type == 'student':
        cursor.execute('SELECT * FROM student WHERE studentID = %s', (Id))
    else:
        cursor.execute('SELECT * FROM company WHERE companyID = %s', (Id))
    data = cursor.fetchone()

    if request.method == 'POST':
        img = request.files.get("img")
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        location = request.form.get("location")
        programme = request.form.get("comp_select_programme")
        cgpa = request.form.get("cgpa")
        jobExperience = request.form.get("jobExperience")
        skill = request.form.get("skill")
        resume = request.files.get("resume")
        industry = request.form.get("industry")
        size = request.form.get("size")
        description = request.form.get("description")

        if img:
            image_file_name_in_s3 = type+"Id-" + str(Id) + "_image_file"
            s3 = boto3.resource('s3')
            s3.Bucket(bucket).put_object(Key=image_file_name_in_s3, Body=img)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=bucket)
            s3_location = (bucket_location['LocationConstraint'])
            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            img_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                bucket,
                image_file_name_in_s3)

        if resume:    
            pdf_file_name_in_s3 = type+"Id-" + str(Id) + "_resume_pdf"
            s3 = boto3.resource('s3')
            s3.Bucket(bucket).put_object(Key=pdf_file_name_in_s3, Body=resume)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=bucket)
            s3_location = (bucket_location['LocationConstraint'])
            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location
            resume_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                bucket,
                pdf_file_name_in_s3)

        if type == 'student':
            update_sql = 'UPDATE student SET studentName = %s, studentEmail = %s, studentProfilePic = %s, studentPhoneNo = %s, studentLocation = %s, studentProgramme = %s, studentCGPA = %s, studentJobExperience = %s, studentSkill = %s, studentResumeLink = %s WHERE studentID = %s'
            cursor.execute(update_sql, (name,email,img_url,phone,location,programme,cgpa,jobExperience,skill,resume_url,Id))
            db_conn.commit()
        else:
            update_sql = 'UPDATE company SET companyName = %s, companyEmail = %s, companyProfilePic = %s, companyLocation = %s, companyIndustry = %s, companySize = %s, companyDescription = %s WHERE companyID = %s'
            cursor.execute(update_sql, (name,email,img_url,location,industry,size,description,Id))
            db_conn.commit()
        
        return redirect(url_for("profile"))

    return render_template("editProfile.html",type=type,data = data)

@app.route("/internship", methods=['GET', 'POST'])
@app.route("/internship/<studentId>", methods=['GET', 'POST'])
def internship(studentId=None):
    type = session['userType']
    if type == 'supervisor':
        Id = studentId
    else:
        Id = session['Id']
    cursor = db_conn.cursor()

    if request.method == 'POST' or 'comp_select_faculty' in request.form or 'comp_select_programme' in request.form or 'comp_select_cohort' in request.form:
        faculty = request.form.get('comp_select_faculty')
        programme = request.form.get('comp_select_programme')
        cohort = request.form.get('comp_select_cohort')
        update_sql = 'UPDATE student SET studentFaculty = %s, studentProgramme = %s, studentCohort = %s'
        cursor.execute(update_sql,(faculty,programme,cohort))
        db_conn.commit()
    
    if request.method == 'POST' and 'comp_select_supervisor' in request.form:
        supervisor = request.form.get('comp_select_supervisor')
        read_sql = "SELECT supervisorID FROM supervisor WHERE supervisorName = '" + supervisor + "'"
        cursor.execute(read_sql)
        supervisor = cursor.fetchone()
        update_sql = 'UPDATE internship SET supervisorID = %s'
        cursor.execute(update_sql,supervisor[0])
        db_conn.commit()
    
    if request.method == 'POST': 
        if 'report1' in request.files:
            if request.files['report1']:
                report1 = request.files['report1']
                pdf_file_name_in_s3 = type+"Id-" + str(Id) + "_report1_pdf"
                s3 = boto3.resource('s3')
                s3.Bucket(bucket).put_object(Key=pdf_file_name_in_s3, Body=report1)
                bucket_location = boto3.client('s3').get_bucket_location(Bucket=bucket)
                s3_location = (bucket_location['LocationConstraint'])
                if s3_location is None:
                    s3_location = ''
                else:
                    s3_location = '-' + s3_location
                report_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                    s3_location,
                    bucket,
                    pdf_file_name_in_s3)
                create_sql = 'insert into report VALUES (%s,%s,%s,%s,%s,%s)'
                cursor.execute(create_sql,(None,'report1',report_url,datetime.now(),None,Id))
                db_conn.commit()

        if 'report2' in request.files:
            if request.files['report2']:
                report2 = request.files['report2']
                pdf_file_name_in_s3 = type+"Id-" + str(Id) + "_report2_pdf"
                s3 = boto3.resource('s3')
                s3.Bucket(bucket).put_object(Key=pdf_file_name_in_s3, Body=report2)
                bucket_location = boto3.client('s3').get_bucket_location(Bucket=bucket)
                s3_location = (bucket_location['LocationConstraint'])
                if s3_location is None:
                    s3_location = ''
                else:
                    s3_location = '-' + s3_location
                report_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                    s3_location,
                    bucket,
                    pdf_file_name_in_s3)
                create_sql = 'insert into report VALUES (%s,%s,%s,%s,%s,%s)'
                cursor.execute(create_sql,(None,'report2',report_url,datetime.now(),None,Id))
                db_conn.commit()
        if 'report3' in request.files:
            if request.files['report3']:
                report4 = request.files['report3']
                pdf_file_name_in_s3 = type+"Id-" + str(Id) + "_report3_pdf"
                s3 = boto3.resource('s3')
                s3.Bucket(bucket).put_object(Key=pdf_file_name_in_s3, Body=report3)
                bucket_location = boto3.client('s3').get_bucket_location(Bucket=bucket)
                s3_location = (bucket_location['LocationConstraint'])
                if s3_location is None:
                    s3_location = ''
                else:
                    s3_location = '-' + s3_location
                report_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                    s3_location,
                    bucket,
                    pdf_file_name_in_s3)
                create_sql = 'insert into report VALUES (%s,%s,%s,%s,%s,%s)'
                cursor.execute(create_sql,(None,'report3',report_url,datetime.now(),None,Id))
                db_conn.commit()
        if 'report4' in request.files:
            if request.files['report4']:
                report4 = request.files['report4']
                pdf_file_name_in_s3 = type+"Id-" + str(Id) + "_report4_pdf"
                s3 = boto3.resource('s3')
                s3.Bucket(bucket).put_object(Key=pdf_file_name_in_s3, Body=report4)
                bucket_location = boto3.client('s3').get_bucket_location(Bucket=bucket)
                s3_location = (bucket_location['LocationConstraint'])
                if s3_location is None:
                    s3_location = ''
                else:
                    s3_location = '-' + s3_location
                report_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                    s3_location,
                    bucket,
                    pdf_file_name_in_s3)
                create_sql = 'insert into report VALUES (%s,%s,%s,%s,%s,%s)'
                cursor.execute(create_sql,(None,'report4',report_url,datetime.now(),None,Id))
                db_conn.commit()

    if request.method == 'POST': 
        if request.form.get('mark1'):
            update_sql = 'UPDATE report SET reportMark = %s WHERE studentID = %s AND reportName = %s'
            cursor.execute(update_sql,(request.form.get('mark1'),Id,'report1'))
            db_conn.commit()
        if request.form.get('mark2'):
            update_sql = 'UPDATE report SET reportMark = %s WHERE studentID = %s AND reportName = %s'
            cursor.execute(update_sql,(request.form.get('mark2'),Id,'report2'))
            db_conn.commit()
        if request.form.get('mark3'):
            update_sql = 'UPDATE report SET reportMark = %s WHERE studentID = %s AND reportName = %s'
            cursor.execute(update_sql,(request.form.get('mark3'),Id,'report3'))
            db_conn.commit()
        if request.form.get('mark4'):
            update_sql = 'UPDATE report SET reportMark = %s WHERE studentID = %s AND reportName = %s'
            cursor.execute(update_sql,(request.form.get('mark4'),Id,'report4'))
            db_conn.commit()

    cursor.execute('SELECT * FROM report WHERE studentID = %s AND reportName = %s', (Id,'report1'))
    report1 = cursor.fetchone()
    cursor.execute('SELECT * FROM report WHERE studentID = %s AND reportName = %s', (Id,'report2'))
    report2 = cursor.fetchone()
    cursor.execute('SELECT * FROM report WHERE studentID = %s AND reportName = %s', (Id,'report3'))
    report3 = cursor.fetchone()
    cursor.execute('SELECT * FROM report WHERE studentID = %s AND reportName = %s', (Id,'report4'))
    report4 = cursor.fetchone()

    if report1 and report2 and report3 and report4:
        if report1[4] and report2[4] and report3[4] and report4[4]:
            finalMark = (report1[4] + report2[4] + report3[4] + report4[4])/4
            if finalMark >= 80:
                grade = 'A'
            elif finalMark >= 70 and finalMark < 80:
                grade = 'B'
            elif finalMark >= 60 and finalMark < 70:
                grade = 'C'
            else:
                grade = 'F'
            update_sql = 'UPDATE internship SET internshipResult = %s WHERE studentID = %s'
            cursor.execute(update_sql,(grade,Id))

    cursor.execute('SELECT studentID,studentName,studentFaculty,studentProgramme,studentCohort FROM student WHERE studentID = %s', (Id))
    data = cursor.fetchone()
    cursor.execute('SELECT supervisor.supervisorID, supervisorName, internshipStartDate, internshipEndDate, internshipStatus, internshipResult FROM internship INNER JOIN supervisor ON supervisor.supervisorID = internship.supervisorID WHERE studentID = %s', (Id))
    internship = cursor.fetchone()
    
    return render_template("internship.html",type=type,data = data, internship=internship, report1=report1, report2=report2, report3=report3, report4=report4)

@app.route("/postJob", methods=['GET', 'POST'])
def postJob():
    if request.method == 'POST':
        Id = session['Id']
        jobPosition = request.form.get('jobPosition')
        jobDesciption = request.form.get('jobDesciption')
        jobResponsibility = request.form.get('jobResponsibility')
        jobRequirement = request.form.get('jobRequirement')
        jobSalary = request.form.get('jobSalary')
        jobWorkingHour = request.form.get('jobWorkingHour')
        jobIndustry = request.form.get('comp_select_industry')
        jobEducationLevel = request.form.get('comp_select_educationLevel')

        cursor = db_conn.cursor()
        insert_sql = "INSERT INTO job VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        cursor.execute(insert_sql,(None,jobPosition,jobSalary,jobWorkingHour,jobIndustry,jobEducationLevel,jobDesciption,jobResponsibility,jobRequirement,datetime.now(),"Pending",Id))
        db_conn.commit()
        return render_template("home.html",type='company')
    else:
        return render_template("postJob.html",type='company')
    
@app.route("/verdictJob", methods=['GET', 'POST'])
def verdictJob():
    type = session['userType']
    jobStatus = request.form.get('comp_select_status')
    read_sql = "SELECT jobID, jobPosition, jobSalary, jobWorkingHour, jobPostedDate, jobStatus, companyLocation FROM job INNER JOIN company ON job.companyID = company.companyID"

    if jobStatus:
        read_sql += " WHERE jobStatus = '" + jobStatus + "'"
    read_sql += " ORDER BY jobPostedDate DESC"            
    cursor = db_conn.cursor()
    cursor.execute(read_sql)
    data = cursor.fetchall()

    return render_template("verdictJob.html",type=type, data=data)

@app.route("/supervise", methods=['GET', 'POST'])
def supervise():
    type = session['userType']
    Id = session['Id']
    read_sql = "SELECT student.studentID, studentName, internshipStatus FROM supervisor INNER JOIN internship ON supervisor.supervisorID = internship.supervisorID INNER JOIN student ON internship.studentID = student.studentID WHERE supervisor.supervisorID = %s"    
    cursor = db_conn.cursor()
    cursor.execute(read_sql,(Id))
    data = cursor.fetchall()

    return render_template("supervise.html",type=type, data=data)

@app.route("/studentList/<Id>", methods=['GET', 'POST'])
def studentList(Id=None):
    type = session['userType']
    Id = Id
    read_sql = "SELECT student.studentID, studentProfilePic,studentProgramme,studentCGPA FROM job INNER JOIN application ON application.jobID = job.jobID INNER JOIN student ON student.studentID = application.studentID WHERE job.jobID = %s"    
    cursor = db_conn.cursor()
    cursor.execute(read_sql,(Id))
    data = cursor.fetchall()

    return render_template("studentList.html",type=type, data=data)

@app.route("/studentProfile/<Id>")
def studentProfile(Id=None):
    Id = Id
    type = 'student'
    cursor = db_conn.cursor()
    cursor.execute('SELECT * FROM student WHERE studentID = %s', (Id))
    data = cursor.fetchone()
    return render_template("profile.html",type=type,data = data)

@app.route("/aboutUs")
def aboutUs(Id=None):
    type = session['userType']
    return render_template("aboutUs.html",type=type)
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
