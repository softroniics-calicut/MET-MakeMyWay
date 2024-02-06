from django.shortcuts import render, redirect
from .models import CustomUser, Package, Booking
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from django.urls import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# Create your views here.

def index(request):
    data = Package.objects.all().order_by('-price')
    return render(request, 'index.html', {'packages':data})

def contact(request):
    return render(request, 'contact.html')

def user_register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        phone = request.POST['phone']
        if CustomUser.objects.filter(username=username).exists():
            return render(request,'user-register.html',{'message':'username already exists'})
        if CustomUser.objects.filter(email=email).exists():
            return render(request,'user-register.html',{'message':'email already exists'})
        data = CustomUser.objects.create_user(username=username, email=email, password=password, phone_number=phone, user_type="user")
        data.save()
        return redirect(Login)
    else:
        return render(request, 'user-register.html')

def agency_register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        phone = request.POST['phone']
        if CustomUser.objects.filter(username=username).exists():
            return render(request,'agency-register.html',{'message':'username already exists'})
        if CustomUser.objects.filter(email=email).exists():
            return render(request,'agency-register.html',{'message':'email already exists'})
        data = CustomUser.objects.create_user(username=username, email=email, password=password, phone_number=phone, user_type="agency")
        data.save()
        return redirect(Login)
    else:
        return render(request, 'agency-register.html')

def Login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
         # Authenticate superusers (admins)
        admin_user = authenticate(request, username=username, password=password)
        if admin_user is not None and admin_user.is_staff:
            login(request, admin_user)
            return redirect(reverse('admin:index'))  # Redirect to the admin dashboard
        elif user is not None:
            # If not an admin, check regular users            
            login(request, user)
            if user.user_type == "user" and user.status == "approve":     #user profile
                return redirect(userHome)
            elif user.user_type == "agency" and user.status == "approve":   #agency profile
                return redirect(agencyindex)
            else:
                context = {
                'message': "*wait for admins approval"
            }
            return render(request, 'login.html', context)  
        else:
            context = {
                'message': "*Invalid credentials"
            }
            return render(request, 'login.html', context)
    else:
        return render(request, 'login.html')
    
def Logout(request):
    logout(request)
    return redirect(Login)

def packages(request):
    data = Package.objects.all()
    return render(request, 'packages.html', {'packages':data})

def search_package(request):
    if request.method == 'GET':
        search_query = request.GET.get('search')
        if search_query:
            packages = Package.objects.filter(destination__icontains=search_query)
            return render(request, 'packages.html', {'packages':packages})






###############################################     AGENCY     ##########################################################




@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url=Login)
def agencyindex(request):
    User = CustomUser.objects.get(id=request.user.id)
    booking_data = Booking.objects.filter(package_id__user_id=request.user.id).order_by('-status')
    pending_bookings_count = Booking.objects.filter(user_id=request.user,status='pending').count()
    items_per_page = 10
    # Use Paginator to paginate the products
    paginator = Paginator(booking_data, items_per_page)
    page = request.GET.get('page', 1)
    try:
        packages = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver the first page
        packages = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver the last page of results
        packages = paginator.page(paginator.num_pages)

    context = {
        'bookings':packages,
        'User':User,
        'pending_bookings_count':pending_bookings_count
    }
    return render(request, 'Agency/index.html', context)

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url=Login)
def rating(request,id):
    booking_data = Booking.objects.get(id=id)
    print(booking_data)
    context = {
        'bookings':booking_data,
    }
    return render(request, 'Agency/rating.html', context)


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url=Login)    
def edit_bookingstatus(request,id):
    booking = Booking.objects.get(id=id)
    if request.method == 'POST':
        status = request.POST['status']
        if status == 'approve':
            booking.status = 'approved'
        elif status == 'reject':
            booking.status = 'reject'
        booking.save()
        return redirect(agencyindex)

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url=Login)
def edit_agencyprofile(request):
    User = CustomUser.objects.get(id=request.user.id)
    if request.method == 'POST':
        User.username = request.POST['username']
        User.email = request.POST['email']
        User.phone_number = request.POST['phone_number']
        User.save()
        return redirect(agencyindex)
    else:
        context = {
            'User':User,
        }
        return render(request, 'Agency/agencyprofile.html', context)

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url=Login)
def add_package(request):
    user = CustomUser.objects.get(id=request.user.id)
    if request.method == 'POST':
        package_name = request.POST['package_name']
        price = request.POST['price']
        no_of_days = request.POST['no_of_days']
        no_of_night = request.POST['no_of_night']
        source = request.POST['source']
        destination = request.POST['destination']
        description = request.POST['description']
        img1 = request.FILES['img1']
        img2 = request.FILES['img2']
        img3 = request.FILES['img3']
        
        data = Package.objects.create(user_id=user, 
                                      package_name=package_name, 
                                      price=price, 
                                      no_of_days=no_of_days, 
                                      no_of_night=no_of_night, 
                                      source=source, 
                                      destination=destination, 
                                      description=description,
                                      img1=img1,
                                      img2=img2,
                                      img3=img3
                                    )
        data.save()
        packages = Package.objects.filter(user_id=user)
        
        return render(request, 'Agency/addpackage.html', {'packages':packages, 'User':user})
    else:
        packages = Package.objects.filter(user_id=user)
        items_per_page = 5
        # Use Paginator to paginate the products
        paginator = Paginator(packages, items_per_page)
        page = request.GET.get('page', 1)
        try:
            packages = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver the first page
            packages = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver the last page of results
            packages = paginator.page(paginator.num_pages)
        
        return render(request, 'Agency/addpackage.html', {'packages':packages, 'User':user})





    
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url=Login)
def edit_package(request, id):
    user = CustomUser.objects.get(id=request.user.id)
    packages = Package.objects.get(user_id=user, id=id)
    if request.method == 'POST':
        packages.package_name = request.POST['package_name']
        packages.price = request.POST['price']
        packages.no_of_days = request.POST['no_of_days']
        packages.no_of_night = request.POST['no_of_night']
        packages.source = request.POST['source']
        packages.destination = request.POST['destination']
        packages.description = request.POST['description']
        if 'img1' in request.FILES:
            packages.img1 = request.FILES['img1']
        if 'img2' in request.FILES:
            packages.img2 = request.FILES['img2']
        if 'img3' in request.FILES:
            packages.img3 = request.FILES['img3']

        packages.save()
        
        return redirect(add_package)
    else:
        context = {
            'id':id,
            'packages':packages
        }    
        return render(request, 'Agency/edit-package.html', context)

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url=Login)
def delete_package(request, id):
    data = Package.objects.get(id=id)
    data.delete()
    return redirect(add_package)








###############################################     USER     ###########################################################





@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url=Login)
def userHome(request):
    User = CustomUser.objects.get(id=request.user.id)
    packages = Package.objects.all().order_by('-price')
    context = {
        'User':User,
        'packages':packages 
    }
    return render(request, 'User/UserHome.html', context)

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url=Login)
def edit_userprofile(request):
    User = CustomUser.objects.get(id=request.user.id)
    if request.method == 'POST':
        User.username = request.POST['username']
        User.email = request.POST['email']
        User.phone_number = request.POST['phone_number']
        User.save()
        return redirect(userHome)
    else:
        context = {
            'User':User,
        }
        return render(request, 'User/userprofile.html', context)

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url=Login)
def user_packages(request):
    User = CustomUser.objects.get(id=request.user.id)
    data = Package.objects.all()
    return render(request, 'User/packages.html', {'packages':data, 'User':User})

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url=Login)
def usersearch_package(request):
    User = CustomUser.objects.get(id=request.user.id)
    if request.method == 'GET':
        search_query = request.GET.get('search')
        if search_query:
            packages = Package.objects.filter(destination__icontains=search_query)
            return render(request, 'User/packages.html', {'packages':packages, 'User':User})

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url=Login)
def user_contact(request):
    User = CustomUser.objects.get(id=request.user.id)
    return render(request, 'User/contact.html', {'User':User})

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url=Login)
def packageDetails(request,id):
    User = CustomUser.objects.get(id=request.user.id)
    package = Package.objects.get(id=id)
    booking_data = Booking.objects.filter(package_id=id)
    
    if request.method == 'POST':
        name = request.POST['name']
        date = request.POST['date']
        no_of_people = int(request.POST['no_of_people'])


        # Convert the date string to a datetime object 
        booking_date = datetime.strptime(date, '%Y-%m-%d').date()



        total_amount = package.price * no_of_people

        booking = Booking.objects.create(
                                         user_id=User,
                                         package_id=package,
                                         name=name, 
                                         booking_date=booking_date, 
                                         no_of_people=no_of_people, 
                                         total_amount=total_amount
                                         )                      
        booking.save()
        return redirect(userviewbookings)
    else:
        context = {
            'package':package,
            'booking_data':booking_data,
            'User':User

        }
        return render(request, 'User/PackageDetails.html', context)

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url=Login)
def userviewbookings(request):
    User = CustomUser.objects.get(id=request.user.id)
    bookings_data = Booking.objects.filter(user_id=User).order_by('-status','-date')
    items_per_page = 5
    # Use Paginator to paginate the products
    paginator = Paginator(bookings_data, items_per_page)
    page = request.GET.get('page', 1)
    try:
        packages = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver the first page
        packages = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver the last page of results
        packages = paginator.page(paginator.num_pages)
    return render(request, 'User/Booking.html', {'bookings_data':packages, 'User':User})

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url=Login)
def cancel_booking(request,id):
    bookings_data = Booking.objects.get(id=id)
    if request.method == 'POST':
        bookings_data.status='canceled'
        bookings_data.save()
        return redirect(userviewbookings)

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url=Login)
def add_review(request,id):
    booking = Booking.objects.get(id=id)
    # form = ReviewForm(request.POST or None)
    user = request.user  
    if request.method == 'POST':
        rating = request.POST['rate']
        review_text = request.POST['review']
        

        # Save the review to the database
        booking.rating = rating
        booking.review = review_text
        booking.save()
        return redirect(userviewbookings) 

    # return render(request, 'your_template.html', {'form': form, 'package': package})

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url=Login)
def payments(request,id):
    User = CustomUser.objects.get(id=request.user.id)
    booking = Booking.objects.get(id=id)
    if request.method == 'POST':
        payment_status = request.POST['status']
        booking.status = payment_status
        booking.save()
        return redirect(userviewbookings)

    else:    
        return render(request, 'User/payment.html', {'User':User, 'booking':booking})






