#!/usr/bin/env python3
"""
HusanAI 签到脚本
用于向 https://husanai.com/api/user/checkin 发送签到请求
"""

import httpx
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


def load_accounts():
    """从环境变量加载账号配置"""
    accounts_str = os.getenv('USER_ACCOUNTS')
    if not accounts_str:
        print('错误：未找到 USER_ACCOUNTS 环境变量')
        return None

    try:
        accounts_data = json.loads(accounts_str)
        if not isinstance(accounts_data, list):
            print('错误：账号配置必须使用数组格式 [{}]')
            return None

        for i, account in enumerate(accounts_data):
            if not isinstance(account, dict):
                print(f'错误：账号 {i + 1} 配置格式不正确')
                return None
            if 'cookies' not in account or 'api_user' not in account:
                print(f'错误：账号 {i + 1} 缺少必需字段 (cookies, api_user)')
                return None

        return accounts_data
    except Exception as e:
        print(f'错误：账号配置格式不正确：{e}')
        return None


def parse_cookies(cookies_data):
    """解析cookies数据，支持字符串和字典格式"""
    if isinstance(cookies_data, dict):
        return cookies_data

    if isinstance(cookies_data, str):
        cookies_dict = {}
        for cookie in cookies_data.split(';'):
            if '=' in cookie:
                key, value = cookie.strip().split('=', 1)
                cookies_dict[key] = value
        return cookies_dict
    
    return {}


def make_checkin_request_for_account(account_info, account_index):
    """为单个账号执行签到请求"""
    account_name = f'账号 {account_index + 1}'
    print(f'\n[处理中] 开始处理 {account_name}')
    
    cookies_data = account_info.get('cookies', {})
    api_user = account_info.get('api_user', '')
    
    if not api_user:
        print(f'[失败] {account_name}：未找到 API 用户标识符')
        return False
    
    # 解析cookies
    cookies_dict = parse_cookies(cookies_data)
    if not cookies_dict:
        print(f'[失败] {account_name}：无效的 cookies 配置')
        return False
    
    # 创建HTTP客户端
    client = httpx.Client(timeout=30.0)
    
    try:
        # 设置cookies
        client.cookies.update(cookies_dict)
        
        # 配置请求头
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Content-Type': 'application/json',
            'Referer': 'https://husanai.com/',
            'Origin': 'https://husanai.com',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'X-Requested-With': 'XMLHttpRequest',
            'husan-api-user': api_user,
        }
        
        print(f'[信息] {account_name}：开始签到请求 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        print(f'[网络] {account_name}：发送 POST 请求到 https://husanai.com/api/user/checkin')
        
        # 发送POST请求
        response = client.post('https://husanai.com/api/user/checkin', headers=headers)
        
        print(f'[响应] {account_name}：状态码 {response.status_code}')
        
        if response.status_code == 200:
            try:
                # 尝试解析JSON响应
                result = response.json()
                print(f'[响应] {account_name}：JSON 响应：{json.dumps(result, ensure_ascii=False, indent=2)}')
                
                # 检查签到是否成功
                if result.get('success') or result.get('code') == 0 or result.get('ret') == 1:
                    print(f'[成功] {account_name}：签到成功！')
                    return True
                else:
                    error_msg = result.get('msg', result.get('message', '未知错误'))
                    print(f'[失败] {account_name}：签到失败：{error_msg}')
                    return False
                    
            except json.JSONDecodeError:
                # 如果响应不是JSON格式
                print(f'[响应] {account_name}：文本响应：{response.text}')
                if 'success' in response.text.lower():
                    print(f'[成功] {account_name}：签到成功！')
                    return True
                else:
                    print(f'[失败] {account_name}：签到失败 - 无效的响应格式')
                    return False
        else:
            print(f'[失败] {account_name}：HTTP 请求失败，状态码 {response.status_code}')
            print(f'[响应] {account_name}：响应文本：{response.text}')
            return False
            
    except Exception as e:
        print(f'[错误] {account_name}：发生异常：{str(e)}')
        return False
    finally:
        client.close()


def main():
    """主函数"""
    print('HusanAI 多账号签到脚本')
    print('=' * 50)
    print(f'[时间] 执行时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    
    # 加载账号配置
    accounts = load_accounts()
    if not accounts:
        print('[失败] 无法加载账号配置，程序退出')
        exit(1)
    
    print(f'[信息] 找到 {len(accounts)} 个账号配置')
    
    # 为每个账号执行签到
    success_count = 0
    total_count = len(accounts)
    
    for i, account in enumerate(accounts):
        try:
            success = make_checkin_request_for_account(account, i)
            if success:
                success_count += 1
        except Exception as e:
            print(f'[失败] 账号 {i + 1} 处理异常：{e}')
    
    # 输出统计结果
    print(f'\n[统计] 签到结果统计：')
    print(f'[成功] 成功：{success_count}/{total_count}')
    print(f'[失败] 失败：{total_count - success_count}/{total_count}')
    
    if success_count == total_count:
        print('[成功] 所有账号签到成功！')
        exit(0)
    elif success_count > 0:
        print('[警告] 部分账号签到成功')
        exit(0)
    else:
        print('[错误] 所有账号签到失败')
        exit(1)


if __name__ == '__main__':
    main()