# -*- coding: utf-8 -*-
"""
Flask Web应用主文件
提供IP证书获取系统的Web服务
"""

from flask import Flask, render_template, jsonify, send_file, request
import os
from utils import load_companies, process_company_request

# 创建Flask应用实例
app = Flask(__name__)

# 设置编码
app.config['JSON_AS_ASCII'] = False


# ============================================================================
# 路由定义
# ============================================================================

@app.route('/')
def index():
    """
    首页路由
    显示主页面，包含公司下拉选择框
    """
    return render_template('index.html')


@app.route('/api/companies', methods=['GET'])
def get_companies():
    """
    API接口：获取所有公司列表
    用于前端下拉框的数据源
    
    Returns:
        JSON响应，包含公司列表
        格式: {"companies": ["公司1", "公司2", ...]}
    """
    try:
        # 从工具函数获取公司列表
        companies = load_companies()
        
        return jsonify({
            'success': True,
            'companies': companies
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/download', methods=['POST'])
def download_certificates():
    """
    API接口：处理证书下载请求
    
    接收前端传来的公司名称，执行筛选和打包流程，返回下载链接
    
    Request Body (JSON):
        {
            "company_name": "公司名称"
        }
    
    Returns:
        JSON响应，包含处理结果和下载链接
        格式: {
            "success": true/false,
            "message": "提示信息",
            "download_url": "/download/file.zip" (如果成功),
            "stats": {
                "total_records": 10,
                "matched_files": 9,
                "missing_files": 1
            }
        }
    """
    try:
        # 获取请求数据
        data = request.get_json()
        
        # 检查是否提供了公司名称
        if not data or 'company_name' not in data:
            return jsonify({
                'success': False,
                'message': '请提供公司名称'
            }), 400
        
        company_name = data['company_name'].strip()
        
        # 检查公司名称是否为空
        if not company_name:
            return jsonify({
                'success': False,
                'message': '公司名称不能为空'
            }), 400
        
        # 调用工具函数处理请求
        result = process_company_request(company_name)
        
        # 如果处理成功，生成下载URL
        if result['success']:
            # 获取ZIP文件名（从完整路径中提取）
            zip_filename = os.path.basename(result['zip_path'])
            result['download_url'] = f'/download/{zip_filename}'
        
        # 返回结果（移除zip_path，只返回download_url）
        response = {
            'success': result['success'],
            'message': result['message'],
            'stats': result['stats']
        }
        
        if result['success']:
            response['download_url'] = result['download_url']
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@app.route('/download/<filename>')
def download_file(filename):
    """
    文件下载路由
    提供生成的ZIP文件下载
    
    Args:
        filename (str): 要下载的文件名
    
    Returns:
        文件下载响应
    """
    try:
        # 构建文件路径（确保在temp目录中）
        file_path = os.path.join('temp', filename)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'message': '文件不存在'
            }), 404
        
        # 返回文件供下载
        # as_attachment=True 表示作为附件下载，而不是在浏览器中打开
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/zip'
        )
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'下载文件失败: {str(e)}'
        }), 500


# ============================================================================
# 应用启动
# ============================================================================

if __name__ == '__main__':
    # 确保临时文件夹存在
    from utils import ensure_temp_dir
    ensure_temp_dir()
    
    # 本地开发环境运行（使用Flask开发服务器）
    # Render等云平台会自动使用gunicorn运行，不会执行这部分代码
    print("=" * 60)
    print("IP证书获取系统启动中...")
    print("=" * 60)
    print("访问地址: http://localhost:5000")
    print("按 Ctrl+C 停止服务器")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)

