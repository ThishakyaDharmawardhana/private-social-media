from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Post, Category


def feed(request):
    category_filter = request.GET.get('category')
    year_filter = request.GET.get('year')
    view_type = request.GET.get('view', 'feed')  # 'feed' or 'timeline'
    group_by = request.GET.get('group', 'month')  # 'day', 'month', 'year'

    posts = Post.objects.all()

    if category_filter:
        posts = posts.filter(category_id=category_filter)

    if year_filter:
        posts = posts.filter(created_at__year=year_filter)

    posts = posts.order_by('-created_at')

    all_posts = Post.objects.all().order_by('-created_at')
    available_years = sorted({post.created_at.year for post in all_posts}, reverse=True)

    grouped_posts = None
    grouped_feed = None
    if view_type == 'timeline':
        grouped_posts = group_posts_by_date(posts, group_by)
    elif group_by in ('day', 'month'):
        grouped_feed = group_posts_by_date(posts, group_by)

    categories = Category.objects.all()
    context = {
        'posts': posts if view_type == 'feed' else [],
        'grouped_posts': grouped_posts if view_type == 'timeline' else None,
        'categories': categories,
        'selected_category': category_filter,
        'selected_year': year_filter,
        'available_years': available_years,
        'view_type': view_type,
        'group_by': group_by,
        'grouped_feed': grouped_feed,
    }
    return render(request, 'feed.html', context)


def group_posts_by_date(posts, group_by='month'):
    """Group posts by day, month, or year."""
    from collections import defaultdict

    grouped = defaultdict(list)
    for post in posts:
        if group_by == 'day':
            key = post.created_at.strftime('%A, %B %d, %Y')
        elif group_by == 'year':
            key = post.created_at.strftime('%Y')
        else:
            key = post.created_at.strftime('%B %Y')

        grouped[key].append(post)

    # Sort groups by newest first based on first item's created_at
    sorted_groups = sorted(grouped.items(), key=lambda item: item[1][0].created_at, reverse=True)
    return sorted_groups


@login_required(login_url='login')
def add_category(request):
    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()
        icon = (request.POST.get('icon') or '').strip()

        if name:
            category, created = Category.objects.get_or_create(name=name, defaults={'icon': icon})
            if not created:
                category.icon = icon
                category.save()
            messages.success(request, 'Category saved!')
        else:
            messages.error(request, 'Name is required to create a category.')
    return redirect('feed')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('feed')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('feed')
        messages.error(request, 'Invalid credentials')

    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def add_post(request):
    if request.method == 'POST':
        caption = request.POST.get('caption')
        image = request.FILES.get('image')
        video = request.FILES.get('video')
        category_id = request.POST.get('category')

        # enforce single media: prefer video if both provided
        if image and video:
            image = None

        category = None
        if category_id:
            category = Category.objects.filter(id=category_id).first()

        Post.objects.create(caption=caption, image=image, video=video, category=category)
        return redirect('feed')

    categories = Category.objects.all()
    return render(request, 'add_post.html', {'categories': categories})


@login_required(login_url='login')
def edit_post(request, pk):
    post = get_object_or_404(Post, pk=pk)

    if request.method == 'POST':
        caption = request.POST.get('caption')
        image = request.FILES.get('image')
        video = request.FILES.get('video')
        category_id = request.POST.get('category')

        if image and video:
            image = None

        post.caption = caption

        if category_id:
            post.category = Category.objects.filter(id=category_id).first()
        else:
            post.category = None

        if image:
            post.image = image
            post.video = None
        elif video:
            post.video = video
            post.image = None

        post.save()
        return redirect('feed')

    categories = Category.objects.all()
    return render(request, 'edit_post.html', {'post': post, 'categories': categories})


@login_required(login_url='login')
def delete_post(request, pk):
    post = get_object_or_404(Post, pk=pk)

    if request.method == 'POST':
        # delete associated files
        if post.image:
            post.image.delete(save=False)
        if post.video:
            post.video.delete(save=False)
        post.delete()
        return redirect('feed')

    return redirect('feed')


@login_required(login_url='login')
def toggle_like(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.user in post.likes.all():
        post.likes.remove(request.user)
    else:
        post.likes.add(request.user)
    return redirect('feed')


@login_required(login_url='login')
def toggle_favorite(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.user in post.favorites.all():
        post.favorites.remove(request.user)
    else:
        post.favorites.add(request.user)
    return redirect('feed')