# -*- coding=utf-8
import time
import hmac
import hashlib
import urllib.parse
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
import sys
import os
import json
from sts.sts import Sts, CIScope, Scope
from nonebot import get_driver
config = get_driver().config
secret_id = config.secretid
secret_key = config.secretkey
bucket = config.bucket
imgurl = config.imgurl

region = 'ap-beijing'
# 替换为用户的 region，已创建桶归属的 region 可以在控制台查看，https://console.cloud.tencent.com/cos5/bucket
scheme = 'https'  # 指定使用 http/https 协议来访问 COS，默认为 https，可不填

class TcbCosAuth:
    # 生成签名的 KeyTime
    @classmethod
    def generate_key_time(cls, valid_duration_seconds=3600):
        """
        生成签名的 KeyTime
        @param valid_duration_seconds: 签名有效期，单位为秒，默认为 3600 秒
        """
        # 获取当前时间的 Unix 时间戳
        current_time = int(time.time())

        # 计算签名过期时间的 Unix 时间戳
        expiration_time = current_time + valid_duration_seconds

        # 拼接 KeyTime
        key_time = f"{current_time};{expiration_time}"

        return key_time

    # 生成签名的 sign_key
    @classmethod
    def generate_sign_key(cls, key_time):
        """
        生成签名的 sign_key
        @param key_time: 签名的 KeyTime
        @param secret_key: 密钥
        """
        # 计算签名摘要
        sign_key = hmac.new(secret_key.encode("utf-8"),
                            key_time.encode("utf-8"), hashlib.sha1).hexdigest()

        return sign_key

    # 生成 UrlParamList 和 HttpParameters
    @classmethod
    def generate_url_param_list_and_http_parameters(cls, query_string):
        # 解析请求参数
        params = urllib.parse.parse_qs(query_string)

        # 将参数名称进行 UrlEncode 编码和排序
        sorted_param_names = sorted(params.keys())

        # 初始化 UrlParamList 和 HttpParameters
        url_param_list = ";".join(sorted_param_names)
        http_parameters = "&".join(
            [f"{name}={urllib.parse.quote_plus(params[name][0])}" for name in sorted_param_names]
        )

        return url_param_list, http_parameters

    # 生成 HeaderList 和 HttpHeaders
    @classmethod
    def generate_header_list_and_http_headers(cls, headers={}):
        # 遍历 HTTP 请求头部，将 key 和 value 进行 UrlEncode 编码，并将 key 转换为小写
        encoded_headers = {
            urllib.parse.quote_plus(name.lower()): urllib.parse.quote_plus(value)
            for name, value in headers.items()
        }

        # 将编码后的头部按字典序排序
        sorted_headers = sorted(encoded_headers.items())

        # 初始化 HeaderList 和 HttpHeaders
        header_list = ";".join([name for name, _ in sorted_headers])
        http_headers = "&".join(
            [f"{name}={value}" for name, value in sorted_headers])

        return header_list, http_headers

    # 生成 HttpString
    @classmethod
    def generate_http_string(cls, http_method, uri_pathname, http_parameters, http_headers):
        # 将 HttpMethod 转换为小写
        http_method = http_method.lower()

        # 生成 HttpString，按照指定格式拼接各个部分
        http_string = f"{http_method}\n{uri_pathname}\n{http_parameters}\n{http_headers}\n"

        return http_string

    # 生成 StringToSign
    @classmethod
    def generate_string_to_sign(cls, key_time, http_string):
        # 计算 SHA1 摘要
        sha1_digest = hashlib.sha1(http_string.encode('utf-8')).hexdigest()

        # 生成 StringToSign，按照指定格式拼接各个部分
        string_to_sign = f"sha1\n{key_time}\n{sha1_digest}\n"

        return string_to_sign

    # 生成 signature
    @classmethod
    def generate_signature(cls, sign_key, string_to_sign):
        return hmac.new(sign_key.encode('utf-8'), string_to_sign.encode('utf-8'), hashlib.sha1).hexdigest()

    # 生成签名
    @classmethod
    def generate_auth(cls, key_time, header_list, url_param_list, signature):
        # 构建签名字符串
        signature_string = (
            f"q-sign-algorithm=sha1"
            f"&q-ak={secret_id}"
            f"&q-sign-time={key_time}"
            f"&q-key-time={key_time}"
            f"&q-header-list={header_list}"
            f"&q-url-param-list={url_param_list}"
            f"&q-signature={signature}"
        )

        return signature_string


def get_temp_key():
    auth_generator = TcbCosAuth()
    key_time = auth_generator.generate_key_time()
    sign_key = auth_generator.generate_sign_key(key_time)
    url_param_list, http_parameters = auth_generator.generate_url_param_list_and_http_parameters('')
    header_list, http_headers = auth_generator.generate_header_list_and_http_headers({
    })
    http_string = auth_generator.generate_http_string('GET', '/', http_parameters, http_headers)
    string_to_sign = auth_generator.generate_string_to_sign(key_time, http_string)
    signature = auth_generator.generate_signature(sign_key, string_to_sign)
    token = auth_generator.generate_auth(key_time, header_list, url_param_list, signature)

    return token



def sts_token():
    """
    获取临时密钥
    """

    scopes = list()
    scopes.append(CIScope('name/ci:*', bucket, region, '*'))
    scopes.append(Scope('name/cos:*', bucket, region, '*'))
    config = {
        'sts_scheme': 'https',
        'sts_url': 'sts.tencentcloudapi.com/',
        # 临时密钥有效时长，单位是秒
        'duration_seconds': 1800,
        'secret_id': secret_id,
        # 固定密钥
        'secret_key': secret_key,
        # 换成 bucket 所在地区
        'region': region,
        'policy': Sts.get_policy(scopes)
    }

    sts = Sts(config)
    try:
        response = sts.get_credential()
        print(response)
        return response['credentials']['sessionToken']
    except Exception as e:
        print(e)
        return None



def Cos():
    # token = sts_token()
    token = None
    config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key, Token=token, Scheme=scheme)
    print('region',region)
    print('secret_id',secret_id)
    print('secret_key',secret_key)
    print('token',token)

    return CosS3Client(config)

