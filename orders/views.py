from django.shortcuts import render

# Create your views here.
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def dashboard(request):
    user = request.user

    context = {
        "user": user,
    }
    return render(request, "orders/dashboard.html", context)