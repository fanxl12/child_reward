"""
微信小程序服务 - 处理微信登录和API调用
"""
import httpx
from typing import Optional
from api.config import settings


class WechatService:
    """微信小程序服务"""
    
    # 微信API端点
    CODE2SESSION_URL = "https://api.weixin.qq.com/sns/jscode2session"
    
    @classmethod
    async def code2session(cls, code: str) -> Optional[dict]:
        """
        使用登录凭证 code 获取 session_key 和 openid
        
        Args:
            code: 微信登录临时凭证
            
        Returns:
            包含 openid, session_key, unionid(可选) 的字典，失败返回 None
        """
        if not settings.WECHAT_APP_ID or not settings.WECHAT_APP_SECRET:
            raise ValueError("微信小程序配置未设置")
        
        params = {
            "appid": settings.WECHAT_APP_ID,
            "secret": settings.WECHAT_APP_SECRET,
            "js_code": code,
            "grant_type": "authorization_code",
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(cls.CODE2SESSION_URL, params=params)
                result = response.json()
                
                # 检查是否返回错误
                if "openid" in result:
                    return {
                        "openid": result["openid"],
                        "session_key": result.get("session_key"),
                        "unionid": result.get("unionid"),
                    }
                else:
                    # 微信API返回错误
                    errcode = result.get("errcode", "unknown")
                    errmsg = result.get("errmsg", "unknown error")
                    print(f"微信登录失败: errcode={errcode}, errmsg={errmsg}")
                    return None
                    
        except Exception as e:
            print(f"调用微信API异常: {str(e)}")
            return None
    
    @classmethod
    def get_phone_number_url(cls, access_token: str) -> str:
        """获取手机号API URL"""
        return f"https://api.weixin.qq.com/wxa/business/getuserphonenumber?access_token={access_token}"
    
    @classmethod
    async def get_access_token(cls) -> Optional[str]:
        """
        获取接口调用凭据
        
        Returns:
            access_token 字符串，失败返回 None
        """
        if not settings.WECHAT_APP_ID or not settings.WECHAT_APP_SECRET:
            raise ValueError("微信小程序配置未设置")
        
        url = "https://api.weixin.qq.com/cgi-bin/token"
        params = {
            "grant_type": "client_credential",
            "appid": settings.WECHAT_APP_ID,
            "secret": settings.WECHAT_APP_SECRET,
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                result = response.json()
                
                if "access_token" in result:
                    return result["access_token"]
                else:
                    errcode = result.get("errcode", "unknown")
                    errmsg = result.get("errmsg", "unknown error")
                    print(f"获取access_token失败: errcode={errcode}, errmsg={errmsg}")
                    return None
                    
        except Exception as e:
            print(f"获取access_token异常: {str(e)}")
            return None


# 全局微信服务实例
wechat_service = WechatService()
