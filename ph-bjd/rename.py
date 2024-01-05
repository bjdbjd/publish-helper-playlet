import json
import os

from pymediainfo import MediaInfo


def get_video_info(file_path):
    if not os.path.exists(file_path):
        print("文件路径不存在")
        return False, ["视频文件路径不存在"]
    try:
        media_info = MediaInfo.parse(file_path)
        print(media_info.to_json())
        width = ""
        format = ""
        hdr_format = ""
        commercial_name = ""
        channel_layout = ""

        for track in media_info.tracks:
            if track.track_type == "General":
                pass
                # ... 添加其他General信息
            elif track.track_type == "Video":
                if track.other_width:
                    width = track.other_width[0]
                if track.other_format:
                    format = track.other_format[0]
                if track.other_hdr_format:
                    hdr_format = track.other_hdr_format[0]
                # ... 添加其他Video信息
            elif track.track_type == "Audio":
                commercial_name = track.commercial_name
                channel_layout = track.channel_layout
                break
                # ... 添加其他Audio信息

        return True, [get_abbreviation(width), get_abbreviation(format), get_abbreviation(hdr_format),
                      get_abbreviation(commercial_name), get_abbreviation(channel_layout)]
    except OSError as e:
        # 文件路径相关的错误
        print(f"文件路径错误: {e}")
        return False, [f"文件路径错误: {e}"]
    except Exception as e:
        # MediaInfo无法解析文件
        print(f"无法解析文件: {e}")
        return False, [f"无法解析文件: {e}"]


def get_abbreviation(original_name, json_file_path="static/abbreviation.json"):
    """
    Gets the abbreviation for a given name from a specified JSON file.

    Parameters:
    original_name (str): The original name to find the abbreviation for.
    json_file_path (str): Path to the JSON file containing abbreviations.

    Returns:
    str: Abbreviation if found in the JSON file, else returns the original name.
    """
    print("开始对参数名称进行转化")
    try:
        with open(json_file_path, 'r') as file:
            abbreviation_map = json.load(file)

        # Return the abbreviation if found, else return the original name
        return abbreviation_map.get(original_name, original_name)
    except FileNotFoundError:
        print(f"File not found: {json_file_path}")
        return original_name
    except json.JSONDecodeError:
        print(f"Error decoding JSON from file: {json_file_path}")
        return original_name
