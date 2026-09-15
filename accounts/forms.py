from django import forms
from django.contrib.auth import password_validation
from django.core.validators import RegexValidator, validate_email

from .models import User, Profile

phone_validator = RegexValidator(r"^09\d{9}$", "شماره تلفن معتبر نیست (مثال: 09123456789)")


class RegisterForm(forms.Form):

    phone_number = forms.CharField(validators=[phone_validator], widget=forms.TextInput(
        attrs={"class": "form-control", "placeholder": "09123456789", "dir": "ltr"}))
    email = forms.EmailField(widget=forms.EmailInput(
        attrs={"class": "form-control", "placeholder": "you@example.com", "dir": "ltr"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control"}))
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control"}))

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password") and cleaned.get("password_confirm"):
            if cleaned["password"] != cleaned["password_confirm"]:
                raise forms.ValidationError("رمز عبور و تکرار آن یکسان نیستند")
            password_validation.validate_password(cleaned["password"])
        return cleaned

    def clean_phone_number(self):
        phone = self.cleaned_data["phone_number"]
        if User.objects.filter(phone_number=phone, is_verified=True).exists():
            raise forms.ValidationError("این شماره قبلا ثبت‌نام کرده است")
        return phone

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email, is_verified=True).exists():
            raise forms.ValidationError("این ایمیل قبلاً استفاده شده است")
        return email


class QuickRegisterForm(forms.Form):

    phone_number = forms.CharField(validators=[phone_validator], widget=forms.TextInput(
        attrs={"class": "form-control", "placeholder": "09123456789", "dir": "ltr"}))
    email = forms.EmailField(widget=forms.EmailInput(
        attrs={"class": "form-control", "placeholder": "you@example.com", "dir": "ltr"}))

    def clean_phone_number(self):
        phone = self.cleaned_data["phone_number"]
        if User.objects.filter(phone_number=phone, is_verified=True).exists():
            raise forms.ValidationError("این شماره قبلا ثبت‌نام کرده است")
        return phone

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email, is_verified=True).exists():
            raise forms.ValidationError("این ایمیل قبلاً استفاده شده است")
        return email


class OTPVerifyForm(forms.Form):
    code = forms.CharField(max_length=6, widget=forms.TextInput(
        attrs={"class": "form-control text-center", "dir": "ltr", "autofocus": True,
               "placeholder": "------", "maxlength": "6"}))


class PhoneOnlyForm(forms.Form):
    identifier = forms.CharField(label="شماره تلفن یا ایمیل", widget=forms.TextInput(
        attrs={"class": "form-control", "placeholder": "09123456789 یا you@example.com", "dir": "ltr"}))

    def clean_identifier(self):
        value = self.cleaned_data["identifier"].strip()
        if "@" in value:
            validate_email(value)
        else:
            phone_validator(value)
        return value


class LoginForm(forms.Form):
    identifier = forms.CharField(label="شماره تلفن یا ایمیل", widget=forms.TextInput(
        attrs={"class": "form-control", "placeholder": "09123456789 یا you@example.com", "dir": "ltr"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control"}))


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["full_name", "avatar", "avatar_pos_x", "avatar_pos_y", "national_code", "gender", "address"]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control"}),
            "avatar": forms.FileInput(attrs={"class": "form-control", "accept": "image/*", "id": "id_avatar"}),
            "avatar_pos_x": forms.HiddenInput(attrs={"id": "id_avatar_pos_x"}),
            "avatar_pos_y": forms.HiddenInput(attrs={"id": "id_avatar_pos_y"}),
            "national_code": forms.TextInput(attrs={"class": "form-control", "dir": "ltr"}),
            "gender": forms.Select(attrs={"class": "form-select"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["full_name"].required = True


class EmailChangeForm(forms.Form):
    email = forms.EmailField(
        label="ایمیل",
        widget=forms.EmailInput(attrs={"class": "form-control", "dir": "ltr"}),
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields["email"].initial = user.email

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError("این ایمیل قبلاً استفاده شده است.")
        return email


class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(label="رمز عبور فعلی", widget=forms.PasswordInput(attrs={"class": "form-control"}))
    new_password = forms.CharField(label="رمز عبور جدید", widget=forms.PasswordInput(attrs={"class": "form-control"}))
    new_password_confirm = forms.CharField(label="تکرار رمز عبور جدید", widget=forms.PasswordInput(attrs={"class": "form-control"}))

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data["old_password"]
        if self.user is not None and not self.user.check_password(old_password):
            raise forms.ValidationError("رمز عبور فعلی اشتباه است.")
        return old_password

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("new_password") and cleaned.get("new_password_confirm"):
            if cleaned["new_password"] != cleaned["new_password_confirm"]:
                raise forms.ValidationError("رمز عبور جدید و تکرار آن یکسان نیستند")
            password_validation.validate_password(cleaned["new_password"], user=self.user)
        return cleaned


class RequestPasswordResetForm(forms.Form):
    phone_number = forms.CharField(validators=[phone_validator], widget=forms.TextInput(
        attrs={"class": "form-control", "dir": "ltr"}))


class RequestPasswordResetByEmailForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(
        attrs={"class": "form-control", "dir": "ltr", "placeholder": "you@example.com"}))


class SetNewPasswordForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control"}))
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control"}))

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password") != cleaned.get("password_confirm"):
            raise forms.ValidationError("رمز عبور و تکرار آن یکسان نیستند")
        if cleaned.get("password"):
            password_validation.validate_password(cleaned["password"])
        return cleaned



from django.contrib.auth.forms import UserCreationForm as _BaseUserCreationForm
from django.contrib.auth.forms import UserChangeForm as _BaseUserChangeForm


class AdminUserCreationForm(_BaseUserCreationForm):
    class Meta(_BaseUserCreationForm.Meta):
        model = User
        fields = ("email", "phone_number")
        field_classes = {}


class AdminUserChangeForm(_BaseUserChangeForm):
    class Meta(_BaseUserChangeForm.Meta):
        model = User
        fields = "__all__"
