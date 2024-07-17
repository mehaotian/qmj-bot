# 解密信息
import hashlib
import base64
from Crypto.Cipher import AES
import json


def check_signature(rawData, session_key, signature):
    """
    验证签名
    """
    if not rawData:
        return True
    # 使用相同的算法计算出签名
    hash_string = rawData + session_key
    hash_object = hashlib.sha1(hash_string.encode())
    signature2 = hash_object.hexdigest()
    print('signature2', signature2)
    print('signature', signature)
    # 比对 signature 与 signature2
    return signature == signature2


def decrypt_data(encrypted_data, session_key, iv):
    """
    解密数据
    """
    # 对称解密秘钥 passkey = Base64_Decode(session_key)
    passkey = base64.b64decode(session_key)

    # 对称解密算法初始向量 为Base64_Decode(iv)
    iv = base64.b64decode(iv)

    # 对称解密使用的算法为 AES-128-CBC
    cipher = AES.new(passkey, AES.MODE_CBC, iv)

    # 对称解密的目标密文为 Base64_Decode(encryptedData)
    encrypted_data = base64.b64decode(encrypted_data)

    # 解密数据
    decrypted = json.loads(cipher.decrypt(encrypted_data).decode())

    return decrypted
