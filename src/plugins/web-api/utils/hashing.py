# 解密信息
import hashlib
import base64
from Crypto.Cipher import AES
import json

from Crypto.Util.Padding import unpad


def check_signature(rawData, session_key:str, signature):
    """
    验证签名
    """
    if not rawData:
        return True
    # 使用相同的算法计算出签名
    hash_string = rawData + str(session_key)
    hash_object = hashlib.sha1(hash_string.encode())
    signature2 = hash_object.hexdigest()
    print('signature2', signature2)
    print('signature', signature)
    # 比对 signature 与 signature2
    return signature == signature2


def decrypt_data(encrypted_data='', session_key='', iv=''):
    """
    解密数据
    """
    try:
        # 对称解密秘钥 passkey = Base64_Decode(session_key)
        passkey = base64.b64decode(session_key)

        # 对称解密算法初始向量 为Base64_Decode(iv)
        iv = base64.b64decode(iv)

        # 对称解密使用的算法为 AES-128-CBC
        cipher = AES.new(passkey, AES.MODE_CBC, iv)

        # 对称解密的目标密文为 Base64_Decode(encryptedData)
        encrypted_data = base64.b64decode(encrypted_data)

        # 解密数据
        decrypted_bytes = unpad(cipher.decrypt(encrypted_data), AES.block_size)

        # 尝试解码为 UTF-8 字符串
        try:
            decrypted_str = decrypted_bytes.decode('utf-8')
        except UnicodeDecodeError as e:
            print(f"解码错误: {e}")
            raise

        decrypted = json.loads(decrypted_str)
        print("+",decrypted)
        return decrypted
    except UnicodeDecodeError as e:
        # 记录解码错误日志
        print(f"解码错误: {e}")
        raise
    except Exception as e:
        # 记录其他错误日志
        print(f"解密错误: {e}")
        raise