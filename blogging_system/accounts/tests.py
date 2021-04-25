from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch
from .forms import SignUpForm
from .models import User,Profile
from django.http import JsonResponse
from .views import UserSignUpView

# Create your tests here.
def post(self, request):
        user_form = SignUpForm(request.POST)
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
                new_user.is_active = True
                new_user.save()
                profile = Profile(user=new_user)
                profile.save()
                
             
                return JsonResponse(status=200,data={"message":"  Successfully SignUp! Please activate your account mail has been send to your mail box! "})
        else:

           return JsonResponse(status=403,data={"message":"  Email has been registered already!!!"})


class UserInvalidRegistrationTestCase(TestCase):
    def setUp(self):
        self.user_data = {
            "username": "test@testuser.com",
            "email": "test@testuser.com",
            "password": "test@testuser.com",
            "password2": "test@testuser.com",
        }
        self.register_url_email = reverse('accounts:signup')
    
    @patch.object(UserSignUpView, "post", post)
    def test_user_valid_registration_by_email(self):
        """
        Test for missing field and duplicate registration test
        """
        user_data = self.user_data.copy()

        response = self.client.post(self.register_url_email, data=user_data)

        # missing field test
        self.assertEqual(response.status_code, 200)

        