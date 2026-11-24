from pathlib import Path
from io import BytesIO
import zipfile
from xml.parsers.expat import ExpatError

from django import forms
from django.contrib import admin, messages
from django.db.models import Count, Sum
from django.http import Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from django.template.response import TemplateResponse
from django.template.loader import render_to_string
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils import timezone
from django.utils.http import content_disposition_header
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied
import mammoth

from .job_import import ImportError as JobImportError, import_posting
from .models import Application, Document, InterviewQuestion, Visitor
from .notifications import queue_notifications
from .learnings import learnings, learning_progress
from .logs import logs


class PortfolioAdmin(admin.AdminSite):
    site_header = "Sujil Mani"
    site_title = "Portfolio admin"
    index_title = "Dashboard"
    index_template = "admin/dashboard.html"

    def get_urls(self):
        return [
            path("logs/", self.admin_view(lambda request: logs(self, request)), name="logs"),
            path("logs/data/", self.admin_view(lambda request: logs(self, request, data=True)), name="logs_data"),
            path("learnings/", self.admin_view(lambda request: learnings(self, request)), name="learnings"),
            path("interview-question/<int:pk>/document/", self.admin_view(self.interview_question_document),
                 name="interview_question_document"),
            path("interview-question/<int:pk>/preview/", self.admin_view(self.interview_question_preview),
                 name="interview_question_preview"),
            path("visitor-map/", self.admin_view(self.visitor_map), name="visitor_map"),
            path("visitor-map/data/", self.admin_view(self.visitor_map_data), name="visitor_map_data"),
            *super().get_urls(),
        ]

    def interview_question_document(self, request, pk):
        question = InterviewQuestion.objects.filter(pk=pk).first()
        model_admin = self._registry[InterviewQuestion]
        if question is None or not model_admin.has_view_or_change_permission(request, question):
            raise Http404
        response = HttpResponse(question.content, content_type="application/octet-stream")
        response["Content-Disposition"] = content_disposition_header(True, question.filename)
        response["X-Content-Type-Options"] = "nosniff"
        return response

    def interview_question_preview(self, request, pk):
        question = InterviewQuestion.objects.filter(pk=pk).first()
        model_admin = self._registry[InterviewQuestion]
        if question is None or not model_admin.has_view_or_change_permission(request, question):
            raise Http404

        filename = question.filename.lower()
        if filename.endswith(".pdf") and question.content.startswith(b"%PDF-"):
            response = HttpResponse(question.content, content_type="application/pdf")
            response["Content-Disposition"] = content_disposition_header(False, question.filename)
            response["X-Content-Type-Options"] = "nosniff"
            response["X-Frame-Options"] = "SAMEORIGIN"
            response["Cache-Control"] = "private, no-store"
            return response

        if filename.endswith(".docx") and question.content.startswith(b"PK\x03\x04"):
            try:
                result = mammoth.convert_to_html(BytesIO(question.content))
            except (zipfile.BadZipFile, KeyError, ExpatError):
                return HttpResponse(
                    "This DOCX file is invalid and cannot be previewed.",
                    status=422,
                    content_type="text/plain; charset=utf-8",
                )
            response = HttpResponse(
                render_to_string("admin/interview_question_document.html", {
                    "title": question.filename,
                    "content": result.value,
                }),
                content_type="text/html; charset=utf-8",
            )
            response["Content-Security-Policy"] = (
                "default-src 'none'; img-src data:; style-src 'unsafe-inline'; "
                "font-src data:; base-uri 'none'; form-action 'none'; frame-ancestors 'self'"
            )
            response["X-Content-Type-Options"] = "nosniff"
            response["X-Frame-Options"] = "SAMEORIGIN"
            response["Cache-Control"] = "private, no-store"
            return response

        raise Http404

    def check_visitor_permission(self, request):
        if not request.user.has_perm("backoffice.view_visitor"):
            raise PermissionDenied

    def visitor_map(self, request):
        self.check_visitor_permission(request)
        request.current_app = self.name
        return TemplateResponse(request, "admin/visitor_map.html", {
            **self.each_context(request), "title": "Visitor world map",
        })

    def visitor_map_data(self, request):
        self.check_visitor_permission(request)
        return JsonResponse({"countries": list(Visitor.objects.values("country").annotate(
            visitors=Count("pk"), visits=Sum("visits")).order_by("country"))})

    def index(self, request, extra_context=None):
        locations = Visitor.objects.values("country", "region").annotate(visitors=Count("pk"))
        countries = Visitor.objects.values("country").annotate(visitors=Count("pk"))
        applications = Application.objects.all()
        can_view_interviews = request.user.has_perm("backoffice.view_application") or request.user.has_perm("backoffice.change_application")
        can_view_questions = (
            request.user.has_perm("backoffice.view_interviewquestion")
            or request.user.has_perm("backoffice.change_interviewquestion")
        )
        can_add_questions = request.user.has_perm("backoffice.add_interviewquestion")
        upcoming = applications.filter(interview_at__gte=timezone.now()).exclude(
            stage__in=Application.CLOSED).order_by("interview_at", "pk")[:3] if can_view_interviews else []
        return super().index(request, {
            "learning": learning_progress(request.user),
            "can_view_interviews": can_view_interviews,
            "upcoming_interviews": upcoming,
            "can_view_interview_questions": can_view_questions,
            "can_manage_interview_questions": can_view_questions or can_add_questions,
            "interview_questions": InterviewQuestion.objects.only(
                "id", "employer", "interview_date", "filename"
            )[:3] if can_view_questions else [],
            "visitor_count": Visitor.objects.count(),
            "countries": countries.order_by("-visitors", "country"),
            "locations": locations.exclude(region="").order_by("-visitors", "country", "region"),
            "active_count": applications.exclude(stage__in=Application.CLOSED).count(),
            "application_count": applications.count(),
            "active_url": reverse("admin:backoffice_application_changelist") + "?" + "stage__in=" + ",".join(v for v, _ in Application.Stage.choices if v not in Application.CLOSED),
            **(extra_context or {}),
        })


site = PortfolioAdmin(name="admin")


class InterviewQuestionForm(forms.ModelForm):
    document = forms.FileField(
        label="Question document",
        required=False,
        widget=forms.FileInput(attrs={"accept": ".pdf,.docx"}),
        help_text="PDF or DOCX, up to 5 MB.",
    )

    class Meta:
        model = InterviewQuestion
        fields = ("employer", "interview_date")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["document"].required = self.instance.pk is None

    def clean_document(self):
        upload = self.cleaned_data.get("document")
        if not upload:
            return upload

        extension = Path(upload.name).suffix.lower()
        signature = upload.read(5)
        upload.seek(0)
        valid = (extension == ".pdf" and signature == b"%PDF-") or (
            extension == ".docx" and signature.startswith(b"PK\x03\x04")
        )
        if upload.size > 5 * 1024 * 1024 or not valid:
            raise forms.ValidationError("Choose a valid PDF or DOCX file up to 5 MB.")
        return upload


@admin.register(InterviewQuestion, site=site)
class InterviewQuestionAdmin(admin.ModelAdmin):
    form = InterviewQuestionForm
    change_list_template = "admin/interviewquestion_change_list.html"
    fields = ("employer", "interview_date", "document", "saved_document")
    readonly_fields = ("saved_document",)
    list_display = ("employer", "interview_date", "preview_button", "document_link")
    list_display_links = ("employer",)
    list_filter = ("interview_date",)
    search_fields = ("employer", "filename")
    ordering = ("-interview_date", "employer")

    @admin.display(description="Saved document")
    def saved_document(self, obj):
        if not obj or not obj.pk:
            return "Save an interview question to attach a document."
        return format_html(
            '<a href="{}">{}</a>',
            reverse("admin:interview_question_document", args=[obj.pk]),
            obj.filename,
        )

    @admin.display(description="Document")
    def document_link(self, obj):
        return format_html(
            '<a href="{}">{}</a>',
            reverse("admin:interview_question_document", args=[obj.pk]),
            obj.filename,
        )

    @admin.display(description="Preview")
    def preview_button(self, obj):
        return format_html(
            '<button type="button" class="interview-question-preview-button" '
            'data-interview-question-preview="{}" data-document-title="{}" '
            'data-document-filename="{}" data-document-download="{}" '
            'aria-label="Preview {}" title="Preview document" aria-haspopup="dialog">'
            '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
            '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z"/>'
            '<circle cx="12" cy="12" r="3"/></svg></button>',
            reverse("admin:interview_question_preview", args=[obj.pk]),
            obj.filename,
            obj.filename,
            reverse("admin:interview_question_document", args=[obj.pk]),
            obj.filename,
        )

    def save_model(self, request, obj, form, change):
        upload = form.cleaned_data.get("document")
        if upload:
            obj.filename = Path(upload.name).name[:200]
            obj.content = upload.read()
        super().save_model(request, obj, form, change)


class ApplicationForm(forms.ModelForm):
    cv = forms.FileField(
        label="CV", required=False,
        widget=forms.FileInput(attrs={"accept": ".pdf,.docx"}),
        help_text="Optional. PDF or DOCX, up to 5 MB.",
    )
    cover = forms.FileField(
        label="Cover letter", required=False,
        widget=forms.FileInput(attrs={"accept": ".pdf,.docx"}),
        help_text="Optional. PDF or DOCX, up to 5 MB.",
    )
    job_desc = forms.FileField(
        label="Job description file", required=False,
        widget=forms.FileInput(attrs={"accept": ".pdf,.docx"}),
        help_text="Optional. PDF or DOCX, up to 5 MB.",
    )

    class Meta:
        model = Application
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        for field, _ in Document.Kind.choices:
            upload = cleaned.get(field)
            if not upload:
                continue
            extension = Path(upload.name).suffix.lower()
            signature = upload.read(5)
            upload.seek(0)
            valid = (extension == ".pdf" and signature == b"%PDF-") or (
                extension == ".docx" and signature.startswith(b"PK\x03\x04")
            )
            if upload.size > 5 * 1024 * 1024 or not valid:
                self.add_error(
                    field,
                    "The selected file must be a PDF or DOCX up to 5 MB. "
                    "Choose another file or leave this field empty and save again.",
                )
        return cleaned


@admin.register(Application, site=site)
class ApplicationAdmin(admin.ModelAdmin):
    form = ApplicationForm
    change_form_template = "admin/application_form.html"
    actions = ("edit_selected_application",)

    class Media:
        js = ("job-import.js", "application-documents.js")

    list_display = (
        "role_link", "company", "stage_badge", "job_location", "work_arrangement",
        "office_days_per_week", "interview_at", "updated_at",
    )
    list_display_links = None
    list_filter = ("stage", "work_arrangement")
    search_fields = ("role", "company", "job_location", "posting_details")
    ordering = ("-updated_at",)
    readonly_fields = ("saved_documents",)
    fieldsets = (
        ("Application", {"fields": ("role", "company", "salary_offered", "stage", "posting_url", "posting_details", "notes")}),
        ("Location and work arrangement", {
            "fields": ("job_location", "work_arrangement", "office_days_per_week"),
        }),
        ("Company", {"fields": ("company_website", "company_details")}),
        ("Interview", {"fields": ("interview_at", "interview_details", "prep_questions")}),
        ("Documents", {
            "fields": ("saved_documents", "job_desc", "cv", "cover"),
            "classes": ("application-document-fields",),
        }),
    )

    @admin.action(permissions=["change"], description="Edit selected application")
    def edit_selected_application(self, request, queryset):
        selected = list(queryset[:2])
        if request.POST.get("select_across") == "1" or len(selected) != 1:
            self.message_user(request, "Select one application to edit.", level=messages.WARNING)
            return None
        application = selected[0]
        if not self.has_change_permission(request, application):
            raise Http404
        return HttpResponseRedirect(reverse("admin:backoffice_application_change", args=[application.pk]))

    @admin.display(description="Role", ordering="role")
    def role_link(self, obj):
        return format_html('<a href="{}">{}</a>', reverse("admin:application_detail", args=[obj.pk]), obj.role)

    def changelist_view(self, request, extra_context=None):
        return super().changelist_view(request, {"title": "Job applications", **(extra_context or {})})

    def progress_context(self, obj):
        stages = [(value, label) for value, label in Application.Stage.choices
                  if value not in {Application.Stage.REJECTED, Application.Stage.WITHDRAWN}]
        current = next((index for index, (value, _) in enumerate(stages) if value == obj.stage), None)
        return {
            "application_progress": [
                {
                    "label": label,
                    "state": "closed" if current is None else (
                        "current" if index == current else "earlier" if index < current else "upcoming"
                    ),
                }
                for index, (_, label) in enumerate(stages)
            ],
            "application_stage_label": obj.get_stage_display(),
        }

    def render_change_form(self, request, context, add=False, change=False, form_url="", obj=None):
        if obj and not context.get("is_popup"):
            context.update(self.progress_context(obj))
        return super().render_change_form(request, context, add, change, form_url, obj)

    @admin.display(description="Stage", ordering="stage")
    def stage_badge(self, obj):
        return format_html(
            '<span class="application-stage" data-stage="{}">{}</span>',
            obj.stage, obj.get_stage_display(),
        )

    @admin.display(description="Saved documents")
    def saved_documents(self, obj):
        return render_to_string("admin/application_documents.html", {
            "documents": obj.documents.defer("content") if obj and obj.pk else (),
            "show_remove": True,
        })

    def get_urls(self):
        return [
            path("<int:pk>/detail/", self.admin_site.admin_view(self.detail), name="application_detail"),
            path("document/<int:pk>/preview/", self.admin_site.admin_view(self.preview_document),
                 name="preview_application_document"),
            path("document/<int:pk>/remove/", self.admin_site.admin_view(require_POST(self.remove_document)),
                 name="remove_application_document"),
            path("import-posting/", self.admin_site.admin_view(require_POST(self.import_job)), name="import_job_posting"),
            path("document/<int:pk>/", self.admin_site.admin_view(self.download), name="application_document"),
            *super().get_urls(),
        ]

    def detail(self, request, pk):
        application = self.get_object(request, str(pk))
        if application is None or not self.has_view_or_change_permission(request, application):
            raise Http404
        request.current_app = self.admin_site.name
        return TemplateResponse(request, "admin/application_detail.html", {
            **self.admin_site.each_context(request),
            **self.progress_context(application),
            "title": application.role,
            "application": application,
            "documents": application.documents.defer("content"),
            "can_edit": self.has_change_permission(request, application),
        })

    def remove_document(self, request, pk):
        document = Document.objects.select_related("application").defer("content").filter(pk=pk).first()
        if document is None or not self.has_change_permission(request, document.application):
            raise Http404
        document.delete()
        return JsonResponse({"removed": True})

    def import_job(self, request):
        if not (self.has_add_permission(request) or self.has_change_permission(request)):
            return JsonResponse({"error": "You do not have permission to import applications."}, status=403)
        url = request.POST.get("url", "").strip()
        if not url or len(url) > Application._meta.get_field("posting_url").max_length:
            return JsonResponse({"error": "Enter a valid public HTTPS posting URL."}, status=400)
        try:
            return JsonResponse({"fields": import_posting(url)})
        except JobImportError as error:
            return JsonResponse({"error": str(error)}, status=422)

    def download(self, request, pk):
        document = Document.objects.select_related("application").filter(pk=pk).first()
        if document is None or not self.has_view_or_change_permission(request, document.application):
            raise Http404
        response = HttpResponse(document.content, content_type="application/octet-stream")
        response["Content-Disposition"] = content_disposition_header(True, document.filename)
        return response

    def preview_document(self, request, pk):
        document = Document.objects.select_related("application").filter(pk=pk).first()
        if (document is None or not self.has_view_or_change_permission(request, document.application)
                or not document.filename.lower().endswith(".pdf") or not document.content.startswith(b"%PDF-")):
            raise Http404
        response = HttpResponse(document.content, content_type="application/pdf")
        response["Content-Disposition"] = content_disposition_header(False, document.filename)
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "SAMEORIGIN"
        return response

    def save_model(self, request, obj, form, change):
        # Django's change form wraps this save in a transaction.
        previous = Application.objects.select_for_update().filter(pk=obj.pk).first() if change else None
        super().save_model(request, obj, form, change)
        queue_notifications(obj, previous)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        for field, _ in Document.Kind.choices:
            upload = form.cleaned_data.get(field)
            documents = form.instance.documents
            if upload:
                documents.update_or_create(
                    kind=field, defaults={"filename": upload.name[:200], "content": upload.read()},
                )


from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from .models import MemberPreferences


class PreferencesInline(admin.StackedInline):
    model = MemberPreferences
    can_delete = False
    extra = 1
    max_num = 1


@admin.register(get_user_model(), site=site)
class MemberAdmin(UserAdmin):
    inlines = (PreferencesInline,)
    list_display = ("username", "email", "is_staff", "is_active")

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    has_add_permission = has_view_permission
    has_change_permission = has_view_permission
    has_delete_permission = has_view_permission


@admin.register(Visitor, site=site)
class VisitorAdmin(admin.ModelAdmin):
    def changelist_view(self, request, extra_context=None):
        from django.conf import settings
        if not settings.TRUST_GEO_HEADERS and (not settings.GEOIP_DATABASE_PATH or not Path(settings.GEOIP_DATABASE_PATH).is_file()):
            self.message_user(request, "Country lookup is not configured. Run update_geoip on the server, then resolve_visitor_countries to fill existing records.", level=messages.WARNING)
        return super().changelist_view(request, extra_context)

    list_display = ("ip_address", "country", "region", "visits", "first_seen", "last_seen")
    search_fields = ("ip_address", "country", "region")
    readonly_fields = ("identifier", "ip_address", "country", "region", "visits", "first_seen", "last_seen")
    list_filter = ("country", "region")
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
