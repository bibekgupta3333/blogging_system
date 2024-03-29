from .models import Profile, ResetToken
from django.urls import reverse
from django.contrib import messages
from django.http import HttpResponse
from django.views.generic import View
from django.core.mail import EmailMessage
from django.contrib.auth.models import User
from .tokens import account_activation_token
from django.shortcuts import render, redirect
from django.template.loader import get_template
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.contrib.auth.hashers import check_password
from django.contrib.auth.decorators import login_required
from django.utils.encoding import force_bytes, force_text
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.sites.shortcuts import get_current_site
from .forms import LoginForm, SignUpForm, EditForm, ProfileEditForm
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode


@method_decorator(login_required, name="dispatch")
class EditView(View):
    def get(self, request):
        if bool(Profile.objects.filter(user=request.user)) is False:
            obj = Profile(user=request.user)
            obj.save()
        user_form = EditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=request.user.profile)
        return render(
            request,
            "accounts/edit.html",
            {"user_form": user_form, "profile_form": profile_form},
        )

    def post(self, request):
        user_form = EditForm(instance=request.user, data=request.POST)
        profile_form = ProfileEditForm(
            files=request.FILES, instance=request.user.profile, data=request.POST
        )

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            print("---------------------------------------")
            print(profile_form.cleaned_data["photo"])
            print("---------------------------------------")
            profile_form.save()
            messages.success(request, " Your profile has been updated successfully")
            return redirect("accounts:edit")
        else:
            messages.error(
                request,
                "   Error occured while updating your profile, Please update again",
            )
        return render(
            request,
            "accounts/edit.html",
            {"user_form": user_form, "profile_form": profile_form},
        )


class UserSignUpView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect("accounts:edit")
        user_form = SignUpForm()
        return render(request, "accounts/signup.html", {"user_form": user_form})

    def post(self, request):
        user_form = SignUpForm(request.POST)
        print(user_form)
        try:
            already_user = User.objects.all().filter(email=user_form["email"].value())[
                0
            ]

        except:
            already_user = None
        print(already_user, user_form["email"].value())
        if already_user is None:
            if user_form.is_valid():
                new_user = user_form.save(commit=False)
                new_user.set_password(user_form.cleaned_data["password"])
                new_user.is_active = False
                new_user.save()
                profile = Profile(user=new_user)
                profile.save()
                current_site = get_current_site(request)
                mail_subject = "Activate your blog account."
                message = render_to_string(
                    "activate_email.html",
                    {
                        "user": new_user,
                        "domain": current_site.domain,
                        "uid": urlsafe_base64_encode(force_bytes(new_user.pk)),
                        "token": account_activation_token.make_token(new_user),
                    },
                )
                print(
                    urlsafe_base64_encode(force_bytes(new_user.pk)),
                    account_activation_token.make_token(new_user),
                )
                to_email = user_form.cleaned_data.get("email")
                email = EmailMessage(mail_subject, message, to=[to_email])
                email.send()
                messages.success(
                    request,
                    "  Successfully SignUp! Please activate your account mail has been send to your mail box! ",
                )
                return redirect("accounts:login")
        else:
            messages.error(request, "   Email has been registered already!!!")
            return redirect("accounts:signup")
        return render(request, "accounts/signup.html", {"user_form": user_form})


class ActivateView(View):
    def get(self, request, uidb64, token):
        try:
            uid = force_text(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        if user is not None and account_activation_token.check_token(user, token):
            user.is_active = True
            user.save()
            messages.success(
                request,
                "  Thank you for your email confirmation. Now you can login to your account.",
            )
            return redirect("accounts:login")

        else:
            messages.error(
                request, "   Activation link is invalid!.", fail_silently=True
            )
            return redirect("accounts:login")


class UserLoginView(View):
    def get(self, request):
        form = LoginForm()
        if request.user.is_authenticated:
            return redirect("posts:list")
        return render(request, "accounts/login.html", {"form": form})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            username = User.objects.all().filter(email=cd["email"])
            if username:
                user = authenticate(
                    request, username=username[0], password=cd["password"]
                )
                print(user)
                if user is not None:
                    if user.is_active:
                        login(request, user)
                        messages.success(request, " Authenticated Successfully")
                        return redirect(
                            "posts:user_post_list",
                            request.user.username,
                            request.user.id,
                        )
                    else:

                        messages.error(
                            request,
                            "   Your account is not activated, Please check your mail",
                        )
                        return redirect("accounts:login")

                else:
                    messages.error(request, "   Your have used wrong password")
                    return redirect("accounts:login")
            else:
                messages.error(request, "   Wrong Email has been please try again!!!")
                return redirect("accounts:login")
        return render(request, "accounts/login.html", {"form": form})


@method_decorator(login_required, name="dispatch")
class UserLogoutView(View):
    def get(self, request):
        logout(request)
        messages.success(request, " You have Successfully logout from account")
        return redirect("accounts:login")

from .forms import EmailForm ,PasswordResetForm
from .models import ResetToken
import uuid
class ResetPasswordTokenView(View):
    
    def get(self,request):
        return render(request,"accounts/reset_initate.html",{"form":EmailForm()})

    def post(self,request):
        form=EmailForm(request.POST)
        email_valid=form.is_valid()
        if not email_valid:
            messages.error(request, "Email is not valid")
            return redirect("accounts:reset_password_initiate")
        email=form.cleaned_data["email"]
        email_exist=User.objects.filter(email=email).exists()
        if not email_exist:
            messages.error(request, "Email not found please sign up")
            return redirect("accounts:reset_password_initiate")
        token=ResetToken(token=str(uuid.uuid4()),email=email)
        token.save()
        user=User.objects.filter(email=email).first()
        mail_subject = "Reset Your Password."
        message = render_to_string(
            "activate_reset_password.html",
            {
                "user": user,
                "domain": get_current_site(request).domain,
                "token": token.token,
            },
        )
        email = EmailMessage(mail_subject, message, to=[email])
        email.send()
        messages.success(request, "Please check your mail to reset your account")
        return redirect("accounts:login")
    

class ResetPasswordView(View):
    
    def get(self,request,token):
        return render(request,"accounts/password_reset.html",{"form":PasswordResetForm()})

    def post(self,request,token):
        form=PasswordResetForm(request.POST)
        password_valid=form.is_valid()
        if not password_valid:
            messages.error(request, "Both password does not match")
            return redirect("accounts:login")
        token=ResetToken.objects.filter(token=token)
        if not token.exists():
            messages.error(request, "Token is invalid")
            return redirect("accounts:login")
        if token.first().used:
            messages.error(request, "Token used already!")
            return redirect("accounts:login")
        reset_token=token.first()
        reset_token.used=True
        user= User.objects.filter(email=reset_token.email).first()
        user.set_password(form.cleaned_data["password"])
        user.save()
        reset_token.save()
        messages.success(request, "Password reset successful")
        return redirect("accounts:login")



        


        
            
        
        
        

