from flask import Flask,request,render_template,redirect,url_for,flash,session,send_file
import mysql.connector
from otp import genotp
from cmail import sendmail
from stoken import encode,decode
from flask_session import Session
from io import BytesIO
import flask_excel as excel
import re 
app=Flask(__name__)
excel.init_excel(app)
app.config['SESSION_TYPE']='filesystem'

app.secret_key='saikiran@8045'
mytdb=mysql.connector.connect(host='localhost',user='root',password='admin',db='snmproject')
Session(app)
@app.route('/')
def home():
    return render_template('welcome.html')
@app.route('/create',methods=['GET','POST'])
def create():
    if request.method=='POST':
        print(request.form)
        username=request.form['username']
        uemail=request.form['email']
        password=request.form['password']
        cpassword=request.form['cpassword']
        cursor=mytdb.cursor()
        cursor.execute('select count(useremail) from users where useremail=%s',[uemail])
        result=cursor.fetchone()
        print(result)
        if result[0]==0:
            gotp=genotp()
            udata={'username':username,'useremail':uemail,'pword':password,'otp':gotp}
            print(gotp)
            subject='OTP For Simple Notes Manager'
            body=f'otp for registration of Simple Notes manager{gotp}'
            sendmail(to=uemail,subject=subject,body=body)
            flash('OTP has sent to given mail')
            return redirect(url_for('otp',enudata=encode(data=udata)))
        elif result[0]>0:
            flash('Email already existed')
            return redirect(url_for('login'))
        else:
            return 'Something Wrong'
            
    
    return render_template('create.html')
@app.route('/otp<enudata>',methods=['GET','POST'])
def otp(enudata):
    if request.method=='POST':
        uotp=request.form['otp']
        try:
            dudata=decode(data=enudata)
        except Exception as e:
            print(e)
            return 'Something went wrong'
        else:
            if dudata['otp']==uotp:
                cursor=mytdb.cursor()
                cursor.execute('insert into users(username,useremail,password) values(%s,%s,%s)',[dudata['username'],dudata['useremail'],dudata['pword']])
                mytdb.commit()
                cursor.close()
                flash('registration Successful')
                               
                return redirect(url_for('login'))
            else:
                return 'OTP was wrong pls register again'
    return render_template('otp.html')
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        uemail=request.form['email']
        pword=request.form['password']
        cursor=mytdb.cursor(buffered=True)
        cursor.execute('select count(useremail) from users where useremail=%s',[uemail])
        bdata=cursor.fetchone()
        if bdata[0]==1:
            cursor.execute('select password from users where useremail=%s',[uemail])
            bpassword=cursor.fetchone()
            if pword==bpassword[0].decode('utf-8'):
                print(session)
                session['user']=uemail
                print(session)
                return redirect(url_for('dashboard'))
            else:
                flash('password ws wrong')
                return redirect(url_for('login'))
        elif bdata[0]==0:
            flash('email not existed')
            return redirect(url_for('create'))
        else:
            return ('something went wrong')
            
                
    
    return render_template('login.html')
@app.route('/dashboard')
def dashboard():
    if session.get('user'):
        return render_template('dashboard.html')
    else:
        return redirect(url_for('login'))
@app.route('/addnotes',methods=['GET','POST'])
def addnotes():
    if session.get('user'):
        if request.method=='POST':
            title=request.form['title']
            description=request.form['description']
            cursor=mytdb.cursor(buffered=True)
            cursor.execute('select userid from users where useremail=%s',[session.get('user')])
            uid=cursor.fetchone()
            if uid:
                try:
                    cursor.execute('insert into notes(title,ndescription,userid) values(%s,%s,%s)',[title,description,uid[0]])
                    mytdb.commit()
                    cursor.close()
                    
                except Exception as e:
                    print(e)
                    flash('Duplicate title entry')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Notes add Successfully')
                    return redirect(url_for('dashboard'))
            else:
                return 'Something Went Wrong'
        return render_template('addnotes.html')
    else:
        return redirect(url_for('login'))
@app.route('/viewallnotes')
def viewallnotes():
    if session.get('user'):
        try:
            cursor=mytdb.cursor(buffered=True)
            cursor.execute('select userid from users where useremail=%s',[session.get('user')])
            uid=cursor.fetchone()
            cursor.execute('select nid,title,create_at from notes where userid=%s',[uid[0]])
            ndata=cursor.fetchall()  # iwill return in tuple format of all data   data from backend be like [(1,"python"),(2,"java")]
        except Exception as e:
            print(e)
            flash('data not found')
            return redirect(url_for('dashboard'))
        else:
            return render_template('viewallnotes.html',ndata=ndata)
    else:
        return redirect(url_for('login'))
@app.route('/viewnotes/<nid>')
def viewnotes(nid):
    if session.get('user'):
        try:
            cursor=mytdb.cursor(buffered=True)
            cursor.execute('select * from notes where nid=%s',[nid])
            ndata=cursor.fetchone()
        except Exception as e:
            print(e)
            flash('No data found')
            return redirect(url_for('dashboard'))
        else:
            return render_template('viewnotes.html',ndata=ndata)
    else:
        return redirect(url_for('login'))
@app.route('/updatenotes/<nid>',methods=['GET','POST'])
def updatenotes(nid):
    if session.get('user'):
        cursor=mytdb.cursor(buffered=True)
        cursor.execute('select * from notes where nid=%s',[nid])
        ndata=cursor.fetchone()
        if request.method=='POST':
            title=request.form['title']
            description=request.form['description']
            cursor=mytdb.cursor(buffered=True)
            cursor.execute('update notes set title=%s,ndescription=%s where nid=%s',[title,description,nid])
            mytdb.commit()
            cursor.close()
            flash('notes updated successfully')
            return redirect(url_for('viewnotes',nid=nid))
        return render_template('updatenotes.html',ndata=ndata)
    else:
        return redirect(url_for('login'))
@app.route('/deletenotes/<nid>',methods=['GET','POST'])
def deletenotes(nid):
    if session.get('user'):
        try:
            cursor=mytdb.cursor(buffered=True)
            cursor.execute("delete from notes where nid=%s",[nid])
            mytdb.commit()
            cursor.close()
        except Exception as e:
            print(e)
            flash("something went wrong")
            return redirect(url_for('viewallnotes'))
        else:
            flash("deleted notes sucessfully")
            return redirect(url_for('viewallnotes'))
    else:
        return redirect(url_for('login'))
@app.route('/uploadfile',methods=['GET','POST'])
def uploadfile():
    if session.get('user'):
        if request.method=='POST':
            filedata=request.files['file']
            fname=filedata.filename
            fdata=filedata.read()
            try:
                cursor=mytdb.cursor(buffered=True)
                cursor.execute('select userid from users where useremail=%s',[session.get('user')])
                uid=cursor.fetchone()
                cursor.execute('insert into filedata(filename,fdata,added_by) values(%s,%s,%s)',[fname,fdata,uid[0]])
                mytdb.commit()
            except Exception as e:
                print(e)
                flash("Couldn't upload file")
                return redirect(url_for('dashboard'))
            else:
                flash('file upload successfully')
                return redirect(url_for('dashboard'))
        return render_template('uploadfile.html')
    else:
        return redirect(url_for('login'))


@app.route('/viewallfiles')
def viewallfiles():
    if session.get('user'):
        try:
            cursor=mytdb.cursor(buffered=True)
            cursor.execute('select userid from users where useremail=%s',[session.get('user')])
            uid=cursor.fetchone()
            cursor.execute('select fid,filename,created_at from filedata where added_by=%s',[uid[0]])
            filedata=cursor.fetchall()  # iwill return in tuple format of all data   data from backend be like [(1,"python"),(2,"java")]
        except Exception as e:
            print(e)
            flash('data not found')
            return redirect(url_for('dashboard'))
        else:
            return render_template('viewallfiles.html',filedata=filedata)
    else:
        return redirect(url_for('login'))

@app.route('/viewfile/<fid>')
def viewfile(fid):
    if session.get('user'):
        try:
            cursor=mytdb.cursor(buffered=True)
            cursor.execute('select filename,fdata from filedata where fid=%s',[fid])
            fdata=cursor.fetchone()
            bytes_data=BytesIO(fdata[1])
            return send_file(bytes_data,download_name=fdata[0],as_attachment=False)
        except Exception as e:
            print(e)
            flash('Could not open file')
            return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

@app.route('/downloadfile/<fid>')
def downloadfile(fid):
    if session.get('user'):
        try:
            cursor=mytdb.cursor(buffered=True)
            cursor.execute('select filename,fdata from filedata where fid=%s',[fid])
            fdata=cursor.fetchone()
            bytes_data=BytesIO(fdata[1])
            return send_file(bytes_data,download_name=fdata[0],as_attachment=True)
        except Exception as e:
            print(e)
            flash('Could not open file')
            return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

@app.route('/getexceldata')
def getexceldata():
    if session.get('user'):
        try:
            cursor=mytdb.cursor(buffered=True)
            cursor.execute('select userid from users where useremail=%s',[session.get('user')])
            uid=cursor.fetchone()
            cursor.execute('select nid,title,create_at from notes where userid=%s',[uid[0]])
            ndata=cursor.fetchall()  # iwill return in tuple format of all data   data from backend be like [(1,"python"),(2,"java")]
        except Exception as e:
            print(e)
            flash('data not found')
            return redirect(url_for('dashboard'))
        else:
            array_data=[list(i) for i in ndata]
            columns=['Notesid','Title','Content','Created_time']
            array_data.insert(0,columns)
            return excel.make_response_from_array(array_data,'xlsx',filename='notesdata')
    else:
        return redirect(url_for('login'))
@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('welcome'))
    else:
        return redirect(url_for('login'))  
    
@app.route('/search',methods=['GET','POST'])
def search():
    if session.get('user'):
        try:
            if request.method=='POST':
                sdata=request.form['sname']
                strg=['A-Za-z0-9']
                pattern=re.compile(f'^{strg}',re.IGNORECASE)
                if (pattern.match(sdata)):
                    cursor=mytdb.cursor(buffered=True)
                    cursor.execute('select * from notes where nid like %s or title like %s or ndescription like %s or create_at like %s',[sdata+'%',sdata+'%',sdata+'%',sdata+'%'])
                    sdata=cursor.fetchall()
                    cursor.close()
                    return render_template('dashboard.html',sdata=sdata)
                else:
                    flash('No data Found')
                    return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('dashboard'))
        except Exception as e:
            print(e)
            flash("can not find anything")
            return redirect(url_for('dasshboard'))
    else:
        return redirect(url_for('login'))
            
            
            
       
app.run(use_reloader=True,debug=True)