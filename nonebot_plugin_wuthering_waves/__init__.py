import httpx
from nonebot import on_command
from requests.exceptions import RequestException
from nonebot.adapters.onebot.v11 import Bot, Message, MessageEvent, MessageSegment

from .models import UserInfo, ResponseData

login_command = on_command("waves", aliases={"鸣潮", "mc"}, priority=5)

user_data = {}
global_token = ""
global_user_id = ""


@login_command.handle()
async def handle_login(bot: Bot, event: MessageEvent):
    await login_command.send("欢迎使用鸣潮bot！！！\n输入登录即可使用")


@login_command.got("登录")
async def get_login(bot: Bot, event: MessageEvent):
    await login_command.send("请输入手机号")


# 获取手机号
@login_command.got("手机号")
async def get_mobile(bot: Bot, event: MessageEvent):
    mobile = str(event.message).strip()
    if not mobile.isdigit() or len(mobile) != 11:
        await login_command.reject("手机号格式不正确，请重新输入")
    user_data[event.user_id] = {"mobile": mobile}
    await login_command.send("请输入您收到的验证码")


# 获取验证码
@login_command.got("验证码")
async def get_verification_code(bot: Bot, event: MessageEvent):
    code = str(event.message).strip()
    if not code.isdigit() or len(code) != 6:
        await login_command.reject("验证码格式不正确，请重新输入")
    if event.user_id not in user_data or "mobile" not in user_data[event.user_id]:
        await login_command.finish("请先输入手机号")
    mobile = user_data[event.user_id]["mobile"]
    token_response = await get_token(mobile, code)
    await login_command.send(Message(token_response))
    await login_command.send("登录成功")
    await login_command.send("请输入:\n个人信息 \n获取游戏 \n签到")
    global global_token, global_user_id
    global_token = token_response.split("Token: ")[1]
    global_user_id = token_response.split("用户ID: ")[1].split("\n")[0]


@login_command.got("个人信息")
async def show_user_info(bot: Bot, event: MessageEvent):
    user_info_response = await get_user_msg()
    await login_command.send(user_info_response)


# TODO 实现
# @login_command.got("获取绑定游戏")
# @login_command.got("签到")
# @login_command.got("")


async def get_token(mobile: str, verification_code: str) -> str:
    LOGIN_API_URL = 'https://api.kurobbs.com/user/sdkLogin'
    dev_code = ''.join([chr(65 + i % 26) if i < 26 else str(i % 10) for i in range(40)])
    data = {
        'mobile': mobile,
        'code': verification_code,
        'devCode': dev_code
    }
    headers = {
        "source": "android",
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(LOGIN_API_URL, data=data, headers=headers)
            response_json = response.json()
            await login_command.send(response_json)
            print(response_json)
            response_data: ResponseData = ResponseData.model_validate(response_json)
            if response_data.code == 200:
                user_info: UserInfo = response_data.data
                return (f"登录成功！\n"
                        f"用户名: {user_info.userName}\n"
                        f"用户ID: {user_info.userId}\n"
                        f"签名: {user_info.signature}\n"
                        f"头像: {MessageSegment.image(user_info.headUrl)}\n"
                        f"Token: {user_info.token}")
            else:
                return f"登录失败：{response_data.msg}"
    except RequestException:
        return '登录失败，疑似网络问题，请检查日志'


async def get_user_msg() -> str:
    USER_INFO_API_URL = 'https://api.kurobbs.com/user/mineV2'
    headers = {
        "osversion": "Android",
        "devcode": "2fba3859fe9bfe9099f2696b8648c2c6",
        "source": "android",
        "token": global_token,
    }
    data = {
        'otherUserId': global_user_id
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(USER_INFO_API_URL, headers=headers, data=data)
            response.raise_for_status()
            response_data = response.json()
            if response_data['code'] == 200:
                user_info = response_data['data']
                return (f"用户信息获取成功！\n"
                        f"用户名: {user_info['userName']}\n"
                        f"性别: {user_info['gender']}\n"
                        f"签名: {user_info['signature']}\n"
                        f"头像: {MessageSegment.image(user_info['headUrl'])}\n"
                        f"注册状态: {'已注册' if user_info['isRegister'] else '未注册'}\n"
                        f"评论数: {user_info['commentCount']}\n"
                        f"粉丝数: {user_info['fansCount']}\n"
                        f"新增粉丝数: {user_info['fansNewCount']}\n"
                        f"关注数: {user_info['followCount']}\n"
                        f"Token: {user_info['token']}")
            else:
                return f"获取用户信息失败：{response_data['msg']}"
    except RequestException:
        return '获取用户信息失败，疑似网络问题，请检查日志'
