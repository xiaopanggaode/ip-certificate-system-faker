# -*- coding: utf-8 -*-
"""
工具函数模块
包含数据读取、筛选、文件匹配、压缩包生成等核心功能
"""

import pandas as pd
import os
import re
import zipfile
import shutil
from datetime import datetime
from pathlib import Path


# ============================================================================
# 配置常量
# ============================================================================

# CSV清单文件路径
CSV_FILE = "输入1：清单 - 源文件.csv"

# 证书文件夹路径
CERT_FOLDER = "输入2：证书 - 源文件"

# 临时文件目录（用于存放生成的压缩包）
TEMP_DIR = "temp"


# ============================================================================
# 数据读取相关函数
# ============================================================================

def load_companies():
    """
    读取CSV文件，提取所有唯一的公司名称（著作权人）
    
    Returns:
        list: 排序后的公司名称列表
    """
    try:
        # 读取CSV文件，使用UTF-8编码
        df = pd.read_csv(CSV_FILE, encoding='utf-8')
        
        # 提取"著作权人"列的所有唯一值
        companies = df['著作权人'].unique().tolist()
        
        # 按字母顺序排序
        companies.sort()
        
        return companies
    except Exception as e:
        print(f"读取公司列表失败: {e}")
        return []


def load_csv_data():
    """
    读取完整的CSV清单数据
    
    Returns:
        pandas.DataFrame: CSV数据框，如果读取失败返回None
    """
    try:
        df = pd.read_csv(CSV_FILE, encoding='utf-8')
        return df
    except Exception as e:
        print(f"读取CSV文件失败: {e}")
        return None


# ============================================================================
# 数据筛选相关函数
# ============================================================================

def filter_by_company(company_name):
    """
    根据公司名称筛选CSV数据（使用包含匹配）
    
    Args:
        company_name (str): 要筛选的公司名称（可以是部分匹配）
    
    Returns:
        pandas.DataFrame: 筛选后的数据框，如果筛选失败返回None
    """
    try:
        # 读取CSV数据
        df = load_csv_data()
        if df is None:
            return None
        
        # 使用包含匹配筛选"著作权人"列
        # na=False 表示忽略NaN值
        # regex=False 表示不使用正则表达式，将搜索字符串当作普通文本处理
        # 这样可以避免括号等特殊字符被当作正则表达式符号
        filtered_df = df[df['著作权人'].str.contains(company_name, na=False, regex=False)]
        
        return filtered_df
    except Exception as e:
        print(f"筛选数据失败: {e}")
        return None


def extract_registration_numbers(filtered_df):
    """
    从筛选后的数据框中提取登记号列表
    
    Args:
        filtered_df (pandas.DataFrame): 筛选后的数据框
    
    Returns:
        list: 登记号列表
    """
    if filtered_df is None or filtered_df.empty:
        return []
    
    # 提取"登记号"列的所有值，转换为列表
    registration_numbers = filtered_df['登记号'].tolist()
    
    return registration_numbers


# ============================================================================
# PDF文件匹配相关函数
# ============================================================================

def extract_registration_from_filename(filename):
    """
    从PDF文件名中提取登记号
    
    PDF文件名格式: "编号. 登记号【软著证书】.pdf"
    例如: "1. 2020SR0415238 【软著证书】.pdf" -> "2020SR0415238"
    
    Args:
        filename (str): PDF文件名
    
    Returns:
        str: 提取出的登记号，如果提取失败返回None
    """
    try:
        # 使用正则表达式匹配登记号格式：年份SR数字
        # 例如: 2020SR0415238
        pattern = r'(\d{4}SR\d+)'
        match = re.search(pattern, filename)
        
        if match:
            return match.group(1)
        return None
    except Exception as e:
        print(f"从文件名提取登记号失败: {e}")
        return None


def find_pdf_files_by_registration_numbers(registration_numbers):
    """
    根据登记号列表，在证书文件夹中查找对应的PDF文件
    
    Args:
        registration_numbers (list): 登记号列表
    
    Returns:
        dict: 字典，键为登记号，值为对应的PDF文件完整路径
              格式: {"2020SR0415238": "输入2：证书 - 源文件/1. 2020SR0415238 【软著证书】.pdf"}
    """
    pdf_files = {}
    
    # 检查证书文件夹是否存在
    if not os.path.exists(CERT_FOLDER):
        print(f"证书文件夹不存在: {CERT_FOLDER}")
        return pdf_files
    
    # 遍历证书文件夹中的所有文件
    for filename in os.listdir(CERT_FOLDER):
        # 只处理PDF文件
        if not filename.lower().endswith('.pdf'):
            continue
        
        # 从文件名中提取登记号
        registration_number = extract_registration_from_filename(filename)
        
        # 如果提取成功，且该登记号在目标列表中，则记录文件路径
        if registration_number and registration_number in registration_numbers:
            file_path = os.path.join(CERT_FOLDER, filename)
            pdf_files[registration_number] = file_path
    
    return pdf_files


# ============================================================================
# 压缩包生成相关函数
# ============================================================================

def ensure_temp_dir():
    """
    确保临时文件夹存在，如果不存在则创建
    
    Returns:
        str: 临时文件夹路径
    """
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
    return TEMP_DIR


def create_zip_package(filtered_df, pdf_files_dict, company_name):
    """
    生成包含筛选清单和证书文件的ZIP压缩包
    
    Args:
        filtered_df (pandas.DataFrame): 筛选后的清单数据
        pdf_files_dict (dict): PDF文件字典，键为登记号，值为文件路径
        company_name (str): 公司名称（用于命名文件）
    
    Returns:
        str: 生成的ZIP文件路径，如果生成失败返回None
    """
    try:
        # 确保临时文件夹存在
        ensure_temp_dir()
        
        # 生成ZIP文件名（包含公司名称和时间戳）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # 清理公司名称中的特殊字符，避免文件名问题
        safe_company_name = re.sub(r'[<>:"/\\|?*]', '_', company_name)
        zip_filename = f"{safe_company_name}_证书包_{timestamp}.zip"
        zip_path = os.path.join(TEMP_DIR, zip_filename)
        
        # 创建ZIP文件
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 1. 添加筛选清单CSV文件
            # 创建临时CSV文件
            temp_csv_path = os.path.join(TEMP_DIR, f"筛选清单_{timestamp}.csv")
            filtered_df.to_csv(temp_csv_path, index=False, encoding='utf-8-sig')
            # 将CSV文件添加到ZIP中（在ZIP内的文件名为"筛选清单.csv"）
            zipf.write(temp_csv_path, "筛选清单.csv")
            # 删除临时CSV文件
            os.remove(temp_csv_path)
            
            # 2. 添加匹配的PDF文件
            # 按照筛选清单中的登记号顺序添加文件
            registration_numbers = filtered_df['登记号'].tolist()
            for reg_num in registration_numbers:
                if reg_num in pdf_files_dict:
                    pdf_path = pdf_files_dict[reg_num]
                    # 获取原始文件名
                    pdf_filename = os.path.basename(pdf_path)
                    # 添加到ZIP中
                    zipf.write(pdf_path, pdf_filename)
        
        return zip_path
    
    except Exception as e:
        print(f"创建压缩包失败: {e}")
        return None


# ============================================================================
# 主处理函数
# ============================================================================

def process_company_request(company_name):
    """
    处理公司筛选请求的主函数
    
    流程：
    1. 根据公司名称筛选CSV数据
    2. 提取登记号列表
    3. 匹配对应的PDF文件
    4. 生成压缩包
    
    Args:
        company_name (str): 公司名称
    
    Returns:
        dict: 处理结果字典，包含：
            - success (bool): 是否成功
            - zip_path (str): ZIP文件路径（如果成功）
            - message (str): 消息提示
            - stats (dict): 统计信息（记录数、文件数等）
    """
    result = {
        'success': False,
        'zip_path': None,
        'message': '',
        'stats': {
            'total_records': 0,
            'matched_files': 0,
            'missing_files': 0
        }
    }
    
    try:
        # 步骤1: 筛选数据
        filtered_df = filter_by_company(company_name)
        if filtered_df is None or filtered_df.empty:
            result['message'] = f'未找到公司名称包含"{company_name}"的记录'
            return result
        
        # 记录筛选出的记录数
        result['stats']['total_records'] = len(filtered_df)
        
        # 步骤2: 提取登记号
        registration_numbers = extract_registration_numbers(filtered_df)
        if not registration_numbers:
            result['message'] = '未找到有效的登记号'
            return result
        
        # 步骤3: 匹配PDF文件
        pdf_files_dict = find_pdf_files_by_registration_numbers(registration_numbers)
        result['stats']['matched_files'] = len(pdf_files_dict)
        result['stats']['missing_files'] = len(registration_numbers) - len(pdf_files_dict)
        
        # 步骤4: 生成压缩包
        zip_path = create_zip_package(filtered_df, pdf_files_dict, company_name)
        if zip_path is None:
            result['message'] = '生成压缩包失败'
            return result
        
        # 成功
        result['success'] = True
        result['zip_path'] = zip_path
        result['message'] = f'成功生成压缩包！找到{result["stats"]["total_records"]}条记录，{result["stats"]["matched_files"]}个证书文件'
        
        return result
    
    except Exception as e:
        result['message'] = f'处理过程中发生错误: {str(e)}'
        return result

