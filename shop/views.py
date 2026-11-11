import json
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST

from .lava_client import LavaError, create_invoice_v3, get_invoice, resolve_offer_id
from .models import Profile, TopUpOrder

CITIES = [
    "Москва", "Санкт-Петербург", "Краснодар", "Сочи", "Казань",
    "Екатеринбург", "Новосибирск", "Ростов-на-Дону", "Самара", "Уфа",
]


def _get_profile(request):
    email = request.session.get("email")
    if not email:
        return None
    return Profile.objects.filter(email=email).first()


def _seed_demo_if_empty():
    if Profile.objects.filter(is_public=True).count() >= 8:
        return
    demos = [
        ("Анна", 2, 24, "Москва", "Ищу серьёзные отношения"),
        ("Мария", 2, 27, "Санкт-Петербург", "Люблю путешествия"),
        ("Елена", 2, 31, "Сочи", "Открыта к общению"),
        ("Виктория", 2, 23, "Казань", "Ищу спонсора для проектов"),
        ("Алина", 2, 29, "Краснодар", "Ценит внимание и заботу"),
        ("Дарья", 2, 26, "Москва", "Только серьёзный подход"),
        ("Александр", 1, 34, "Москва", "Готов поддерживать"),
        ("Дмитрий", 1, 38, "Екатеринбург", "Ищу интересную девушку"),
        ("Максим", 1, 32, "Санкт-Петербург", "Деловые и личные знакомства"),
        ("Иван", 1, 41, "Сочи", "Ценит красоту и ум"),
    ]
    for i, (name, gender, age, city, title) in enumerate(demos):
        email = f"demo{i}@example.local"
        if Profile.objects.filter(email=email).exists():
            continue
        Profile.objects.create(
            email=email,
            name=name,
            gender=gender,
            age=age,
            city=city,
            title=title,
            about="Демо-анкета для витрины знакомств.",
            is_public=True,
            online=(i % 3 == 0),
            balance=0,
        )


def home(request):
    _seed_demo_if_empty()
    qs = Profile.objects.filter(is_public=True).order_by("-online", "-created_at")[:24]
    return render(request, "shop/home.html", {
        "ankets": qs,
        "key_ok": bool(settings.LAVA_API_KEY),
    })


def search(request):
    _seed_demo_if_empty()
    gender = request.GET.get("gender", "")
    city = request.GET.get("city", "")
    age_from = request.GET.get("agefrom", "18")
    age_to = request.GET.get("ageto", "60")
    try:
        age_from_i = max(18, int(age_from))
        age_to_i = min(99, int(age_to))
    except ValueError:
        age_from_i, age_to_i = 18, 60

    qs = Profile.objects.filter(is_public=True, age__gte=age_from_i, age__lte=age_to_i)
    if gender in ("1", "2"):
        qs = qs.filter(gender=int(gender))
    if city:
        qs = qs.filter(city__icontains=city)
    qs = qs.order_by("-online", "-created_at")[:50]

    return render(request, "shop/search.html", {
        "ankets": qs,
        "cities": CITIES,
        "filters": {
            "gender": gender,
            "city": city,
            "agefrom": age_from_i,
            "ageto": age_to_i,
        },
    })


def anketa_detail(request, pk):
    a = get_object_or_404(Profile, pk=pk, is_public=True)
    return render(request, "shop/anketa.html", {"a": a})


def register(request):
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        name = (request.POST.get("name") or "").strip()
        password = (request.POST.get("password") or "").strip()
        try:
            age = int(request.POST.get("age") or 25)
        except ValueError:
            age = 25
        gender = int(request.POST.get("gender") or 2)
        city = (request.POST.get("city") or "Москва").strip()
        about = (request.POST.get("about") or "").strip()
        title = (request.POST.get("title") or "Ищу общение").strip()

        if not email or "@" not in email:
            messages.error(request, "Укажите email")
            return redirect("register")
        if Profile.objects.filter(email=email).exists():
            messages.error(request, "Такой email уже зарегистрирован — войдите")
            return redirect("login")
        if age < 18:
            messages.error(request, "Только 18+")
            return redirect("register")

        profile = Profile.objects.create(
            email=email,
            name=name or email.split("@")[0],
            password=password,  # demo store; not production hashing
            gender=gender if gender in (1, 2) else 2,
            age=age,
            city=city,
            about=about,
            title=title,
            is_public=True,
            online=True,
        )
        request.session["email"] = profile.email
        messages.success(request, "Регистрация успешна. Анкета в поиске.")
        return redirect("profile")

    return render(request, "shop/register.html", {"cities": CITIES})


def login_view(request):
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        password = (request.POST.get("password") or "").strip()
        profile = Profile.objects.filter(email=email).first()
        if not profile:
            messages.error(request, "Аккаунт не найден — зарегистрируйтесь")
            return redirect("register")
        if profile.password and password and profile.password != password:
            messages.error(request, "Неверный пароль")
            return redirect("login")
        request.session["email"] = profile.email
        profile.online = True
        profile.save(update_fields=["online"])
        messages.success(request, "С возвращением")
        return redirect("profile")
    return render(request, "shop/login.html")


def logout_view(request):
    email = request.session.get("email")
    if email:
        Profile.objects.filter(email=email).update(online=False)
    request.session.flush()
    messages.info(request, "Вы вышли")
    return redirect("home")


def profile(request):
    profile = _get_profile(request)
    if not profile:
        return redirect("login")
    recent = profile.orders.all().order_by("-created_at")[:8]
    return render(request, "shop/profile.html", {"profile": profile, "orders": recent})


def profile_edit(request):
    profile = _get_profile(request)
    if not profile:
        return redirect("login")
    if request.method == "POST":
        profile.name = (request.POST.get("name") or profile.name).strip()
        try:
            profile.age = max(18, int(request.POST.get("age") or profile.age))
        except ValueError:
            pass
        g = request.POST.get("gender")
        if g in ("1", "2"):
            profile.gender = int(g)
        profile.city = (request.POST.get("city") or profile.city).strip()
        profile.title = (request.POST.get("title") or profile.title).strip()
        profile.about = (request.POST.get("about") or "").strip()
        profile.is_public = request.POST.get("is_public") == "on"
        profile.save()
        messages.success(request, "Анкета сохранена")
        return redirect("profile")
    return render(request, "shop/profile_edit.html", {"profile": profile, "cities": CITIES})


def topup(request):
    profile = _get_profile(request)
    if not profile:
        messages.warning(request, "Войдите, чтобы пополнить баланс")
        return redirect("login")
    return render(request, "shop/topup.html", {
        "profile": profile,
        "currency": settings.LAVA_CURRENCY,
        "preset": [100, 300, 500, 1000, 3000],
    })


@require_POST
def topup_start(request):
    profile = _get_profile(request)
    if not profile:
        return redirect("login")
    raw = (request.POST.get("amount") or "").replace(",", ".").strip()
    try:
        amount = Decimal(raw)
    except (InvalidOperation, TypeError):
        messages.error(request, "Некорректная сумма")
        return redirect("topup")
    if amount < 1:
        messages.error(request, "Минимум 1")
        return redirect("topup")
    if not settings.LAVA_API_KEY:
        messages.error(request, "На сервере не задан LAVA_API_KEY")
        return redirect("topup")

    try:
        offer_id = resolve_offer_id()
        data = create_invoice_v3(
            email=profile.email,
            offer_id=offer_id,
            currency=settings.LAVA_CURRENCY,
            amount=float(amount),
            buyer_language="RU",
        )
    except LavaError as e:
        messages.error(request, f"Lava: {e}")
        return redirect("topup")

    payment_url = data.get("paymentUrl") or data.get("payment_url") or data.get("url") or ""
    invoice_id = str(data.get("id") or data.get("invoiceId") or data.get("contractId") or "")
    TopUpOrder.objects.create(
        profile=profile,
        amount=amount,
        currency=settings.LAVA_CURRENCY,
        offer_id=offer_id,
        invoice_id=invoice_id,
        payment_url=payment_url,
        status="pending" if payment_url else "created",
        raw_response=json.dumps(data, ensure_ascii=False)[:5000],
    )
    if not payment_url:
        messages.error(request, "Нет paymentUrl: " + json.dumps(data)[:300])
        return redirect("orders")
    return redirect(payment_url)


def topup_return(request):
    profile = _get_profile(request)
    invoice_id = (request.GET.get("invoiceId") or request.GET.get("id") or "").strip()
    if profile and invoice_id:
        order = TopUpOrder.objects.filter(profile=profile, invoice_id=invoice_id).first()
        if order:
            _sync_order(order)
    messages.info(request, "Статус оплаты обновлён, если Lava подтвердила платёж")
    return redirect("profile")


def orders(request):
    profile = _get_profile(request)
    if not profile:
        return redirect("login")
    # expire old pending > 24h
    old = timezone.now() - timezone.timedelta(hours=24)
    TopUpOrder.objects.filter(profile=profile, status="pending", created_at__lt=old).update(status="expired")
    items = profile.orders.all().order_by("-created_at")
    for o in items:
        if o.status == "pending" and o.invoice_id:
            try:
                _sync_order(o)
            except Exception:
                pass
    items = profile.orders.all().order_by("-created_at")
    return render(request, "shop/orders.html", {"orders": items, "profile": profile})


def rules(request):
    return render(request, "shop/rules.html")


def _sync_order(order: TopUpOrder):
    if order.status == "paid" or not order.invoice_id:
        return order
    try:
        data = get_invoice(order.invoice_id)
    except LavaError:
        return order
    status = str(data.get("status") or data.get("invoiceStatus") or data.get("contractStatus") or "").lower()
    if any(m in status for m in ("paid", "success", "completed", "done", "settled")) or data.get("paid") is True:
        if order.status != "paid":
            order.status = "paid"
            order.paid_at = timezone.now()
            order.raw_response = json.dumps(data, ensure_ascii=False)[:5000]
            order.save(update_fields=["status", "paid_at", "raw_response"])
            p = order.profile
            p.balance = (p.balance or 0) + order.amount
            p.save(update_fields=["balance"])
    return order


@csrf_exempt
@require_http_methods(["POST"])
def lava_webhook(request):
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False}, status=400)
    invoice_id = str(
        payload.get("invoiceId")
        or payload.get("id")
        or payload.get("contractId")
        or (payload.get("data") or {}).get("id")
        or ""
    )
    event = str(payload.get("eventType") or payload.get("event") or payload.get("type") or "")
    if invoice_id:
        order = TopUpOrder.objects.filter(invoice_id=invoice_id).first()
        if order and order.status != "paid":
            if "success" in event.lower() or "paid" in event.lower() or not event:
                try:
                    _sync_order(order)
                except Exception:
                    order.status = "paid"
                    order.paid_at = timezone.now()
                    order.save(update_fields=["status", "paid_at"])
                    p = order.profile
                    p.balance = (p.balance or 0) + order.amount
                    p.save(update_fields=["balance"])
    return JsonResponse({"ok": True})
