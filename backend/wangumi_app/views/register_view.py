import json

from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from wangumi_app.models import UserProfile
from wangumi_app.services import (
    RateLimitError,
    SmsSendError,
    send_email_code,
    verify_email_code,
)
from wangumi_app.views.utils import get_client_ip
"""
用户注册接口
"""
@csrf_exempt
def register(request):
    if request.method != "POST":
        return JsonResponse({'error': '仅支持POST请求'}, status=405,json_dumps_params={'ensure_ascii': False})
    
    try:
        data = json.loads(request.body.decode('utf-8'))
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        code = data.get('code')

        """输入正确性检测"""
        if not username or not password:
            return JsonResponse({'error': '用户名和密码不能为空'}, status=400,json_dumps_params={'ensure_ascii': False})
        if not email:
            return JsonResponse({'error': '邮箱不能为空'}, status=400,json_dumps_params={'ensure_ascii': False})
        if len(password) < 6:
            return JsonResponse({'error': '密码长度至少6位'}, status=400,json_dumps_params={'ensure_ascii': False})
        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': '用户名已存在'}, status=400,json_dumps_params={'ensure_ascii': False})
        if email and User.objects.filter(email=email).exists():
            return JsonResponse({'error': '邮箱已被注册'}, status=400,json_dumps_params={'ensure_ascii': False})

        # 校验验证码
        if not code :
            return JsonResponse({'error': '验证码不能为空'}, status=400, json_dumps_params={'ensure_ascii': False})
        try:
            is_valid = verify_email_code(email, "register", code, consume=True)
        except ValueError as exc:
            return JsonResponse({'error': str(exc)}, status=400, json_dumps_params={'ensure_ascii': False})
        if not is_valid:
            return JsonResponse({'error': '验证码无效或已过期'}, status=400, json_dumps_params={'ensure_ascii': False})


        user = User.objects.create_user(username=username, password=password, email=email)
        UserProfile.objects.create(user=user)
        return JsonResponse({
            "code": 200,
            "message": "注册成功",
            "data": {
                "username": username,
                "email": email,
            }
        }, status=200,json_dumps_params={'ensure_ascii': False})

    except json.JSONDecodeError:
        return JsonResponse({'error': '请求数据格式错误'}, status=400,json_dumps_params={'ensure_ascii': False})
    except Exception as e:
        return JsonResponse({'error': f"服务器内部错误: {str(e)}"}, status=500,json_dumps_params={'ensure_ascii': False})



@csrf_exempt
def send_verification_code(request):
    """
    发送验证码到手机号或邮箱的接口
    """
    if request.method != "POST":
        return JsonResponse({'error': '仅支持POST请求'}, status=405, json_dumps_params={'ensure_ascii': False})

    try:
        data = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'error': '请求数据格式错误'}, status=400, json_dumps_params={'ensure_ascii': False})
    email = data.get('email')
    purpose = data.get('purpose', 'register')

    if not email:
        return JsonResponse({'error': '邮箱不能为空'}, status=400, json_dumps_params={'ensure_ascii': False})

    client_ip = get_client_ip(request)
    try:
        result = send_email_code(email, purpose, requester_ip=client_ip)
    except ValueError as exc:
        return JsonResponse({'error': str(exc)}, status=400, json_dumps_params={'ensure_ascii': False})
    except RateLimitError as exc:
        return JsonResponse({'error': str(exc)}, status=429, json_dumps_params={'ensure_ascii': False})
    except SmsSendError as exc:
        return JsonResponse({'error': str(exc)}, status=502, json_dumps_params={'ensure_ascii': False})

    payload = {'message': '验证码已发送', 'data': {'purpose': purpose}}
    if result.request_id:
        payload['data']['request_id'] = result.request_id
    return JsonResponse(payload, json_dumps_params={'ensure_ascii': False})


@csrf_exempt
def verify_code(request):
    if request.method != "POST":
        return JsonResponse({'error': '仅支持POST请求'}, status=405, json_dumps_params={'ensure_ascii': False})
    try:
        data = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'error': '请求数据格式错误'}, status=400,json_dumps_params={'ensure_ascii': False})

    email = data.get('email')
    code = data.get('code')
    purpose = data.get('purpose', 'register')
    consume = data.get('consume', True)

    if not code:
        return JsonResponse({'error': '验证码不能为空'}, status=400, json_dumps_params={'ensure_ascii': False})
    try:
        is_valid = verify_email_code(email, purpose, code, consume=consume)
    except ValueError as exc:
        return JsonResponse({'error': str(exc)}, status=400, json_dumps_params={'ensure_ascii': False})

    if not is_valid:
        return JsonResponse({'error': '验证码无效或已过期'}, status=400, json_dumps_params={'ensure_ascii': False})
    return JsonResponse({'message': '验证码已验证', 'data': {'purpose': purpose}}, json_dumps_params={'ensure_ascii': False})
