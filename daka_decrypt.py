import json
import random
from Crypto.Cipher import AES
import base64


class AESCipher:
    def __init__(self, key):
        self.key = key

    # 获取16位随机字符串
    def generate_random_string(self):
        characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_"
        random_string = ""
        for _ in range(16):
            random_index = random.randint(0, len(characters) - 1)
            random_string += characters[random_index]
        return random_string

    # 补全16位
    def o(self, t):
        t = list(t)
        if len(t) >= 16:
            t = t[:16]
        else:
            for e in range(len(t)):
                if not t[e]:
                    t[e] = "0"
        return "".join(t)

    # 补全16位
    def pad(self, s):
        return s + (16 - len(s) % 16) * chr(0)

    # 去掉补全的字符
    def unpad(self, s):
        return s.rstrip(chr(0))

    # 加密
    def encrypt(self, data):
        data = self.pad(json.dumps(data, separators=(',', ':'))).encode("utf-8")
        key = self.o(self.key)
        key_bytes = key.encode("utf-8")
        random_str = self.generate_random_string()
        random_str_bytes = random_str.encode("utf-8")
        cipher = AES.new(key_bytes, AES.MODE_CBC, random_str_bytes)
        encrypted_data = cipher.encrypt(data)
        encrypted_data = base64.b64encode(encrypted_data).decode("utf-8")
        return encrypted_data, random_str

    # 解密
    def decrypt(self, data, random_str):
        key = self.o(self.key)
        key_bytes = key.encode("utf-8")
        random_str_bytes = random_str.encode("utf-8")
        cipher = AES.new(key_bytes, AES.MODE_CBC, random_str_bytes)
        decrypted_data = base64.b64decode(data)
        decrypted_data = cipher.decrypt(decrypted_data)
        return json.loads(self.unpad(decrypted_data.decode("utf-8")))


if __name__ == '__main__':
    aes_cipher = AESCipher("/catch/core/syllabus/freeSignAjax")
    #data2 = {
        # "aid": "",
        # "pid": "",
        # "token": "90322b75e581f3658e06e0453b606c49"
    #}
    # encrypt, random = aes_cipher.encrypt(data2)

    encrypt = "bgFgUf3uVoCCJTe8rfgqxmgfCH9F8W5uoiEoqTy6XE7e6CQ5j/RmvXr9UKqcwf4jyGY0Gx09LZIdn2eW4nwitDQuwml6HdIKVib3YbQf6tdPakhDBdq8ifJvjVNkSx7ugmvtZhZHQuzsQyMrqNTzPsyY/VRRvvKpQfamAanXjJr4L85ouG/0tbmSBB80GPMeqOEOwHoG4KylKyHOy7pjC2YbI0NF3wY3fA5RgCfVSUB7x737ef95VEsmyDlg7pWs"
    random = "9FxIeR4y5kohSkJ6"
    data2 = aes_cipher.decrypt(encrypt, random)
    print(encrypt, random)
    print(data2)
