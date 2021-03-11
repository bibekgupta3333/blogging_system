from taggit.models import Tag
from django.db.models import Q
from django.http import Http404
from django.conf import settings
from .models import Post
from comments.models import  Comment
from django.contrib import messages
from django.contrib.auth.models import User
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from .forms import PostForm, PostCreateForm
from comments.forms import CommentCreateForm
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.views.generic.edit import (
    ModelFormMixin,
    DeleteView,
    DeletionMixin,
    BaseDetailView,
    View,
)


class ListPostView(ListView):
    model = Post
    template_name = "posts/common_list.html"
    context_object_name = "objects"

    def get_queryset(self, *args, **kwargs):
        queryset = super(ListPostView, self).get_queryset(*args, **kwargs)
        queryset = queryset.filter(status="published")
        query = self.request.GET.get("q")
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(body__icontains=query)
                | Q(author__username=query)
                | Q(tags__name=query)
            )
            queryset = (
                queryset.order_by("-created").filter(status="published").distinct()
            )

        page = self.request.GET.get("page", 1)
        paginator = Paginator(queryset, 4)
        try:
            queryset = paginator.page(page)
        except PageNotAnInteger:
            queryset = paginator.page(1)
        except EmptyPage:
            queryset = paginator.page(paginator.num_pages)

        return queryset

    def get_context_data(self, *args, **kwargs):
        context = super(ListPostView, self).get_context_data(*args, **kwargs)
        # filtering similar tagged post
        tag = []
        for obj_tag in Tag.objects.all().order_by("name"):
            tag.append(str(obj_tag.name))
        tag = set(tag)  # eleminates dublicates
        tag = list(tag)  # back to list
        tag = sorted(tag)  # sorting
        context["tags"] = tag
        context["featured"] = Post.published.all().order_by("-count")[:5]
        context["users"] = User.objects.all()[:5]
        context["page_obj"] = context["objects"]

        return context


class UserDetailListPostView(DetailView):
    model = Post
    template_name = "posts/user_list.html"
    context_object_name = "objects"
    pk_url_kwarg = "author_id"
    slug_url_kwarg = "author"

    def get_queryset(self, *args, **kwargs):
        queryset = super(UserDetailListPostView, self).get_queryset(*args, **kwargs)

        query = self.request.GET.get("q")
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(body__icontains=query)
                | Q(author__username=query)
                | Q(status=query)
            ).distinct()
            queryset = queryset.order_by("-created")

        if not self.request.user.is_authenticated:
            queryset = queryset.filter(status="published")
            queryset = queryset.order_by("-created").distinct()
            print(queryset)

        return queryset

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        pk = self.kwargs.get(self.pk_url_kwarg)  # author_id
        slug = self.kwargs.get(self.slug_url_kwarg)  # author_username
        if pk is not None and slug is not None:
            queryset = queryset.filter(author__id=pk).filter(author__username=slug)
            print(queryset, "bibek")

        try:

            page = self.request.GET.get("page", 1)
            paginator = Paginator(queryset, 4)
            try:
                queryset = paginator.page(page)
            except PageNotAnInteger:
                queryset = paginator.page(1)
            except EmptyPage:
                queryset = paginator.page(paginator.num_pages)
            obj = queryset
        except queryset.model.DoesNotExist:
            raise Http404(
                _("No %(verbose_name)s found matching the query")
                % {"verbose_name": queryset.model._meta.verbose_name}
            )
        return obj

    def get_context_data(self, *args, **kwargs):
        context = super(UserDetailListPostView, self).get_context_data(*args, **kwargs)
        pk = self.kwargs.get(self.pk_url_kwarg)
        user = get_object_or_404(User, pk=pk)
        context["user"] = user
        print(self.queryset)
        context["page_obj"] = self.get_object()
        user_posts_count = user.blog_posts.all()
        if self.request.user.username == user.username:
            context["counts"] = user_posts_count.count()
        else:
            context["counts"] = user_posts_count.filter(status="published").count()
        return context


class CreateCommentView(SuccessMessageMixin, CreateView):
    template_name = "posts/details.html"
    form_class = CommentCreateForm
    success_message = "Post was created SuccessFully"

    def form_valid(self, form):
        form.save(commit=False)
        slug = self.kwargs.get(self.slug_url_kwarg)
        form.instance.user = self.request.user
        form.save()
        return super(CreateCommentView, self).form_valid(form)


class DetailPostView(DetailView, SuccessMessageMixin, CreateView):
    model = Post
    # form_class = PostCreateForm
    context_object_name = "objects"
    slug_url_kwarg = "slug"
    pk_url_kwarg = "author_id"
    author_url_kwarg = "author"
    template_name = "posts/detail.html"
    form_class = CommentCreateForm
    success_message = "Commented SuccessFully"

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        pk = self.kwargs.get(self.pk_url_kwarg)  # author_id
        slug = self.kwargs.get(self.slug_url_kwarg)
        author = self.kwargs.get(self.author_url_kwarg)  # author_username
        if pk is not None and slug is not None and author is not None:
            queryset = (
                queryset.filter(author__id=pk)
                .filter(author__username=author)
                .filter(slug=slug)
            )
            print(queryset, "bibek")

        if pk is None and slug is None and author is None:
            raise AttributeError(
                "Generic detail view %s must be called with either an object "
                "pk or a slug in the URLconf." % self.__class__.__name__
            )

        try:
            obj = queryset.get()
            obj.count = obj.count + 1
            obj.save()
        except queryset.model.DoesNotExist:
            raise Http404(
                _("No %(verbose_name)s found matching the query")
                % {"verbose_name": queryset.model._meta.verbose_name}
            )
        return obj

    def form_valid(self, form):
        form.save(commit=False)
        slug = self.kwargs.get(self.slug_url_kwarg)
        if self.request.user.is_authenticated:
            form.instance.user = self.request.user
        form.instance.post = Post.objects.filter(slug=slug).first()
        form.save()
        return super(DetailPostView, self).form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super(DetailPostView, self).get_context_data(*args, **kwargs)
        slug = self.kwargs.get(self.slug_url_kwarg)
        comments = (
            Comment.objects.filter(post=Post.objects.filter(slug=slug).first())
            .order_by("created_at")
            .distinct()
        )
        context["comments"] = comments
        return context


@method_decorator(login_required(login_url="/accounts/login/"), name="dispatch")
class CreatePostView(SuccessMessageMixin, CreateView):
    template_name = "posts/create.html"
    form_class = PostCreateForm
    success_message = "Post was created SuccessFully"

    def form_valid(self, form):
        form.save(commit=False)
        form.instance.author = self.request.user
        form.save()
        form.save_m2m()
        return super(CreatePostView, self).form_valid(form)


@method_decorator(login_required(login_url="/accounts/login/"), name="dispatch")
class UpdatePostView(SuccessMessageMixin, UpdateView):
    model = Post
    form_class = PostForm
    slug_url_kwarg = "slug"
    pk_url_kwarg = "author_id"
    author_url_kwarg = "author"
    template_name = "posts/update.html"
    success_message = "Post was Updated successfully"

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        pk = self.kwargs.get(self.pk_url_kwarg)  # author_id
        slug = self.kwargs.get(self.slug_url_kwarg)
        author = self.kwargs.get(self.author_url_kwarg)  # author_username
        if pk is not None and slug is not None and author is not None:
            queryset = (
                queryset.filter(author__id=pk)
                .filter(author__username=author)
                .filter(slug=slug)
            )
            print(queryset, "bibek")

        if pk is None and slug is None and author is None:
            raise AttributeError(
                "Generic detail view %s must be called with either an object "
                "pk or a slug in the URLconf." % self.__class__.__name__
            )

        try:
            obj = queryset.get()
        except queryset.model.DoesNotExist:
            raise Http404(
                ("No %(verbose_name)s found matching the query")
                % {"verbose_name": queryset.model._meta.verbose_name}
            )
        return obj

    def form_valid(self, form):
        form.save(commit=False)
        form.instance.author = self.request.user
        form.save()
        form.save_m2m()
        return super(UpdatePostView, self).form_valid(form)


@method_decorator(login_required(login_url="/accounts/login/"), name="dispatch")
class DeletePostView(View):
    def get(self, request, author_id, slug):
        obj = get_object_or_404(Post, author__id=author_id, slug=slug)
        obj.delete()
        messages.success(request, "Post Successfully Deleted")
        return redirect(
            "posts:user_post_list", request.user.username, request.user.id
        )
