from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db.models import Q, Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views import View

from accounts.forms import LoginForm, PhoneOnlyForm
from accounts.services import issue_otp, find_user_by_identifier

from .forms import WorkingHourForm, DoctorProfileForm, DoctorSearchForm
from .mixins import DoctorRequiredMixin
from .models import Doctor, Specialty, WorkingHour, TimeSlot
from .services import generate_time_slots
from payments.models import Transaction


class DoctorLoginView(View):

    template_name = "doctors/login.html"

    def get(self, request):
        return render(request, self.template_name, {"form": LoginForm()})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            target = find_user_by_identifier(form.cleaned_data["identifier"])
            user = None
            if target is not None:
                user = authenticate(request, username=target.email,
                                     password=form.cleaned_data["password"])
            if user is not None:
                if not user.is_doctor:
                    messages.error(request, "این حساب پزشک نیست. لطفاً از صفحه‌ی ورود کاربران اقدام کنید.")
                    return render(request, self.template_name, {"form": form})
                if not user.is_verified:
                    issue_otp(user, "login")
                    request.session["otp_user_id"] = user.id
                    request.session["otp_purpose"] = "login"
                    return redirect("accounts:verify_otp")
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                return redirect("doctors:dashboard")
            messages.error(request, "شماره تلفن/ایمیل یا رمز عبور اشتباه است.")
        return render(request, self.template_name, {"form": form})


class DoctorOTPLoginRequestView(View):

    template_name = "doctors/otp_login.html"

    def get(self, request):
        return render(request, self.template_name, {"form": PhoneOnlyForm()})

    def post(self, request):
        form = PhoneOnlyForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data["identifier"]
            user = find_user_by_identifier(identifier)
            if not user:
                messages.error(request, "کاربری با این شماره/ایمیل یافت نشد.")
                return render(request, self.template_name, {"form": form})
            if not user.is_doctor:
                messages.error(
                    request,
                    "این حساب متعلق به پزشک نیست. لطفاً از صفحه‌ی ورود کاربران اقدام کنید.",
                )
                return render(request, self.template_name, {"form": form})
            issue_otp(user, "otp_login", channel="sms")
            request.session["otp_user_id"] = user.id
            request.session["otp_purpose"] = "otp_login"
            messages.info(request, "کد یکبار مصرف برای شما ارسال شد.")
            return redirect("accounts:verify_otp")
        return render(request, self.template_name, {"form": form})


class HomeView(View):
    def get(self, request):
        top_doctors = cache.get("home_top_doctors")
        if top_doctors is None:
            top_doctors = list(
                Doctor.objects.filter(is_active=True)
                .select_related("profile", "specialty")
                .order_by("-id")[:12]
            )
            cache.set("home_top_doctors", top_doctors, 60 * 10)  # ۱۰ دقیقه
        specialties = Specialty.objects.all()[:8]
        return render(request, "doctors/home.html", {
            "top_doctors": top_doctors, "specialties": specialties,
        })


class SearchDoctorsView(View):
    def get(self, request):
        form = DoctorSearchForm(request.GET or None)
        doctors = Doctor.objects.filter(is_active=True).select_related("profile", "specialty")

        q = request.GET.get("q", "").strip()
        specialty_id = request.GET.get("specialty", "").strip()

        if q:
            doctors = doctors.filter(
                Q(profile__full_name__icontains=q) | Q(specialty__name__icontains=q)
            )
        if specialty_id:
            doctors = doctors.filter(specialty_id=specialty_id)

        specialties = Specialty.objects.all()
        return render(request, "doctors/search.html", {
            "form": form, "doctors": doctors, "specialties": specialties,
            "selected_specialty": specialty_id,
        })


class DoctorDetailView(View):
    def get(self, request, pk):
        doctor = get_object_or_404(Doctor.objects.select_related("profile", "specialty"), pk=pk)
        now = timezone.localtime()
        slots = doctor.time_slots.filter(
            Q(status="free")
            & (Q(visit_date__gt=now.date())
               | Q(visit_date=now.date(), end_time__gt=now.time().replace(tzinfo=None)))
        ).order_by(
            "visit_date", "start_time")[:60]

        slots_by_date = {}
        for slot in slots:
            slots_by_date.setdefault(slot.visit_date, []).append(slot)

        from reviews.models import Review
        doctor_reviews = Review.objects.filter(
            appointment__time_slot__doctor=doctor).select_related(
            "appointment__patient__profile").order_by("-created_at")[:20]

        return render(request, "doctors/detail.html", {
            "doctor": doctor, "slots_by_date": slots_by_date, "reviews": doctor_reviews,
        })


class DashboardView(LoginRequiredMixin, DoctorRequiredMixin, View):
    login_url = "accounts:login"

    def get(self, request):
        doctor = request.user.profile.doctor
        today = timezone.now().date()
        upcoming = TimeSlot.objects.filter(doctor=doctor, status="booked",
                                            visit_date__gte=today).select_related(
            "appointment__patient__profile").order_by("visit_date", "start_time")[:10]
        earnings = Transaction.objects.filter(
            appointment__time_slot__doctor=doctor,
            status="success",
        ).aggregate(
            payments=Sum("amount", filter=Q(type="payment")),
            refunds=Sum("amount", filter=Q(type="refund")),
        )
        total_earnings = (earnings["payments"] or 0) - (earnings["refunds"] or 0)
        stats = {
            "total_slots": doctor.time_slots.count(),
            "free_slots": doctor.time_slots.filter(status="free", visit_date__gte=today).count(),
            "booked_slots": doctor.time_slots.filter(status="booked", visit_date__gte=today).count(),
            "rating": doctor.average_rating,
            "review_count": doctor.review_count,
            "earnings": total_earnings,
            "earnings_display": f"{total_earnings:,.0f}",
        }
        return render(request, "doctors/dashboard.html", {
            "doctor": doctor, "upcoming": upcoming, "stats": stats,
        })


class DoctorTransactionsView(LoginRequiredMixin, DoctorRequiredMixin, View):
    login_url = "accounts:login"

    def get(self, request):
        doctor = request.user.profile.doctor
        transactions = Transaction.objects.filter(
            appointment__time_slot__doctor=doctor,
            status="success",
            type__in=["payment", "refund"],
        ).select_related(
            "appointment__patient__profile",
            "appointment__time_slot",
        ).order_by("-created_at")
        for transaction in transactions:
            transaction.amount_display = f"{transaction.amount:,.0f}"
        return render(request, "doctors/transactions.html", {
            "doctor": doctor,
            "transactions": transactions,
        })


class DoctorReviewsView(LoginRequiredMixin, DoctorRequiredMixin, View):
    login_url = "accounts:login"

    def get(self, request):
        doctor = request.user.profile.doctor
        from reviews.models import Review

        reviews = Review.objects.filter(
            appointment__time_slot__doctor=doctor,
        ).select_related(
            "appointment__patient__profile",
            "appointment__time_slot",
        ).order_by("-created_at")
        return render(request, "doctors/reviews.html", {
            "doctor": doctor,
            "reviews": reviews,
        })


class ProfileSettingsView(LoginRequiredMixin, DoctorRequiredMixin, View):
    login_url = "accounts:login"

    def get(self, request):
        doctor = request.user.profile.doctor
        form = DoctorProfileForm(instance=doctor)
        return render(request, "doctors/profile_settings.html", {"form": form, "doctor": doctor})

    def post(self, request):
        doctor = request.user.profile.doctor
        form = DoctorProfileForm(request.POST, instance=doctor)
        if form.is_valid():
            form.save()
            messages.success(request, "اطلاعات پزشک بروزرسانی شد.")
            return redirect("doctors:profile_settings")
        return render(request, "doctors/profile_settings.html", {"form": form, "doctor": doctor})


class WorkingHoursView(LoginRequiredMixin, DoctorRequiredMixin, View):
    login_url = "accounts:login"
    template_name = "doctors/working_hours.html"

    def _context(self, request, doctor, form):
        hours = doctor.working_hours.all()
        today = timezone.now().date()
        slots = doctor.time_slots.filter(visit_date__gte=today).order_by("visit_date", "start_time")[:200]

        slots_by_date = {}
        for slot in slots:
            slots_by_date.setdefault(slot.visit_date, []).append(slot)

        return {"form": form, "hours": hours, "doctor": doctor, "slots_by_date": slots_by_date}

    def get(self, request):
        doctor = request.user.profile.doctor
        form = WorkingHourForm(doctor=doctor)
        return render(request, self.template_name, self._context(request, doctor, form))

    def post(self, request):
        doctor = request.user.profile.doctor
        form = WorkingHourForm(request.POST, doctor=doctor)
        if form.is_valid():
            wh = form.save(commit=False)
            wh.doctor = doctor
            wh.save()
            messages.success(request, "ساعت کاری اضافه شد.")
            return redirect("doctors:working_hours")
        return render(request, self.template_name, self._context(request, doctor, form))


class DeleteWorkingHourView(LoginRequiredMixin, DoctorRequiredMixin, View):
    login_url = "accounts:login"

    def post(self, request, pk):
        doctor = request.user.profile.doctor
        wh = get_object_or_404(WorkingHour, pk=pk, doctor=doctor)
        wh.delete()
        messages.success(request, "ساعت کاری حذف شد.")
        return redirect("doctors:working_hours")


class DeleteTimeSlotView(LoginRequiredMixin, DoctorRequiredMixin, View):


    login_url = "accounts:login"

    def post(self, request, pk):
        doctor = request.user.profile.doctor
        slot = get_object_or_404(TimeSlot, pk=pk, doctor=doctor)
        if slot.status != "free":
            messages.error(request, "این نوبت رزرو شده و قابل حذف نیست.")
        else:
            slot.delete()
            messages.success(request, "نوبت خالی حذف شد.")
        return redirect("doctors:working_hours")


class GenerateSlotsView(LoginRequiredMixin, DoctorRequiredMixin, View):
    login_url = "accounts:login"

    def post(self, request):
        doctor = request.user.profile.doctor
        created = generate_time_slots(doctor, days_ahead=14)
        if created:
            messages.success(request, f"{created} نوبت خالی جدید برای ۱۴ روز آینده ساخته شد.")
        else:
            messages.info(request, "نوبت جدیدی برای ساخت وجود نداشت (همه از قبل موجود بودند).")
        return redirect("doctors:working_hours")


class ManageSlotsView(LoginRequiredMixin, DoctorRequiredMixin, View):
    login_url = "accounts:login"

    def get(self, request):
        doctor = request.user.profile.doctor
        from appointments.services import auto_complete_past_appointments
        auto_complete_past_appointments(doctor=doctor)
        slots = doctor.time_slots.all().order_by("-visit_date", "-start_time")[:100]
        return render(request, "doctors/manage_slots.html", {"slots": slots, "doctor": doctor})


class CompleteAppointmentView(LoginRequiredMixin, DoctorRequiredMixin, View):
    login_url = "accounts:login"

    def post(self, request, pk):
        from appointments.models import Appointment
        from appointments.services import complete_appointment as do_complete

        doctor = request.user.profile.doctor
        appointment = get_object_or_404(Appointment, pk=pk, time_slot__doctor=doctor)
        try:
            do_complete(appointment)
            messages.success(request, "نوبت به‌عنوان انجام‌شده علامت‌گذاری شد.")
        except ValidationError as e:
            messages.error(request, str(e))
        return redirect("doctors:manage_slots")
