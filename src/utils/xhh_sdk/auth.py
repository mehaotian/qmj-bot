import hashlib
import time
import random



class XhhAuth():
    """
    小黑盒参数鉴权
    """
    # 代理ip设置
    proxies = {}
    # 字符集
    char_set = ['a', 'b', 'e', 'g', 'h', 'i', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'w']
    # 小黑盒地址

    def byte_shift(self,e):
        """左移和按位与操作，主要用于加密计算"""
        return 255 & (e << 1 ^ 27) if 128 & e else e << 1


    def byte_xor(self,e):
        """单字节异或操作"""
        return self.byte_shift(e) ^ e


    def byte_expand(self,e):
        """
        扩展异或
        @param e:
        @return:
        """
        return self.byte_xor(self.byte_shift(e))


    def byte_expand_more(self,e):
        """
        进一步的异或运算
        @param e:
        @return:
        """
        return self.byte_expand(self.byte_xor(self.byte_shift(e)))


    def final_byte_transform(self,e):
        """
        最终字节转换，用于加密
        @param e:
        @return:
        """
        return self.byte_expand_more(e) ^ self.byte_expand(e) ^ self.byte_xor(e)


    def convert_to_int(self,input_string):
        """
        将输入字符串转换成整数，用于生成验证码等加密操作
        @param input_string:
        @return:
        """
        byte_list = [ord(c) for c in input_string[-4:]]
        transformed = [0, 0, 0, 0]
        transformed[0] = self.final_byte_transform(byte_list[0]) ^ self.byte_expand_more(byte_list[1]) ^ self.byte_expand(
            byte_list[2]) ^ self.byte_xor(byte_list[3])
        transformed[1] = self.byte_xor(byte_list[0]) ^ self.final_byte_transform(byte_list[1]) ^ self.byte_expand_more(
            byte_list[2]) ^ self.byte_expand(byte_list[3])
        transformed[2] = self.byte_expand(byte_list[0]) ^ self.byte_xor(byte_list[1]) ^ self.final_byte_transform(
            byte_list[2]) ^ self.byte_expand_more(byte_list[3])
        transformed[3] = self.byte_expand_more(byte_list[0]) ^ self.byte_expand(byte_list[1]) ^ self.byte_xor(
            byte_list[2]) ^ self.final_byte_transform(byte_list[3])
        return sum(transformed)

    def generate_code(self,endpoint, timestamp, nonce):
        """
        生成加密字符串，类似于验证码生成
        @param endpoint:
        @param timestamp:
        @param nonce:
        @return:
        """
        # 规范化URL路径
        normalized_endpoint = "/" + "/".join(filter(lambda x: x, endpoint.split("/"))) + "/"

        # 字符集
        char_pool = "JKMNPQRTX1234OABCDFG56789H"

        # 处理nonce和字符集进行哈希运算
        hash_nonce = self.generate_md5("".join(filter(lambda e: e.isdigit(), nonce + char_pool)))
        hashed_string = self.generate_md5(str(timestamp) + normalized_endpoint + hash_nonce)

        # 提取数字并拼接为9位
        digits_only = "".join(filter(lambda e: e.isdigit(), hashed_string))[:9]
        extended_digits = digits_only.ljust(9, "0")

        numeric_value = int(extended_digits)
        code = ""

        # 使用数字生成字符组合
        for _ in range(5):
            index = numeric_value % len(char_pool)
            numeric_value //= len(char_pool)
            code += char_pool[index]

        # 计算校验码（百分制两位数字）
        check_sum = str(self.convert_to_int(code) % 100).zfill(2)
        return code + check_sum

    def generate_md5(slef,input_string):
        """
        生成MD5哈希值
        @return: md5
        """
        md5 = hashlib.md5()
        md5.update(input_string.encode())
        return md5.hexdigest()

    def generate_hkey(self,endpoint, timestamp, nonce):
        """
        根据加密算法生成hkey
        @param endpoint:
        @param timestamp:
        @param nonce:
        @return:
        """
        return self.generate_code(endpoint, timestamp + 1, nonce)
    @classmethod
    def create_sign(cls, endpoint):
        """
        生成请求签名和随机数
        @return:
        """
        interface = cls()
        result = {}
        current_time = int(time.time())
        random_seed = str(current_time) + str(random.random())[:18]

        nonce = interface.generate_md5(random_seed).upper()
        result['hkey'] = interface.generate_hkey(endpoint, current_time, nonce)
        result["_time"] = current_time
        result["nonce"] = nonce
        return result

