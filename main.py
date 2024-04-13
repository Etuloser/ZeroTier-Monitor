import json
import os
import smtplib

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

import requests

from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent

load_dotenv()

zerotier_authtoken = os.getenv("zerotier_authtoken")
api_server = os.getenv("api_server")


def get_peers():
    url = f"{api_server}/peer"
    response = requests.get(url, headers={"X-ZT1-Auth": zerotier_authtoken})
    return [obj["address"] for obj in response.json()]


def get_nwid():
    url = f"{api_server}/controller/network"
    response = requests.get(url, headers={"X-ZT1-Auth": zerotier_authtoken})
    nwid = response.json()[0]
    return nwid


def get_network_members() -> list[str]:
    nwid = get_nwid()
    url = f"{api_server}/controller/network/{nwid}/member"
    response = requests.get(url, headers={"X-ZT1-Auth": zerotier_authtoken})
    return [obj for obj in response.json().keys()]


def send_mail(member):
    # 设置发件人和收件人
    sender_email = os.getenv("sender_email")
    receiver_email = os.getenv("receiver_email")

    # 创建邮件内容
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = "ZeroTier节点监控"
    member_name_hashtable = {
        "0f67f4384f": "Windows11",
        "30fb3b4fca": "Ubuntu22.04",
        "eda3c8f74f": "yoga14s",
    }
    body = f"{member_name_hashtable[member]} 节点离线"
    message.attach(MIMEText(body, "plain"))

    # 连接到 SMTP 服务器
    server = smtplib.SMTP("smtp.qq.com", 587)
    server.starttls()
    server.login(sender_email, os.getenv("qq_smtp_auth_code"))  # type: ignore

    # 发送邮件
    server.sendmail(sender_email, receiver_email, message.as_string())  # type: ignore
    print("Email sent successfully!")

    # 关闭连接
    server.quit()


def check_members_is_alive():
    members = get_network_members()
    peers = get_peers()
    members_json_path = os.path.join(BASE_DIR, "members.json")
    has_init = os.path.exists(members_json_path)
    if has_init:
        with open(members_json_path, "r") as f:
            members_obj = json.load(f)
            for peer in members_obj.keys():
                if peer in peers:
                    members_obj[peer] = "ONLINE"
                else:
                    if members_obj[peer] == "OFFLINE":
                        pass
                    else:
                        members_obj[peer] = "OFFLINE"
                        send_mail(peer)
        with open(members_json_path, "w") as f:
            f.writelines(json.dumps(members_obj, indent=4))
    else:
        members_obj = {}
        for member in members:
            members_obj[member] = "ONLINE"
        lines = json.dumps(members_obj, indent=4)
        with open(members_json_path, "w") as f:
            f.writelines(lines)
        check_members_is_alive()


check_members_is_alive()
