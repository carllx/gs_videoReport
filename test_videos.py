#!/usr/bin/env python3
"""
YouTube Video Testing Script for gs_videoReport
用于测试YouTube视频分析功能的专用脚本
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime
import argparse

# Test video configurations
TEST_VIDEOS = {
    "public": {
        "url": "https://www.youtube.com/watch?v=7r7ZDugy3EE",
        "description": "公共测试视频",
        "expected_accessible": True,
        "local_filename": "public_test_video.mp4"
    },
    "private": {
        "url": "https://www.youtube.com/watch?v=EXmz9O1xQbM", 
        "description": "私有测试视频",
        "expected_accessible": False,
        "local_filename": "private_test_video.mp4"
    }
}

def log_message(message, level="INFO"):
    """记录日志消息"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {level}: {message}")

def check_video_accessibility(url):
    """检查YouTube视频是否可访问"""
    try:
        import requests
        response = requests.head(url, timeout=10)
        return response.status_code == 200
    except Exception as e:
        log_message(f"检查视频可访问性时出错: {e}", "WARNING")
        return False

def download_video_with_ytdlp(url, output_path):
    """使用yt-dlp下载YouTube视频"""
    try:
        cmd = [
            "yt-dlp",
            "--format", "best[ext=mp4]",
            "--output", str(output_path),
            url
        ]
        
        log_message(f"开始下载视频: {url}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            log_message(f"视频下载成功: {output_path}")
            return True
        else:
            log_message(f"视频下载失败: {result.stderr}", "ERROR")
            return False
            
    except FileNotFoundError:
        log_message("未找到yt-dlp，请先安装: pip install yt-dlp", "ERROR")
        return False
    except subprocess.TimeoutExpired:
        log_message("视频下载超时", "ERROR")
        return False
    except Exception as e:
        log_message(f"下载过程中出错: {e}", "ERROR")
        return False

def run_gs_videoreport_analysis(video_path, output_dir="./test_output"):
    """运行gs_videoReport分析"""
    try:
        cmd = [
            "python", "-m", "src.gs_video_report.cli", "main",
            str(video_path),
            "--template", "chinese_transcript",
            "--output", output_dir,
            "--config", "test_config.yaml",
            "--verbose"
        ]
        
        log_message(f"开始分析视频: {video_path}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=900)  # 15分钟超时
        
        log_message(f"分析完成，退出代码: {result.returncode}")
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        if result.stderr:
            print("STDERR:")  
            print(result.stderr)
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        log_message("视频分析超时", "ERROR")
        return False
    except Exception as e:
        log_message(f"分析过程中出错: {e}", "ERROR")
        return False

def test_video(video_type, download_first=False):
    """测试单个视频"""
    video_config = TEST_VIDEOS[video_type]
    log_message(f"开始测试{video_config['description']}: {video_config['url']}")
    
    # 1. 检查视频可访问性
    log_message("检查视频可访问性...")
    is_accessible = check_video_accessibility(video_config["url"])
    
    if is_accessible:
        log_message("✅ 视频可访问")
    else:
        log_message("❌ 视频不可访问或为私有视频")
        if video_type == "private":
            log_message("这是预期行为（私有视频应该不可访问）")
            return {"accessible": False, "expected": True, "analysis_success": False}
        else:
            log_message("公共视频不可访问，可能需要检查URL或网络")
            return {"accessible": False, "expected": False, "analysis_success": False}
    
    # 2. 如果需要，下载视频
    video_path = Path("./test_videos") / video_config["local_filename"]
    video_path.parent.mkdir(exist_ok=True)
    
    if download_first and not video_path.exists():
        success = download_video_with_ytdlp(video_config["url"], video_path)
        if not success:
            return {"accessible": is_accessible, "expected": True, "analysis_success": False, "download_failed": True}
    
    # 3. 分析视频（如果有本地文件）
    analysis_success = False
    if video_path.exists():
        log_message(f"使用本地视频文件进行分析: {video_path}")
        analysis_success = run_gs_videoreport_analysis(video_path)
    else:
        log_message("没有本地视频文件可供分析")
    
    return {
        "accessible": is_accessible,
        "expected": video_config["expected_accessible"],
        "analysis_success": analysis_success,
        "video_path": str(video_path) if video_path.exists() else None
    }

def main():
    """主测试函数"""
    parser = argparse.ArgumentParser(description="测试YouTube视频分析功能")
    parser.add_argument("--download", action="store_true", help="是否下载视频文件")
    parser.add_argument("--video-type", choices=["public", "private", "both"], default="both", 
                       help="要测试的视频类型")
    
    args = parser.parse_args()
    
    log_message("开始YouTube视频测试")
    log_message(f"测试类型: {args.video_type}")
    log_message(f"是否下载: {args.download}")
    
    # 检查依赖
    if args.download:
        try:
            subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            log_message("需要安装yt-dlp才能下载视频: pip install yt-dlp", "ERROR")
            sys.exit(1)
    
    # 检查配置文件
    if not Path("test_config.yaml").exists():
        log_message("未找到test_config.yaml配置文件", "ERROR")
        sys.exit(1)
    
    # 运行测试
    results = {}
    
    if args.video_type in ["public", "both"]:
        log_message("=" * 50)
        results["public"] = test_video("public", args.download)
    
    if args.video_type in ["private", "both"]:
        log_message("=" * 50)
        results["private"] = test_video("private", args.download)
    
    # 输出测试结果总结
    log_message("=" * 50)
    log_message("测试结果总结:")
    
    for video_type, result in results.items():
        video_desc = TEST_VIDEOS[video_type]["description"]
        log_message(f"\n{video_desc} ({video_type}):")
        log_message(f"  可访问性: {'✅' if result['accessible'] else '❌'} (预期: {'✅' if result['expected'] else '❌'})")
        
        if result.get('analysis_success'):
            log_message(f"  分析结果: ✅ 成功")
        elif result.get('download_failed'):
            log_message(f"  分析结果: ❌ 下载失败")
        else:
            log_message(f"  分析结果: ❌ 分析失败或未执行")
    
    log_message("测试完成!")

if __name__ == "__main__":
    main()
