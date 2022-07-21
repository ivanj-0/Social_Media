from django.shortcuts import render, redirect
from django.contrib.auth.models import User, auth
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from requests import post
from .models import Profile, Post, LikePost, FollowersCount, Comment
from .forms import CommentForm, EditForm, PrefForm
from itertools import chain
import random
from django.views.generic import UpdateView
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import csv

# Create your views here.

@login_required(login_url='signin')
def index(request):
    user_object = User.objects.get(username=request.user.username)

    try:
        user_profile = Profile.objects.get(user=user_object)
    except Profile.DoesNotExist:
        new_profile = Profile.objects.create(user=user_object, id_user=user_object.id)
        new_profile.save()
        return redirect('settings')

    user_following_list = []
    feed = []

    user_following = FollowersCount.objects.filter(follower=request.user)

    for users in user_following:
        user_following_list.append(users.user)

    for usernames in user_following_list:
        feed_lists = Post.objects.filter(user=usernames)
        feed.append(feed_lists)

    feed_list = list(chain(*feed))

    # user suggestion starts
    all_users = User.objects.all()
    user_following_all = []

    for user in user_following:
        user_list = User.objects.get(username=user.user)
        user_following_all.append(user_list)
    
    new_suggestions_list = [x for x in list(all_users) if (x not in list(user_following_all))]
    current_user = User.objects.filter(username=request.user.username)
    final_suggestions_list = [x for x in list(new_suggestions_list) if ( x not in list(current_user))]
    random.shuffle(final_suggestions_list)

    username_profile = []
    username_profile_list = []

    for users in final_suggestions_list:
        username_profile.append(users.id)

    for ids in username_profile:
        profile_lists = Profile.objects.filter(id_user=ids)
        username_profile_list.append(profile_lists)

    suggestions_username_profile_list = list(chain(*username_profile_list))

    comment_list = Comment.objects.all()


    cf = CommentForm()
    context = {
        'user_object': user_object,
        'user_profile': user_profile,
        'posts': feed_list,
        'suggestions_username_profile_list': suggestions_username_profile_list[:4],
        'comment_form': cf,
        'comment_list': comment_list,
    }

    return render(request, 'index.html', context)

@login_required(login_url='signin')
def upload(request):

    if request.method == 'POST':
        user = request.user
        image = request.FILES.get('image_upload')
        caption = request.POST['caption']
        
        new_post = Post.objects.create(user=user, image=image, caption=caption)
        new_post.save()
        list1 = FollowersCount.objects.filter(user=user) 
        
        for i in list1:
            profile=Profile.objects.get(user=i.follower)
            if profile.pref is True:
                message = Mail(
                from_email='ivanjosephjacob@gmail.com',
                to_emails=i.follower.email,
                subject='Post',
                html_content='<div style="font-family: inherit; text-align: inherit"><span style="font-size: 30px"> User has a new post!</span></div>')
                try:
                    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
                    response = sg.send(message)
                    print(response.status_code)
                    print(response.body)
                    print(response.headers)
                except Exception as e:
                    print(e.message)
                    print('poop')

          




        return redirect('/')
    else:
        return redirect('/')

@login_required(login_url='signin')
def comment(request, pk):

    if request.method == 'POST':
        user = request.user
        post = Post.objects.get(pk=pk)
        comment = request.POST['content']

        new_comment = Comment.objects.create(user=user, post=post, comment=comment)
        new_comment.save()

    return redirect('/')

@login_required(login_url='signin')
def explore(request):
    posts = Post.objects.all()
    return render(request, 'explore.html', {'posts': posts})



@login_required(login_url='signin')
def search(request):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)

    if request.method == 'POST':
        username = request.POST['username']
        username_object = User.objects.filter(username__icontains=username)

        username_profile = []
        username_profile_list = []

        for users in username_object:
            username_profile.append(users.id)

        for ids in username_profile:
            profile_lists = Profile.objects.filter(id_user=ids)
            username_profile_list.append(profile_lists)
        
        username_profile_list = list(chain(*username_profile_list))
    return render(request, 'search.html', {'user_profile': user_profile, 'username_profile_list': username_profile_list})

@login_required(login_url='signin')
def like_post(request):
    username = request.user
    post_id = request.GET.get('post_id')

    post = Post.objects.get(id=post_id)

    like_filter = LikePost.objects.filter(post_id=post_id, username=username).first()

    if like_filter == None:
        new_like = LikePost.objects.create(post_id=post_id, username=username)
        new_like.save()
        post.no_of_likes = post.no_of_likes+1
        post.save()
        return redirect('/')
    else:
        like_filter.delete()
        post.no_of_likes = post.no_of_likes-1
        post.save()
        return redirect('/')

@login_required(login_url='signin')
def profile(request, pk):
    user_object = User.objects.get(username=pk)
    user_profile = Profile.objects.get(user=user_object)
    user_posts = Post.objects.filter(user=user_object)
    user_post_length = len(user_posts)

    follower = request.user

    if FollowersCount.objects.filter(follower=follower, user=user_object).first():
        button_text = 'Unfollow'
    else:
        button_text = 'Follow'

    user_followers = len(FollowersCount.objects.filter(user=user_object))
    user_following = len(FollowersCount.objects.filter(follower=user_object))
    

    comment_list = Comment.objects.all()

    context = {
        'user_object': user_object,
        'user_profile': user_profile,
        'user_posts': user_posts,
        'user_post_length': user_post_length,
        'button_text': button_text,
        'user_followers': user_followers,
        'user_following': user_following,
        'comment_list': comment_list,
        
        
    }
    return render(request, 'profile.html', context)

@login_required(login_url='signin')
def follow(request):
    if request.method == 'POST':
        name = request.POST['user']
        follower = request.user
        user = User.objects.get(username = name)

        if FollowersCount.objects.filter(follower=follower, user=user).first():
            delete_follower = FollowersCount.objects.get(follower=follower, user=user)
            delete_follower.delete()
            return redirect('/profile/'+user.username)
        else:
            new_follower = FollowersCount.objects.create(follower=follower, user=user)
            new_follower.save()
            return redirect('/profile/'+user.username)
    else:
        return redirect('/')

@login_required(login_url='signin')
def settings(request):
    user_profile = Profile.objects.get(user=request.user)

    if request.method == 'POST':
        
        if request.FILES.get('image') == None:
            image = user_profile.profileimg
            bio = request.POST['bio']
            location = request.POST['location']

            user_profile.profileimg = image
            user_profile.bio = bio
            user_profile.location = location
            user_profile.save()
        if request.FILES.get('image') != None:
            image = request.FILES.get('image')
            bio = request.POST['bio']
            location = request.POST['location']

            user_profile.profileimg = image
            user_profile.bio = bio
            user_profile.location = location
            user_profile.save()
        
        return redirect('settings')
    return render(request, 'setting.html', {'user_profile': user_profile})

def signup(request):

    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']

        if password == password2:
            if User.objects.filter(email=email).exists():
                messages.info(request, 'Email Taken')
                return redirect('signup')
            elif User.objects.filter(username=username).exists():
                messages.info(request, 'Username Taken')
                return redirect('signup')
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()

                #log user in and redirect to settings page
                user_login = auth.authenticate(username=username, password=password)
                auth.login(request, user_login)

                #create a Profile object for the new user
                user_model = User.objects.get(username=username)
                new_profile = Profile.objects.create(user=user_model, id_user=user_model.id)
                new_profile.save()
                return redirect('settings')
        else:
            messages.info(request, 'Password Not Matching')
            return redirect('signup')
        
    else:
        return render(request, 'signup.html')

def signin(request):
    
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = auth.authenticate(username=username, password=password)

        if user is not None:
            auth.login(request, user)
            return redirect('/')
        else:
            messages.info(request, 'Credentials Invalid')
            return redirect('signin')

    else:
        return render(request, 'signin.html')

@login_required(login_url='signin')
def logout(request):
    auth.logout(request)
    return redirect('signin')


@login_required(login_url='signin')
def delete(request, delete_id):
    post = Post.objects.get(pk=delete_id)
    post.delete()
    return redirect('profile', request.user.username)



class EditPostView(UpdateView):
    model = Post
    template_name = 'edit.html'
    form_class = EditForm
    success_url='/'




@login_required(login_url='signin')
def pref(request):
    form_class = PrefForm
    form = form_class(request.POST or None)

    if request.method == 'POST':
        
        user_profile = Profile.objects.get(user=request.user)
        pref = request.POST.get('pref')
        if pref == 'on':
            pref = True
        else:
            pref = False
        user_profile.pref = pref
        user_profile.save()
        return render(request, 'pref.html',{'form':form,'pref':pref})

    else:
        return render(request, 'pref.html',{'form':form})



def data(request):
    response = HttpResponse(content_type='text/csv')
    response['Contetnt-Disposition'] = 'attachments; filename=user_data.csv'
    writer = csv.writer(response)
    users = User.objects.all()
    writer.writerow(['Username','Email','Date joined'])
    for user in users:
        writer.writerow([user.username, user.email, user.date_joined])
    return response
    


