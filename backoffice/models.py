from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, URLValidator
from django.db import models
from django.conf import settings


class LearningEntry(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField()
    draft = models.JSONField(default=list)
    ideas = models.JSONField(default=list)
    saved_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "date"], name="one_learning_day_per_user")]
        ordering = ["-date"]


class Visitor(models.Model):
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    visits = models.PositiveIntegerField(default=1)
    identifier = models.CharField(max_length=64, unique=True)
    country = models.CharField(max_length=2, blank=True)
    region = models.CharField(max_length=100, blank=True)
    first_seen = models.DateTimeField(auto_now_add=True)


class Application(models.Model):
    class WorkArrangement(models.TextChoices):
        HYBRID = "hybrid", "Hybrid"
        ON_SITE = "on_site", "On-site"
        REMOTE = "remote", "Fully remote"

    class Stage(models.TextChoices):
        APPLIED = "applied", "Applied"
        SCREENING = "screening", "Recruiter screening"
        FIRST = "first", "First round"
        SECOND = "second", "Second round"
        THIRD = "third", "Third round"
        FINAL = "final", "Final round"
        OFFER = "offer", "Offer"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        WITHDRAWN = "withdrawn", "Withdrawn"

    CLOSED = (Stage.ACCEPTED, Stage.REJECTED, Stage.WITHDRAWN)
    role = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    salary_offered = models.CharField(
        "salary offered", max_length=200, blank=True,
        help_text="Salary offered by the employer or recruiter, including currency and period (e.g. €55,000–€60,000 per year).",
    )
    company_website = models.URLField(blank=True, validators=[URLValidator(schemes=["http", "https"])])
    company_details = models.TextField(blank=True)
    posting_url = models.URLField(max_length=2048, blank=True, validators=[URLValidator(schemes=["http", "https"])])
    posting_details = models.TextField(blank=True)
    job_location = models.CharField(
        "job / office location", max_length=200, blank=True,
        help_text="Enter where you would work, such as Dublin, Dundalk, or the office address listed in the posting.",
    )
    work_arrangement = models.CharField(max_length=10, choices=WorkArrangement, blank=True)
    office_days_per_week = models.PositiveSmallIntegerField(
        blank=True, null=True, validators=[MaxValueValidator(5)],
        help_text="Enter 0 for fully remote, or leave blank if the number is unknown.",
    )
    stage = models.CharField(max_length=20, choices=Stage, default=Stage.APPLIED)
    interview_at = models.DateTimeField(blank=True, null=True)
    interview_details = models.TextField(blank=True)
    prep_questions = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.role} at {self.company}"

    def clean(self):
        super().clean()
        days = self.office_days_per_week
        if days is None:
            return

        if self.work_arrangement == self.WorkArrangement.REMOTE and days != 0:
            raise ValidationError({"office_days_per_week": "Fully remote roles have zero office days."})
        if self.work_arrangement == self.WorkArrangement.HYBRID and days not in range(1, 5):
            raise ValidationError({"office_days_per_week": "Enter 1 to 4 office days for a hybrid role."})
        if self.work_arrangement == self.WorkArrangement.ON_SITE and days == 0:
            raise ValidationError({"office_days_per_week": "Enter at least one office day for an on-site role."})


class Document(models.Model):
    class Kind(models.TextChoices):
        CV = "cv", "CV"
        COVER = "cover", "Cover letter"
        JOB_DESCRIPTION = "job_desc", "Job description"

    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="documents")
    kind = models.CharField(max_length=8, choices=Kind)
    filename = models.CharField(max_length=200)
    content = models.BinaryField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["application", "kind"], name="one_document_per_kind")]


class Notification(models.Model):
    category = models.CharField(max_length=25, default="application_updates")
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    subject = models.CharField(max_length=450)
    body = models.TextField()
    due_at = models.DateTimeField(db_index=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    cancelled = models.BooleanField(default=False)


class MemberPreferences(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    new_jobs = models.BooleanField(default=False)
    application_updates = models.BooleanField(default=False)
    interviews = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Email notification preferences"


class NotificationDelivery(models.Model):
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name="deliveries")
    email = models.EmailField()
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["notification", "email"], name="unique_notification_recipient")]


class AppEvent(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    level = models.CharField(max_length=10, default="INFO")
    category = models.CharField(max_length=30, default="activity")
    message = models.CharField(max_length=1000)
    actor_id = models.PositiveBigIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-id"]
