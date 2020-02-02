from django.shortcuts import render,redirect
from django.http import HttpResponse, HttpResponseRedirect
from pymongo import MongoClient
from  uuid import uuid4
from django.core.files.storage import FileSystemStorage
from datetime import datetime
from datetime import date
from sparkpost import SparkPost

def Hompage(request):
    if request.method =="GET":
        client = MongoClient("mongodb://127.0.0.1:27017")
        db = client.discounts
        coll = db["couponsdiscounts"]
        coll1 = db["merchants"]
        start_date = datetime.combine(datetime.utcnow().date(), datetime.min.time())
        db_data = coll.find( {"Validity": {'$gte': start_date },"status":"approved"}).limit(5)
        db_data1 = coll.find( {"Validity": {'$gte': start_date },"uploadtype":"coupons","status":"approved"}).limit(10)
        db_data2 = coll.find( {"Validity": {'$gte': start_date },"uploadtype":"deals","status":"approved"}).limit(10)
        db_data3 = coll.find({"start_date":{'$gte':start_date},"status":"approved"}).limit(20)
        stores = coll1.find({"status":"approved"})
        a = []
        c = [] 
        e = [] 
        g = []
        for b in db_data1:
            a.append(b) 
        for d in db_data2:
            c.append(d)
        for f in db_data:
            e.append(f)
        for h in db_data3:
            g.append(h) 
        return render(request,"home.html",{"coupons":a,"deals":c,"data":e,"todays":g,"stores":stores})
        
        
       
def about(request):
    if request.method == "GET":
        return render(request,"about.html")

def contact(request):
    if request.method == "GET":
        return render(request,"contact.html")  
    if request.method == "POST":
        name = request.POST["name"]
        email = request.POST["email"]
        subject = request.POST["subject"]
        message = request.POST["message"]
        sparky = SparkPost('83cc77cb771ec25d9ef26d61ff7b27c5958b32cf')
        emailBody = 'Name: {}, Email: {}, Subject: {}, Message: {}'.format(name, email, subject, message)
        response = sparky.transmissions.send(
        use_sandbox = False,
        recipients = ["chaitrahazra@gmail.com"],
        html = emailBody,
        from_email = 'bestbuy@gmrit.kspraneeth.com',
        subject = 'hello!!!!!!')
        return HttpResponse("ok")

def ForgotPassword(request):
    if request.method == "GET":
        return render(request,"forgot.html")
    elif request.method == "POST":
        email = request.POST["companyemail"]
        client = MongoClient("mongodb://127.0.0.1:27017")
        db = client.discounts
        coll = db["merchants"]
        data = coll.find_one({"companyemail":email})
        if data!= None:
            password = data["password"]
            sparky = SparkPost('83cc77cb771ec25d9ef26d61ff7b27c5958b32cf')
            response = sparky.transmissions.send(
            use_sandbox = False,
            recipients = [email],
            html = '<html><body><p>Hi! your password is {}</p></body></html>'.format(password),
            from_email = 'bestbuy@gmrit.kspraneeth.com',
            subject = 'Oh hey')
            print(response)
            return render(request,"forgot.html",{"password":password,"message":"password has been sent to your email"})

def merchant_login(request):
    if request.method == "GET":
        if request.session.get("user_session"):
            return HttpResponseRedirect('/merchant/merchant_dashboard/')
        else:
            return render(request,"login.html")
    elif request.method == "POST":
        email = request.POST["companyemail"]
        password = request.POST["password"]
        client = MongoClient("mongodb://127.0.0.1:27017")
        db = client.discounts
        coll = db["merchants"]
        dbData = coll.find_one({
            "companyemail": email,
            "password": password
        })
        if dbData != None:
            sid = str(uuid4())
            request.session["user_session"] = sid
            request.session["email_id"] = email
            coll.update_one({"companyemail": email}, {"$push": {"session_id" : sid}})
            client.close()
            return HttpResponseRedirect("/merchant/merchant_home/")
        else:
            client.close()
            return render(request,"login.html",{"a":"INVALID DEATILS"})



def merchant_register(request):
    if request.method == "GET":
        return render(request,"register.html")
    elif request.method == "POST":
        client = MongoClient("mongodb://127.0.0.1:27017")
        db = client.discounts
        col = db["merchants"]
        companyname = request.POST["companyname"]
        companyemail = request.POST["companyemail"]
        password = request.POST["password"]
        main = request.POST.getlist('category[]')
        image = request.FILES["image"]
        fs = FileSystemStorage()
        filename = fs.save(image.name, image)
        ma = []
        for a in main:
            ma.append(a)
        status ="pending"
        start_date = datetime.combine(datetime.utcnow().date(), datetime.min.time())
        p_id =  str(uuid4())
        
        col.insert_one({
            
                "companyname": companyname,
                "companyemail": companyemail,
                "password": password,
                "maincategories" : ma,
                "profile" : filename,
                "status"  : status,
                "email_verified": "false",
                "start_date" : start_date,
                "session_id" : [],
                "m_id" : p_id

            })
        SendVerificationEmail(companyemail, "merchants")
        return HttpResponseRedirect('/merchant/emailverify/')

def merchant_home(request):
    if request.method == "GET":
            sid = request.session.get("user_session")
            email = request.session.get("email_id")
            client = MongoClient("mongodb://127.0.0.1:27017")
            db = client.discounts
            coll = db["merchants"]
            coll1 = db["couponsdiscounts"]
            db_data = coll.find_one({"companyemail": email, "session_id": sid})
            start_date = datetime.now()
            db_data1 = coll1.find({"uploadtype":"coupons","email":email})
            coupons = db_data1.count()
            db_data2 = coll1.find({"uploadtype":"deals","email":email})
            deals = db_data2.count()
            print(db_data)
            if db_data != None:
                company_name = db_data["companyname"]
                profile = db_data["profile"]
                email = db_data["companyemail"]
                return render(request, "merchanthome.html", {"company_name": company_name,"profile": profile,"email":email,"coupons" : coupons,"deals": deals})
            else:
                return HttpResponse("Invalid Session!")

def merchant_saved_coupons(request):
     if request.method == "GET":
            sid = request.session.get("user_session")
            email = request.session.get("email_id")
            client = MongoClient("mongodb://127.0.0.1:27017")
            db = client.discounts
            coll = db["merchants"]
            coll1 = db["couponsdiscounts"]
            db_data = coll.find_one({"companyemail": email, "session_id": sid})
            start_date = datetime.now()
            db_data1 = coll1.find({"email":email}) 
            a = []
            for  i in db_data1:
                a.append(i)          
            print(db_data)
            if db_data != None:
                company_name = db_data["companyname"]
                profile = db_data["profile"]
                email = db_data["companyemail"]
               
                return render(request, "saved_coupons.html", {"company_name": company_name,"profile": profile,"email" :email,"data" :a})
            else:
                return HttpResponse("Invalid Session!")
def merchant_business(request):
    if request.method == "GET":
        sid = request.session.get("user_session")
        email = request.session.get("email_id")
        client = MongoClient("mongodb://127.0.0.1:27017")
        db = client.discounts
        coll = db["merchants"]
        db_data = coll.find_one({"companyemail": email, "session_id": sid})
        print(db_data)
        if db_data != None:
            company_name = db_data["companyname"]
            profile = db_data["profile"]
            cate = db_data["maincategories"]
            email = db_data["companyemail"]
            return render(request, "merchantbusiness.html", {"company_name": company_name,"profile": profile,"email": email, "cate" : cate})
        else:
            return HttpResponse("Invalid Session!")    
    elif request.method == "POST":
        client = MongoClient("mongodb://127.0.0.1:27017")
        db = client.discounts
        col = db["couponsdiscounts"]
        uploadtype = request.POST["select"]
        coupon = request.POST["type"]
        offer  = request.POST["offertitle"]
        date = request.POST["expiry"]
        end_date = datetime.strptime(date,"%Y-%m-%d")
        start_date = datetime.combine(datetime.utcnow().date(), datetime.min.time())
        coupontype = request.POST["cdtype"]
        category = request.POST["category"]
        subcategory = request.POST["sbtype"]
        des = request.POST["description"]
        company = request.POST["company"]
        email = request.session.get("email_id")
        status ="pending"
        sid = request.session.get("user_session")
        p_id =  str(uuid4())

        im = request.FILES.getlist('image')
        c = []
        for f in im :
            fs = FileSystemStorage()
            filename = fs.save(f.name,f)
            c.append(filename)
        
        col.insert_one({
                  "company": company,
                  "uploadtype" : uploadtype,
                  "code" : coupon,
                  "offer_title" : offer,
                  "Validity" : end_date,
                  "coupon_type" : coupontype,
                  "category" : category,
                  "subcategory" : subcategory,
                  "img_id" : c,
                  "start_date":start_date,
                  "description" : des,
                  "email" : email,
                  "status": status,
                  "cd_id" : p_id,
                  "session_id": sid,
        
                 })
        return HttpResponseRedirect('/merchant/merchant_business/')
def merchantprofile(request):
    if request.method == "GET":
            sid = request.session.get("user_session")
            email = request.session.get("email_id")
            client = MongoClient("mongodb://127.0.0.1:27017")
            db = client.discounts
            coll = db["merchants"]
            db_data = coll.find_one({"companyemail": email, "session_id": sid})
            print(db_data)
            if db_data != None:
                company_name = db_data["companyname"]
                profile = db_data["profile"]
                password = db_data["password"]
                email = db_data["companyemail"]
                return render(request, "merchantp.html", {"company_name": company_name,"profile": profile,"password":password,"email" :email})
            else:
                return HttpResponse("Invalid Session!")
    elif request.method == "POST":
        sid = request.session.get("user_session")
        email = request.session.get("email_id")
        client = MongoClient("mongodb://127.0.0.1:27017")
        db = client.discounts
        coll = db["merchants"]
        website = request.POST["website"]
        newpassword = request.POST["newpassword"]
        fburl = request.POST["fburl"]
        twurl = request.POST["twurl"]
        gurl  = request .POST["gurl"]
        db_data = coll.find_one({"companyemail": email, "session_id": sid})
        company_name = db_data["companyname"]
        coll.update_one( {"companyname": company_name},
            {
                "$set": {
                    "website": website,
                    "password": newpassword,
                    "fburl": fburl,
                    "twurl": twurl,
                    "gurl": gurl,
                }
            }
                
        ) 
        return HttpResponseRedirect('/merchant/merchant_success/')
def merchant_logout(request):
    if request.method == "GET":
       sid = request.session.get("user_session")
       email = request.session.get("email_id")
       del request.session["user_session"]
       del request.session["email_id"]
       client = MongoClient("mongodb://127.0.0.1:27017")
       db = client.discounts
       coll = db["merchants"]
       coll.update_one({"companyemail": email}, {"$pull": {"session_id": sid}})
       return HttpResponseRedirect("/merchant/home/")
    else:
        return HttpResponseRedirect("merchant/merchant_home/")   
    
def logouthome(request):
    if request.method =="GET":
        client = MongoClient("mongodb://127.0.0.1:27017")
        db = client.discounts
        coll = db["couponsdiscounts"]
        coll1 = db["merchants"]
        start_date = datetime.combine(datetime.utcnow().date(), datetime.min.time())
        db_data = coll.find( {"Validity": {'$gte': start_date },"status":"approved"}).limit(10)
        db_data1 = coll.find( {"Validity": {'$gte': start_date },"uploadtype":"coupons","status":"approved"}).limit(10)
        db_data2 = coll.find( {"Validity": {'$gte': start_date },"uploadtype":"deals","status":"approved"}).limit(10)
        db_data3 = coll.find({"start_date":{'$eq':start_date},"status":"approved"}).limit(20)
        stores = coll1.find({})
        a = []
        c = [] 
        e = [] 
        g = []
        for b in db_data1:
            a.append(b) 
        for d in db_data2:
            c.append(d)
        for f in db_data:
            e.append(f)
        for h in db_data3:
            g.append(h) 
        return render(request,"logouthome.html",{"coupons":a,"deals":c,"data":e,"todays":g,"stores":stores})


def user_logout(request):
    if request.method == "GET":
       sid = request.session.get("user_session")
       email = request.session.get("email_id")
       del request.session["user_session"]
       del request.session["email_id"]
       client = MongoClient("mongodb://127.0.0.1:27017")
       db = client.discounts
       coll = db["users"]
       coll.update_one({"companyemail": email}, {"$pull": {"session_id": sid}})
       return HttpResponseRedirect("/merchant/home/")
    else:
        return HttpResponseRedirect("merchant/logouthome/")

def viewdeals(request):
        if request.method =="GET":
            client = MongoClient("mongodb://127.0.0.1:27017")
            db = client.discounts
            coll = db["couponsdiscounts"]
            start_date = datetime.now()
            data = coll.find({"Validity":{'$gte':start_date},"uploadtype":"deals","status":"approved"})
            a = []
            for i in data:
                a.append(i)
            return render(request,"alldeals.html",{"deals" : a})

def viewcoupons(request):
        if request.method =="GET":
            client = MongoClient("mongodb://127.0.0.1:27017")
            db = client.discounts
            coll = db["couponsdiscounts"]
            start_date = datetime.now()
            data = coll.find({"Validity":{'$gte':start_date},"uploadtype":"coupons","status":"approved"})
            a = []
            for i in data:
                a.append(i)
            return render(request,"allcoupons.html",{"coupons" :a})

def foodseparate(request):
    if request.method == "GET":
        client = MongoClient("mongodb://127.0.0.1:27017")
        db = client.discounts
        coll = db["couponsdiscounts"]
        cat = request.GET.get("cate")
        sub = request.GET.get("subcate")
        da = coll.find({"category": cat,"subcategory" : sub,"status":"approved"})
        client.close()
        return render(request, "food.html",{"data": da})
    else:
        return HttpResponseRedirect("/merchant/home/")

def foodall(request):
    if request.method == "GET":
        client = MongoClient("mongodb://127.0.0.1:27017")
        db = client.discounts
        coll = db["couponsdiscounts"]
        cat = request.GET.get("cate")
        da = coll.find({"category": cat,"status":"approved"})
        client.close()
        return render(request, "food.html",{"data": da})
    else:
        return HttpResponseRedirect("/merchant/home/")

def clothingseparate(request):
    if request.method == "GET":
        client = MongoClient("mongodb://127.0.0.1:27017")
        db = client.discounts
        coll = db["couponsdiscounts"]
        cat = request.GET.get("cate")
        sub = request.GET.get("subcate")
        da = coll.find({"category": cat,"subcategory" : sub,"status":"approved"})
        client.close()
        return render(request, "clothing.html",{"data": da})
    else:
        return HttpResponseRedirect("/merchant/home/")

def clothingall(request):
    if request.method == "GET":
        client = MongoClient("mongodb://127.0.0.1:27017")
        db = client.discounts
        coll = db["couponsdiscounts"]
        cat = request.GET.get("cate")
        da = coll.find({"category": cat,"status":"approved"})
        client.close()
        return render(request, "clothing.html",{"data": da})

    else:
        return HttpResponseRedirect("/merchant/home/")

def saloonseparate(request):
    if request.method == "GET":
        client = MongoClient("mongodb://127.0.0.1:27017")
        db = client.discounts
        coll = db["couponsdiscounts"]
        cat = request.GET.get("cate")
        sub = request.GET.get("subcate")
        da = coll.find({"category": cat,"subcategory" : sub,"status":"approved"})
        client.close()
        return render(request, "saloon.html",{"data": da})
    else:
        return HttpResponseRedirect("/merchant/home/")

def saloonall(request):
    if request.method == "GET":
        client = MongoClient("mongodb://127.0.0.1:27017")
        db = client.discounts
        coll = db["couponsdiscounts"]
        cat = request.GET.get("cate")
        da = coll.find({"category": cat,"status":"approved"})
        client.close()
        return render(request, "saloon.html",{"data": da})
    else:
        return HttpResponseRedirect("/merchant/home/")

def groceriesall(request):
    if request.method == "GET":
        client = MongoClient("mongodb://127.0.0.1:27017")
        db = client.discounts
        coll = db["couponsdiscounts"]
        cat = request.GET.get("cate")
        da = coll.find({"category": cat,"status":"approved"})
        client.close()
        return render(request, "groceries.html",{"data": da})
    else:
        return HttpResponseRedirect("/merchant/home/")

def teseparate(request):
    if request.method == "GET":
        client = MongoClient("mongodb://127.0.0.1:27017")
        db = client.discounts
        coll = db["couponsdiscounts"]
        cat = request.GET.get("cate")
        sub = request.GET.get("subcate")
        da = coll.find({"category": cat,"subcategory" : sub,"status":"approved"})
        client.close()
        return render(request, "travel.html",{"data": da})
    else:
        return HttpResponseRedirect("/merchant/home/")

def teall(request):
    if request.method == "GET":
        client = MongoClient("mongodb://127.0.0.1:27017")
        db = client.discounts
        coll = db["couponsdiscounts"]
        cat = request.GET.get("cate")
        da = coll.find({"category": cat,"status":"approved"})
        client.close()
        return render(request, "travel.html",{"data": da})
    else:
        return HttpResponseRedirect("/merchant/home/")

def jseparate(request):
    if request.method == "GET":
        client = MongoClient("mongodb://127.0.0.1:27017")
        db = client.discounts
        coll = db["couponsdiscounts"]
        cat = request.GET.get("cate")
        sub = request.GET.get("subcate")
        da = coll.find({"category": cat,"subcategory" : sub,"status":"approved"})
        client.close()
        return render(request, "jewellery.html",{"data": da})
    else:
        return HttpResponseRedirect("/merchant/home/")

def jall(request):
    if request.method == "GET":
        client = MongoClient("mongodb://127.0.0.1:27017")
        db = client.discounts
        coll = db["couponsdiscounts"]
        cat = request.GET.get("cate")
        da = coll.find({"category": cat,"status":"approved"})
        client.close()
        return render(request, "jewellery.html",{"data": da})
    else:
        return HttpResponseRedirect("/merchant/home/")

def meseparate(request):
    if request.method == "GET":
        client = MongoClient("mongodb://127.0.0.1:27017")
        db = client.discounts
        coll = db["couponsdiscounts"]
        cat = request.GET.get("cate")
        sub = request.GET.get("subcate")
        da = coll.find({"category": cat,"subcategory" : sub,"status":"approved"})
        client.close()
        return render(request, "mobileselectronics.html",{"data": da})
    else:
        return HttpResponseRedirect("/merchant/home/")

def meall(request):
    if request.method == "GET":
        client = MongoClient("mongodb://127.0.0.1:27017")
        db = client.discounts
        coll = db["couponsdiscounts"]
        cat = request.GET.get("cate")
        da = coll.find({"category": cat,"status":"approved"})
        client.close()
        return render(request, "mobileselectronics.html",{"data": da})
    else:
        return HttpResponseRedirect("/merchant/home/")

def hkseparate(request):
    if request.method == "GET":
        client = MongoClient("mongodb://127.0.0.1:27017")
        db = client.discounts
        coll = db["couponsdiscounts"]
        cat = request.GET.get("cate")
        sub = request.GET.get("subcate")
        da = coll.find({"category": cat,"subcategory" : sub,"status":"approved"})
        client.close()
        return render(request, "homekitchen.html",{"data": da})
    else:
        return HttpResponseRedirect("/merchant/home/")

def hkall(request):
    if request.method == "GET":
        client = MongoClient("mongodb://127.0.0.1:27017")
        db = client.discounts
        coll = db["couponsdiscounts"]
        cat = request.GET.get("cate")
        da = coll.find({"category": cat,"status":"approved"})
        client.close()
        return render(request, "homekitchen.html",{"data": da})
    else:
        return HttpResponseRedirect("/merchant/home/")

def searchall(request):
    if request.method =="POST":
        client = MongoClient("mongodb://127.0.0.1:27017")
        db = client.discounts
        coll = db["couponsdiscounts"]
        search = request.POST["search"].lower()
        da = []
        data = coll.find({"category":search,"status":"approved"})
        if data != None:
            for i in data:
                da.append(i)
        data = coll.find({"subcategory": search,"status":"approved"})
        if data != None:
            for i in data:
                da.append(i)
        data = coll.find({"uploadtype" : search,"status":"approved"})
        if data != None:
            for i in data:
                da.append(i)

        if len(da) == 0:
            return render(request,"searchhome.html",{"result": "No Results!!!"})
        else:
            return render(request,"searchhome.html",{"result": da})


def stores(request):
    if request.method == "GET":
        client = MongoClient("mongodb://127.0.0.1:27017")
        db = client.discounts
        coll = db["couponsdiscounts"]
        coll1 = db["merchants"]
        email = request.GET.get("id")
        da = coll.find({"email":email })
        da1 = coll1.find({"companyemail": email,"status":"approved"})
        c = []
        for d in da1:
            c.append(d)
        a = []
        for b in da:
            a.append(b)
        client.close()
        return render(request, "stored.html",{"data":a,"data1":c})
    else:
        return HttpResponseRedirect("/merchant/home/")

def allstore(request):
    if request.method == "GET":
        client = MongoClient("mongodb://127.0.0.1:27017")
        db = client.discounts
        coll = db["couponsdiscounts"]
        cat = request.GET.get("cate")
        email  = request.GET.get("id")
        da = coll.find({"category": cat,"email":email,"status":"approved"})
        client.close()
        return render(request, "food.html",{"data": da})
    else:
        return HttpResponseRedirect("/merchant/home/")

def separatestore(request):
    if request.method == "GET":
        client = MongoClient("mongodb://127.0.0.1:27017")
        db = client.discounts
        coll = db["couponsdiscounts"]
        cat = request.GET.get("cate")
        sub = request.GET.get("subcate")
        email  = request.GET.get("id")
        da = coll.find({"category": cat,"email":email,"subcategory":sub,"status":"approved"})
        client.close()
        return render(request, "food.html",{"data": da})
    else:
        return HttpResponseRedirect("/merchant/home/")


def displaystores(request):
    if request.method == "GET":
        client = MongoClient("mongodb://127.0.0.1:27017")
        db = client.discounts
        coll = db["merchants"]        
        da = coll.find({"status":"approved"})
        a =[] 
        for i in da:
            a.append(i)
        client.close()
        return render(request, "allstores.html",{"data": a})
    else:
        return HttpResponseRedirect("/merchant/home/")


def DBConn():
    client = MongoClient("mongodb://127.0.0.1:27017")
    db = client.discounts
    return client, db

def CreateExpiryEmailHash():
    client, db = DBConn()
    dbData = db["ExpireEmailHash"].find_one({"createdIndexForKilling": "True", "forDB": "discounts"})
    if dbData == None:
        db["email_verification"].create_index("expireAt", expireAfterSeconds=86400)
        db["ExpireEmailHash"].update_one({"forDB": "discounts"}, {"$set": {"createdIndexForKilling": "True"}})
    client.close()
    return "success"

def SendVerificationEmail(email, type):
    client, db = DBConn()
    db_data = db["email_verification"].find_one({"email": email})
    if db_data == None:
        hash = str(uuid4())
        db["email_verification"].insert_one({"expireAt": datetime.utcnow(), "email": email, "hash": hash})
        client.close()
        sparky = SparkPost('83cc77cb771ec25d9ef26d61ff7b27c5958b32cf')
        emailBody = '<html><body><h1>Welcome to Bestbuy</h1><p><a href="http://127.0.0.1:8000/merchant/email/verify/?hash={}&email={}&type={}">Click here</a> to verify your email.</p></body></html>'.format(hash, email, type)
        response = sparky.transmissions.send(
        use_sandbox = False,
        recipients = [email],
        html = emailBody,
        from_email = 'bestbuy@gmrit.kspraneeth.com',
        subject = 'Verify Your Email - Bestbuy')
        CreateExpiryEmailHash()
        return response
    else:
        client.close()
        hash = db_data["hash"]
        sparky = SparkPost('83cc77cb771ec25d9ef26d61ff7b27c5958b32cf')
        emailBody = '<html><body><h1>Welcome to Bestbuy</h1><p><a href="http://127.0.0.1:8000/merchant/email/verify/?hash={}&email={}&type={}">Click here</a> to verify your email.</p></body></html>'.format(hash, email, type)
        response = sparky.transmissions.send(
        use_sandbox = False,
        recipients = [email],
        html = emailBody,
        from_email = 'email-alerts@gmrit.kspraneeth.com',
        subject = 'Verify Your Email - Bestbuy')
        CreateExpiryEmailHash()
        return response

def VerifyEmailHash(request):
    if request.method == "GET":
        if request.GET.get("hash") and request.GET.get("email") and request.GET.get("type"):
            hash = request.GET.get("hash")
            email = request.GET.get("email")
            type = request.GET.get("type")
            client = MongoClient("127.0.0.1:27017")
            db = client.discounts
            db_data = db["email_verification"].find_one({"email": email, "hash": hash})
            if db_data != None:
                db["merchants"].update_one({"companyemail": email}, {"$set": {"email_verified": "True"}})
                client.close()
                if type == "merchants":
                    redirect_url = "/merchant/merchant_login/"
                if type == "users":
                    redirect_url = "/user/user_login/"
                return HttpResponseRedirect(redirect_url)
            else:
                client.close()
                # redirect_url = "/frontpage/message/?message=Invalid verification link. Try logging in."
                return HttpResponse("Invalid link")
        else:
            return HttpResponseRedirect("/")
    else:
        return HttpResponseRedirect("https://www.youtube.com/")

def EmailVerify(request):
    if request.method == "GET":
        return render(request,"emailverify.html")

















    